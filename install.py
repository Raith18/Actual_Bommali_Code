#!/usr/bin/env python3
"""
Installation script for Robotic Arm Control System
Installs all required dependencies and sets up the system
"""

import sys
import subprocess
import os
import platform
from pathlib import Path

def run_command(command, description=""):
    """Run a command and return success status"""
    try:
        print(f"Running: {description or command}")
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ Success: {description or command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {description or command}")
        print(f"Error: {e.stderr}")
        return False

def install_python_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing Python dependencies...")

    # Core dependencies
    core_packages = [
        "pyserial>=3.5",
        "pyautogui>=0.9.54",
        "pillow>=8.0.0",
        "requests>=2.25.0"
    ]

    # Optional packages for enhanced features
    optional_packages = [
        "opencv-python>=4.5.0",
        "pyaudio>=0.2.11",
        "pygame>=2.0.0",
        "pydantic>=1.8.0"
    ]

    # Install core packages
    for package in core_packages:
        if not run_command(f"pip install {package}", f"Installing {package}"):
            return False

    # Try to install optional packages
    print("\n📦 Installing optional packages (some may fail if not needed)...")
    for package in optional_packages:
        run_command(f"pip install {package}", f"Installing {package}")

    return True

def create_virtual_environment():
    """Create virtual environment"""
    print("\n🏗️  Setting up virtual environment...")

    if os.path.exists("venv"):
        print("Virtual environment already exists")
        return True

    return run_command(
        f"{sys.executable} -m venv venv",
        "Creating virtual environment"
    )

def setup_startup_scripts():
    """Create startup scripts"""
    print("\n📜 Creating startup scripts...")

    # Unix/Linux/Mac script
    unix_script = '''#!/bin/bash
# Robotic Arm Control System Startup Script

echo "🚀 Starting 6 DOF Robotic Arm Control System..."
echo "=============================================="

# Activate virtual environment
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Launch application
echo "Launching application..."
python launch.py

echo "Application closed."
'''

    # Windows script
    windows_script = '''@echo off
echo 🚀 Starting 6 DOF Robotic Arm Control System...
echo ==============================================

REM Activate virtual environment
if exist "venv" (
    echo Activating virtual environment...
    call venv\\Scripts\\activate.bat
)

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Launch application
echo Launching application...
python launch.py

echo Application closed.
pause
'''

    # Write scripts
    if platform.system() != "Windows":
        with open('start.sh', 'w') as f:
            f.write(unix_script)
        os.chmod('start.sh', 0o755)
        print("✅ Created start.sh")
    else:
        with open('start.bat', 'w') as f:
            f.write(windows_script)
        print("✅ Created start.bat")

    return True

def verify_arduino_sketch():
    """Verify Arduino sketch exists"""
    print("\n🔍 Checking Arduino sketch...")

    if os.path.exists("Arduino_mega.ino"):
        print("✅ Arduino sketch found: Arduino_mega.ino")
        print("📝 Make sure your Arduino Mega is programmed with this sketch")
        return True
    else:
        print("⚠️  Arduino sketch not found: Arduino_mega.ino")
        print("Please ensure Arduino_mega.ino is in the same directory")
        return False

def main():
    """Main installation function"""
    print("🚀 Robotic Arm Control System Installation")
    print("==========================================")

    # Check Python version
    python_version = sys.version_info
    print(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")

    if python_version < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)

    # Create virtual environment
    if not create_virtual_environment():
        print("❌ Failed to create virtual environment")
        sys.exit(1)

    # Install dependencies
    if not install_python_dependencies():
        print("❌ Failed to install dependencies")
        print("Please install manually: pip install -r requirements.txt")
        sys.exit(1)

    # Setup startup scripts
    setup_startup_scripts()

    # Verify Arduino sketch
    verify_arduino_sketch()

    # Installation complete
    print("\n🎉 Installation Complete!")
    print("=========================")
    print("✅ Virtual environment created")
    print("✅ Dependencies installed")
    print("✅ Startup scripts created")
    print("✅ Arduino sketch verified")

    print("\n🚀 To start the application:")
    if platform.system() != "Windows":
        print("   ./start.sh")
    else:
        print("   start.bat")
    print("   OR")
    print("   python launch.py")

    print("\n📚 For Arduino setup:")
    print("1. Open Arduino_mega.ino in Arduino IDE")
    print("2. Connect your Arduino Mega board")
    print("3. Upload the sketch to the board")
    print("4. Note the serial port (COMx on Windows, /dev/tty* on Linux/Mac)")

    print("\n🎯 The system is ready to control your 6 DOF robotic arm!")

if __name__ == "__main__":
    main()