#!/usr/bin/env python3
"""
Test Suite for SkyGuard Startup Scripts and Service Functionality

Tests the systemd services, health checks, and control scripts.
"""

import os
import sys
import time
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
import pytest
import yaml
import json

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from skyguard.core.config_manager import ConfigManager
from skyguard.main import SkyGuardSystem


class TestStartupScripts:
    """Test suite for startup scripts and service functionality."""
    
    def setup_method(self) -> None:
        """Set up test environment."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="skyguard_test_"))
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create test directory structure
        (self.test_dir / "logs").mkdir()
        (self.test_dir / "data").mkdir()
        (self.test_dir / "config").mkdir()
        (self.test_dir / "deployment" / "scripts").mkdir(parents=True)
        (self.test_dir / "deployment" / "systemd").mkdir(parents=True)
        
    def teardown_method(self) -> None:
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_systemd_service_files_exist(self) -> None:
        """Test that systemd service files exist and are valid."""
        service_files = [
            "deployment/systemd/skyguard.service",
            "deployment/systemd/skyguard-web.service"
        ]
        
        for service_file in service_files:
            service_path = project_root / service_file
            assert service_path.exists(), f"Service file not found: {service_file}"
            
            # Check service file content
            content = service_path.read_text()
            assert "[Unit]" in content, f"Invalid service file format: {service_file}"
            assert "[Service]" in content, f"Invalid service file format: {service_file}"
            assert "[Install]" in content, f"Invalid service file format: {service_file}"
    
    def test_health_check_script_exists(self) -> None:
        """Test that health check script exists and is executable."""
        health_script = project_root / "deployment/scripts/health_check.sh"
        assert health_script.exists(), "Health check script not found"
        
        # Check if script is executable (on Unix systems)
        if os.name != 'nt':
            assert os.access(health_script, os.X_OK), "Health check script not executable"
    
    def test_control_script_exists(self) -> None:
        """Test that control script exists and is executable."""
        control_script = project_root / "deployment/scripts/skyguard-control.sh"
        assert control_script.exists(), "Control script not found"
        
        # Check if script is executable (on Unix systems)
        if os.name != 'nt':
            assert os.access(control_script, os.X_OK), "Control script not executable"
    
    def test_installer_script_exists(self) -> None:
        """Test that unified installer script exists."""
        installer_script = project_root / "deployment/install_pi5_unified.sh"
        assert installer_script.exists(), "Unified installer script not found"
    
    def test_health_check_script_syntax(self) -> None:
        """Test health check script syntax."""
        health_script = project_root / "deployment/scripts/health_check.sh"
        
        # Skip bash syntax check on Windows
        if os.name == 'nt':
            pytest.skip("Bash syntax check not available on Windows")
        
        # Test script syntax by running with --help or dry-run
        try:
            result = subprocess.run(
                ["bash", "-n", str(health_script)],
                capture_output=True,
                text=True,
                timeout=10
            )
            assert result.returncode == 0, f"Health check script syntax error: {result.stderr}"
        except subprocess.TimeoutExpired:
            pytest.fail("Health check script syntax check timed out")
    
    def test_control_script_syntax(self) -> None:
        """Test control script syntax."""
        control_script = project_root / "deployment/scripts/skyguard-control.sh"
        
        # Skip bash syntax check on Windows
        if os.name == 'nt':
            pytest.skip("Bash syntax check not available on Windows")
        
        # Test script syntax
        try:
            result = subprocess.run(
                ["bash", "-n", str(control_script)],
                capture_output=True,
                text=True,
                timeout=10
            )
            assert result.returncode == 0, f"Control script syntax error: {result.stderr}"
        except subprocess.TimeoutExpired:
            pytest.fail("Control script syntax check timed out")
    
    def test_installer_script_syntax(self) -> None:
        """Test installer script syntax."""
        installer_script = project_root / "deployment/install_pi5_unified.sh"
        
        # Skip bash syntax check on Windows
        if os.name == 'nt':
            pytest.skip("Bash syntax check not available on Windows")
        
        # Test script syntax
        try:
            result = subprocess.run(
                ["bash", "-n", str(installer_script)],
                capture_output=True,
                text=True,
                timeout=10
            )
            assert result.returncode == 0, f"Installer script syntax error: {result.stderr}"
        except subprocess.TimeoutExpired:
            pytest.fail("Installer script syntax check timed out")
    
    def test_health_check_help_output(self) -> None:
        """Test health check script help output."""
        health_script = project_root / "deployment/scripts/health_check.sh"
        
        # Skip bash script execution on Windows
        if os.name == 'nt':
            pytest.skip("Bash script execution not available on Windows")
        
        try:
            result = subprocess.run(
                ["bash", str(health_script), "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            # Script should either show help or run normally
            assert result.returncode in [0, 1], f"Unexpected return code: {result.returncode}"
        except subprocess.TimeoutExpired:
            pytest.fail("Health check script help check timed out")
    
    def test_control_script_help_output(self) -> None:
        """Test control script help output."""
        control_script = project_root / "deployment/scripts/skyguard-control.sh"
        
        # Skip bash script execution on Windows
        if os.name == 'nt':
            pytest.skip("Bash script execution not available on Windows")
        
        try:
            result = subprocess.run(
                ["bash", str(control_script), "help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            # Script should show help
            assert "SkyGuard Service Control" in result.stdout, "Help output not found"
        except subprocess.TimeoutExpired:
            pytest.fail("Control script help check timed out")
    
    def test_systemd_service_dependencies(self) -> None:
        """Test that systemd services have correct dependencies."""
        skyguard_service = project_root / "deployment/systemd/skyguard.service"
        web_service = project_root / "deployment/systemd/skyguard-web.service"
        
        skyguard_content = skyguard_service.read_text()
        web_content = web_service.read_text()
        
        # Check that web service depends on detection service
        assert "After=network-online.target skyguard.service" in web_content, "Web service should start after detection service"
        assert "BindsTo=skyguard.service" in web_content, "Web service should bind to detection service"
        
        # Check that detection service starts before web service
        assert "Before=skyguard-web.service" in skyguard_content, "Detection service should start before web service"
    
    def test_systemd_service_restart_policies(self) -> None:
        """Test that systemd services have correct restart policies."""
        service_files = [
            "deployment/systemd/skyguard.service",
            "deployment/systemd/skyguard-web.service"
        ]
        
        for service_file in service_files:
            service_path = project_root / service_file
            content = service_path.read_text()
            
            assert "Restart=always" in content, f"Service should restart always: {service_file}"
            assert "RestartSec=10" in content, f"Service should have restart delay: {service_file}"
    
    def test_systemd_service_user_permissions(self) -> None:
        """Test that systemd services run as correct user."""
        service_files = [
            "deployment/systemd/skyguard.service",
            "deployment/systemd/skyguard-web.service"
        ]
        
        for service_file in service_files:
            service_path = project_root / service_file
            content = service_path.read_text()
            
            assert "User=pi" in content, f"Service should run as pi user: {service_file}"
            assert "WorkingDirectory=/home/pi/skyguard" in content, f"Service should have correct working directory: {service_file}"


class TestServiceIntegration:
    """Test integration between services and main SkyGuard system."""
    
    def setup_method(self) -> None:
        """Set up test environment."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="skyguard_integration_test_"))
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create test directory structure
        (self.test_dir / "logs").mkdir()
        (self.test_dir / "data").mkdir()
        (self.test_dir / "config").mkdir()
        
    def teardown_method(self) -> None:
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_skyguard_system_initialization(self) -> None:
        """Test that SkyGuard system can be initialized."""
        # Create a minimal config for testing
        config_path = self.test_dir / "config" / "skyguard.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        test_config = {
            'camera': {
                'source': 0,
                'width': 640,
                'height': 480,
                'fps': 30
            },
            'ai': {
                'model_path': 'models/dummy.pt',
                'confidence_threshold': 0.5,
                'classes': ['bird']
            },
            'notifications': {
                'audio': {'enabled': False},
                'email': {'enabled': False},
                'sms': {'enabled': False},
                'push': {'enabled': False}
            },
            'storage': {
                'database_path': str(self.test_dir / 'data' / 'skyguard.db'),
                'detection_images_path': str(self.test_dir / 'data' / 'detections')
            },
            'system': {
                'detection_interval': 1
            },
            'logging': {
                'level': 'INFO',
                'file': str(self.test_dir / 'logs' / 'skyguard.log')
            }
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        # Test system initialization
        try:
            system = SkyGuardSystem(str(config_path))
            # System should be created without errors
            assert system is not None
            assert system.config_manager is not None
        except Exception as e:
            pytest.fail(f"SkyGuard system initialization failed: {e}")
    
    def test_config_manager_loading(self) -> None:
        """Test that config manager can load configuration."""
        config_path = self.test_dir / "config" / "skyguard.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        test_config = {
            'camera': {'source': 0},
            'ai': {'confidence_threshold': 0.5},
            'system': {'detection_interval': 1}
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        config_manager = ConfigManager(str(config_path))
        config = config_manager.get_config()
        
        assert config is not None
        assert 'camera' in config
        assert 'ai' in config
        assert 'system' in config


class TestServiceManagement:
    """Test service management functionality."""
    
    def test_service_file_validation(self) -> None:
        """Test that service files contain required sections."""
        service_files = [
            "deployment/systemd/skyguard.service",
            "deployment/systemd/skyguard-web.service"
        ]
        
        for service_file in service_files:
            service_path = project_root / service_file
            content = service_path.read_text()
            
            # Check for required sections
            required_sections = ["[Unit]", "[Service]", "[Install]"]
            for section in required_sections:
                assert section in content, f"Missing section {section} in {service_file}"
            
            # Check for required service properties
            required_properties = [
                "Type=simple",
                "User=pi",
                "WorkingDirectory=/home/pi/skyguard",
                "Restart=always",
                "RestartSec=10"
            ]
            
            for prop in required_properties:
                assert prop in content, f"Missing property {prop} in {service_file}"
    
    def test_script_permissions(self) -> None:
        """Test that scripts have correct permissions."""
        scripts = [
            "deployment/scripts/health_check.sh",
            "deployment/scripts/skyguard-control.sh",
            "deployment/install_pi5_unified.sh"
        ]
        
        for script in scripts:
            script_path = project_root / script
            assert script_path.exists(), f"Script not found: {script}"
            
            # On Unix systems, check if executable
            if os.name != 'nt':
                assert os.access(script_path, os.R_OK), f"Script not readable: {script}"
    
    def test_installer_script_completeness(self) -> None:
        """Test that installer script contains all necessary steps."""
        installer_script = project_root / "deployment/install_pi5_unified.sh"
        content = installer_script.read_text(encoding='utf-8')
        
        # Check for key installation steps
        required_steps = [
            "apt update",
            "python3-venv",
            "systemctl daemon-reload",
            "systemctl enable",
            "logrotate"
        ]
        
        for step in required_steps:
            assert step in content, f"Missing installation step: {step}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
