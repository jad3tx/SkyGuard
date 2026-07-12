#!/usr/bin/env python3
"""
Start SkyGuard Web Portal

This script starts the SkyGuard web portal for configuration and monitoring.
"""

import os
import sys
import argparse
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from a project-root .env file if present.
# This lets security settings (SKYGUARD_WEB_PASSWORD, SKYGUARD_SECRET_KEY,
# notification secrets, ...) be configured without exporting them in the
# shell — important because start_skyguard.sh launches this script via
# `runuser -l`, a fresh login shell that would not inherit exported vars.
try:
    from dotenv import load_dotenv
    load_dotenv(project_root / ".env")
except ImportError:
    # python-dotenv is an optional convenience; env vars still work if set.
    pass

from skyguard.web.app import SkyGuardWebPortal


def main():
    """Main function to start the web portal."""
    parser = argparse.ArgumentParser(description='SkyGuard Web Portal')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind to (default: 8080)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--config', default='config/skyguard.yaml', help='Configuration file path')
    parser.add_argument('--install-deps', action='store_true', help='Install web dependencies')
    
    args = parser.parse_args()
    
    # Install dependencies if requested
    if args.install_deps:
        print("📦 Installing web portal dependencies...")
        os.system("pip install -r requirements-web.txt")
        print("✅ Dependencies installed!")
        return
    
    # Check if dependencies are installed
    try:
        import flask
        import flask_cors
    except ImportError:
        print("❌ Web dependencies not installed!")
        print("Run: python scripts/start_web_portal.py --install-deps")
        return
    
    # Create web portal
    print("🌐 Starting SkyGuard Web Portal...")
    print(f"   Host: {args.host}")
    print(f"   Port: {args.port}")
    print(f"   Config: {args.config}")
    print(f"   Debug: {args.debug}")
    print("")
    print("🌐 Web Portal will be available at:")
    print(f"   http://{args.host}:{args.port}")
    print("")
    print("📱 Features:")
    print("   - Real-time system monitoring")
    print("   - Configuration management")
    print("   - Detection history and images")
    print("   - System statistics and logs")
    print("   - Camera and AI model testing")
    print("")
    
    try:
        portal = SkyGuardWebPortal(args.config)
        portal.run(host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        print("\n🛑 Web portal stopped by user")
    except Exception as e:
        print(f"❌ Failed to start web portal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
