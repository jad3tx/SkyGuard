#!/usr/bin/env python3
"""
SkyGuard Cleanup and Reinstallation Script

Performs a complete cleanup and fresh installation of SkyGuard.
This script stops services, removes the virtual environment, optionally
creates a backup, and runs a fresh installation.
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path
from typing import Optional, List
from datetime import datetime

# Colors for terminal output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color


def print_colored(message: str, color: str = NC) -> None:
    """Print a colored message."""
    print(f"{color}{message}{NC}")


def run_command(cmd: List[str], check: bool = True, shell: bool = False) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            cmd,
            check=check,
            shell=shell,
            capture_output=True,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print_colored(f"Error running command: {' '.join(cmd)}", RED)
        print_colored(f"Error: {e.stderr}", RED)
        raise


def check_user() -> None:
    """Check current user (informational only - no requirement)."""
    user = os.environ.get('USER', os.environ.get('USERNAME', ''))
    print_colored(f"Running as user: {user}", BLUE)
    print_colored("Note: Some operations may require sudo privileges", YELLOW)


def stop_services() -> None:
    """Stop any running SkyGuard services."""
    print_colored("🛑 Stopping SkyGuard services...", BLUE)
    
    # Try to stop using the stop script
    stop_script = Path(__file__).parent / "stop_skyguard.sh"
    if stop_script.exists():
        try:
            run_command(["bash", str(stop_script)], check=False)
        except Exception as e:
            print_colored(f"Warning: Could not stop services via script: {e}", YELLOW)
    
    # Also try to kill any running processes
    try:
        run_command(["pkill", "-f", "skyguard"], check=False)
        run_command(["pkill", "-f", "start_web_portal"], check=False)
    except Exception:
        pass  # Ignore if processes don't exist
    
    print_colored("✅ Services stopped", GREEN)


def create_backup(backup_dir: Path, project_root: Path) -> None:
    """Create a backup of the current installation."""
    print_colored(f"💾 Creating backup to {backup_dir}...", BLUE)
    
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"skyguard_backup_{timestamp}"
    
    # Backup important directories
    items_to_backup = ['config', 'data', 'logs', 'models']
    
    for item in items_to_backup:
        item_path = project_root / item
        if item_path.exists():
            dest_path = backup_path / item
            shutil.copytree(item_path, dest_path, dirs_exist_ok=True)
            print_colored(f"  ✓ Backed up {item}", GREEN)
    
    # Backup config file if it exists
    config_file = project_root / "config" / "skyguard.yaml"
    if config_file.exists():
        dest_config = backup_path / "skyguard.yaml"
        shutil.copy2(config_file, dest_config)
        print_colored("  ✓ Backed up skyguard.yaml", GREEN)
    
    print_colored(f"✅ Backup created at {backup_path}", GREEN)


def remove_venv(project_root: Path) -> None:
    """Remove the virtual environment."""
    venv_path = project_root / "venv"
    if venv_path.exists():
        print_colored("🗑️  Removing virtual environment...", BLUE)
        shutil.rmtree(venv_path)
        print_colored("✅ Virtual environment removed", GREEN)
    else:
        print_colored("ℹ️  No virtual environment found", YELLOW)


def clone_repository(repo_url: str, target_dir: Path, skip_git: bool) -> None:
    """Clone the repository if not skipping git."""
    if skip_git:
        print_colored("⏭️  Skipping git clone (using existing directory)", YELLOW)
        return
    
    if target_dir.exists() and any(target_dir.iterdir()):
        print_colored(f"⚠️  Directory {target_dir} already exists and is not empty", YELLOW)
        response = input("Remove existing directory and clone fresh? (y/N): ").strip().lower()
        if response == 'y':
            shutil.rmtree(target_dir)
        else:
            print_colored("Using existing directory", YELLOW)
            return
    
    print_colored(f"📥 Cloning repository from {repo_url}...", BLUE)
    run_command(["git", "clone", repo_url, str(target_dir)])
    print_colored("✅ Repository cloned", GREEN)


def run_installation(project_root: Path) -> None:
    """Run the installation script."""
    install_script = project_root / "scripts" / "install.sh"
    
    if not install_script.exists():
        print_colored(f"❌ Installation script not found: {install_script}", RED)
        sys.exit(1)
    
    print_colored("🔧 Running installation script...", BLUE)
    
    # Make script executable
    os.chmod(install_script, 0o755)
    
    # Run the installation script
    try:
        result = subprocess.run(
            ["bash", str(install_script)],
            cwd=project_root,
            check=True
        )
        print_colored("✅ Installation completed", GREEN)
    except subprocess.CalledProcessError as e:
        print_colored(f"❌ Installation failed with exit code {e.returncode}", RED)
        sys.exit(1)


def start_services(project_root: Path) -> None:
    """Start SkyGuard services."""
    start_script = project_root / "scripts" / "start_skyguard.sh"
    
    if not start_script.exists():
        print_colored("⚠️  Start script not found, skipping service start", YELLOW)
        return
    
    print_colored("🚀 Starting SkyGuard services...", BLUE)
    
    # Make script executable
    os.chmod(start_script, 0o755)
    
    try:
        subprocess.run(
            ["bash", str(start_script)],
            cwd=project_root,
            check=False  # Don't fail if services don't start
        )
        print_colored("✅ Services started", GREEN)
    except Exception as e:
        print_colored(f"⚠️  Could not start services: {e}", YELLOW)


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Cleanup and reinstall SkyGuard"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating a backup"
    )
    parser.add_argument(
        "--skip-git",
        action="store_true",
        help="Skip git clone (use existing directory)"
    )
    parser.add_argument(
        "--install-only",
        action="store_true",
        help="Skip cleanup, only run installation"
    )
    parser.add_argument(
        "--no-start",
        action="store_true",
        help="Don't start services after installation"
    )
    parser.add_argument(
        "--repo-url",
        default="https://github.com/jad3tx/SkyGuard.git",
        help="Repository URL to clone (default: https://github.com/jad3tx/SkyGuard.git)"
    )
    parser.add_argument(
        "--target-dir",
        default=Path.home() / "SkyGuard",
        type=Path,
        help="Target directory for installation (default: ~/SkyGuard)"
    )
    parser.add_argument(
        "--backup-dir",
        default=Path.home() / "skyguard_backups",
        type=Path,
        help="Directory for backups (default: ~/skyguard_backups)"
    )
    
    args = parser.parse_args()
    
    # Show banner
    print_colored("🧹 SkyGuard Cleanup and Fresh Installation", BLUE)
    print_colored("=" * 50, BLUE)
    print()
    
    # Check user
    check_user()
    
    # Get project root (where this script is located)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # If install-only, skip cleanup
    if not args.install_only:
        # Stop services
        stop_services()
        
        # Create backup if not skipping
        if not args.no_backup:
            create_backup(args.backup_dir, project_root)
        
        # Remove virtual environment
        remove_venv(project_root)
        
        # Clone repository if not skipping
        if not args.skip_git:
            clone_repository(args.repo_url, args.target_dir, args.skip_git)
            # Update project_root if we cloned to a different location
            if args.target_dir != project_root and args.target_dir.exists():
                project_root = args.target_dir
                os.chdir(project_root)
    
    # Run installation
    run_installation(project_root)
    
    # Start services if not disabled
    if not args.no_start:
        start_services(project_root)
    
    # Show final information
    print()
    print_colored("✅ SkyGuard cleanup and reinstallation completed!", GREEN)
    print()
    print_colored("📋 Next steps:", BLUE)
    print("1. Configure the system:")
    print("   cd SkyGuard")
    print("   source venv/bin/activate")
    print("   python -m skyguard.setup.configure")
    print()
    print("2. Access the web portal:")
    print("   Open http://<DEVICE_IP_ADDRESS>:8080 in your browser")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_colored("\n\n❌ Operation cancelled by user", RED)
        sys.exit(1)
    except Exception as e:
        print_colored(f"\n❌ Error: {e}", RED)
        sys.exit(1)

