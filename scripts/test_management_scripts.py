#!/usr/bin/env python3
"""
Test script for SkyGuard management scripts
Validates that the scripts are properly formatted and contain expected functionality
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any

def test_script_syntax(script_path: str) -> bool:
    """Test if a bash script has valid syntax."""
    try:
        result = subprocess.run(['bash', '-n', script_path], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        print("❌ bash not found - cannot test syntax")
        return False

def test_script_content(script_path: str, expected_functions: List[str]) -> Dict[str, bool]:
    """Test if a script contains expected functions."""
    if not os.path.exists(script_path):
        return {"exists": False}
    
    with open(script_path, 'r') as f:
        content = f.read()
    
    results = {"exists": True}
    for func in expected_functions:
        results[func] = func in content
    
    return results

def test_start_script() -> Dict[str, Any]:
    """Test the start_skyguard.sh script."""
    script_path = "scripts/start_skyguard.sh"
    print(f"🔍 Testing {script_path}...")
    
    # Test syntax
    syntax_ok = test_script_syntax(script_path)
    print(f"   Syntax: {'✅' if syntax_ok else '❌'}")
    
    # Test content
    expected_functions = [
        "start_main_system",
        "start_web_portal", 
        "check_user",
        "check_skyguard_dir",
        "check_venv",
        "usage()"
    ]
    
    content_results = test_script_content(script_path, expected_functions)
    print(f"   Content: {'✅' if all(content_results.values()) else '❌'}")
    
    for func, found in content_results.items():
        if func != "exists":
            print(f"     {func}: {'✅' if found else '❌'}")
    
    return {
        "syntax": syntax_ok,
        "content": content_results,
        "overall": syntax_ok and all(content_results.values())
    }

def test_stop_script() -> Dict[str, Any]:
    """Test the stop_skyguard.sh script."""
    script_path = "scripts/stop_skyguard.sh"
    print(f"🔍 Testing {script_path}...")
    
    # Test syntax
    syntax_ok = test_script_syntax(script_path)
    print(f"   Syntax: {'✅' if syntax_ok else '❌'}")
    
    # Test content
    expected_functions = [
        "stop_main_system",
        "stop_web_portal",
        "check_user",
        "usage()"
    ]
    
    content_results = test_script_content(script_path, expected_functions)
    print(f"   Content: {'✅' if all(content_results.values()) else '❌'}")
    
    for func, found in content_results.items():
        if func != "exists":
            print(f"     {func}: {'✅' if found else '❌'}")
    
    return {
        "syntax": syntax_ok,
        "content": content_results,
        "overall": syntax_ok and all(content_results.values())
    }

def test_cleanup_script() -> Dict[str, Any]:
    """Test the cleanup_and_reinstall.sh script."""
    script_path = "scripts/cleanup_and_reinstall.sh"
    print(f"🔍 Testing {script_path}...")
    
    # Test syntax
    syntax_ok = test_script_syntax(script_path)
    print(f"   Syntax: {'✅' if syntax_ok else '❌'}")
    
    # Test content
    expected_functions = [
        "stop_services",
        "remove_skyguard_dir",
        "clone_repository",
        "run_installation",
        "start_services",
        "check_user",
        "check_git",
        "usage()"
    ]
    
    content_results = test_script_content(script_path, expected_functions)
    print(f"   Content: {'✅' if all(content_results.values()) else '❌'}")
    
    for func, found in content_results.items():
        if func != "exists":
            print(f"     {func}: {'✅' if found else '❌'}")
    
    return {
        "syntax": syntax_ok,
        "content": content_results,
        "overall": syntax_ok and all(content_results.values())
    }

def test_script_permissions() -> Dict[str, bool]:
    """Test if scripts have executable permissions."""
    scripts = [
        "scripts/start_skyguard.sh",
        "scripts/stop_skyguard.sh", 
        "scripts/cleanup_and_reinstall.sh"
    ]
    
    results = {}
    for script in scripts:
        if os.path.exists(script):
            # Check if file is executable (has execute bit set)
            is_executable = os.access(script, os.X_OK)
            results[script] = is_executable
            print(f"   {script}: {'✅' if is_executable else '❌'} (executable)")
        else:
            results[script] = False
            print(f"   {script}: ❌ (not found)")
    
    return results

def main():
    """Run all tests."""
    print("🧪 Testing SkyGuard Management Scripts")
    print("=====================================")
    print("")
    
    # Test each script
    start_results = test_start_script()
    print("")
    
    stop_results = test_stop_script()
    print("")
    
    cleanup_results = test_cleanup_script()
    print("")
    
    # Test permissions
    print("🔐 Testing script permissions...")
    perm_results = test_script_permissions()
    print("")
    
    # Summary
    print("📊 Test Summary")
    print("===============")
    print(f"Start script: {'✅' if start_results['overall'] else '❌'}")
    print(f"Stop script: {'✅' if stop_results['overall'] else '❌'}")
    print(f"Cleanup script: {'✅' if cleanup_results['overall'] else '❌'}")
    print(f"Permissions: {'✅' if all(perm_results.values()) else '❌'}")
    
    overall_success = (
        start_results['overall'] and 
        stop_results['overall'] and 
        cleanup_results['overall'] and 
        all(perm_results.values())
    )
    
    print("")
    if overall_success:
        print("🎉 All tests passed! Scripts are ready to use.")
    else:
        print("❌ Some tests failed. Please check the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
