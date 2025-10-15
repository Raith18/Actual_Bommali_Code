#!/usr/bin/env python3
"""
Complete Robotic Arm Control System Launcher
Single file to launch entire application with proper initialization
"""

import sys
import os
import subprocess
import tkinter as tk
from tkinter import messagebox
import threading
import time
import logging
from pathlib import Path

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

class SystemLauncher:
    """Main launcher for the complete robotic arm control system"""

    def __init__(self):
        self.backend_initialized = False
        self.gui_initialized = False
        self.system_ready = False

        # Setup logging
        self._setup_logging()

        # Check system requirements
        self._check_requirements()

    def _setup_logging(self):
        """Setup comprehensive logging system"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('system_launch.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger("SystemLauncher")

    def _check_requirements(self):
        """Check system requirements and dependencies"""
        self.logger.info("Checking system requirements...")

        # Check Python version
        python_version = sys.version_info
        if python_version < (3, 8):
            messagebox.showerror("Error", "Python 3.8 or higher is required")
            sys.exit(1)

        # Check for required modules
        required_modules = [
            'tkinter', 'serial', 'threading', 'queue',
            'math', 'json', 'os', 'time', 'dataclasses'
        ]

        missing_modules = []
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)

        if missing_modules:
            self.logger.error(f"Missing required modules: {missing_modules}")
            messagebox.showerror(
                "Missing Dependencies",
                f"Please install missing modules: {', '.join(missing_modules)}\n\n"
                "Run: pip install pyserial"
            )
            sys.exit(1)

        self.logger.info("All requirements satisfied")

    def initialize_backend(self):
        """Initialize the professional backend system"""
        try:
            self.logger.info("Initializing backend system...")

            # Import and initialize backend
            from backend import initialize_backend, get_backend

            # Initialize backend
            self.backend = initialize_backend()
            self.backend_initialized = True

            self.logger.info("Backend initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Backend initialization failed: {e}")
            messagebox.showerror(
                "Backend Error",
                f"Failed to initialize backend system:\n\n{str(e)}\n\n"
                "Please check your backend.py file and dependencies."
            )
            return False

    def initialize_gui(self):
        """Initialize the GUI system"""
        try:
            self.logger.info("Initializing GUI system...")

            # Import GUI
            from gui import ArduinoGUI

            # Create root window
            self.root = tk.Tk()

            # Initialize GUI
            self.app = ArduinoGUI(self.root)
            self.gui_initialized = True

            self.logger.info("GUI initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"GUI initialization failed: {e}")
            messagebox.showerror(
                "GUI Error",
                f"Failed to initialize GUI system:\n\n{str(e)}\n\n"
                "Please check your gui.py file and dependencies."
            )
            return False

    def check_arduino_connection(self):
        """Check Arduino connection and provide guidance"""
        try:
            from serial.tools import list_ports

            # Get available ports
            ports = [port.device for port in list_ports.comports()]

            if not ports:
                self.logger.warning("No serial ports found")
                messagebox.showwarning(
                    "No Arduino Found",
                    "No Arduino boards detected.\n\n"
                    "Please ensure your Arduino Mega is:\n"
                    "1. Connected to the computer via USB\n"
                    "2. Properly programmed with the provided sketch\n"
                    "3. Not being used by other applications\n\n"
                    "Then restart the application."
                )
                return False

            # Show available ports
            port_list = "\n".join(f"  • {port}" for port in ports)
            self.logger.info(f"Available ports: {ports}")

            messagebox.showinfo(
                "Arduino Detected",
                f"Found {len(ports)} serial port(s):\n\n{port_list}\n\n"
                "The application will automatically detect your Arduino Mega.\n"
                "Please select the correct port in the GUI when it launches."
            )

            return True

        except Exception as e:
            self.logger.error(f"Arduino detection failed: {e}")
            return False

    def create_startup_script(self):
        """Create startup script for easy launching"""
        try:
            startup_content = '''#!/bin/bash
# Robotic Arm Control System Startup Script

echo "Starting 6 DOF Robotic Arm Control System..."
echo "============================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
echo "Installing/updating dependencies..."
pip install pyserial pyautogui pillow requests

# Launch application
echo "Launching application..."
python launch.py

echo "Application closed."
'''

            # Windows version
            windows_startup = '''@echo off
echo Starting 6 DOF Robotic Arm Control System...
echo =============================================

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\\Scripts\\activate.bat

REM Install dependencies
echo Installing/updating dependencies...
pip install pyserial pyautogui pillow requests

REM Launch application
echo Launching application...
python launch.py

echo Application closed.
pause
'''

            # Write appropriate startup script
            if os.name == 'posix':
                with open('start.sh', 'w') as f:
                    f.write(startup_content)
                os.chmod('start.sh', 0o755)
                self.logger.info("Created start.sh script")
            else:
                with open('start.bat', 'w') as f:
                    f.write(windows_startup)
                self.logger.info("Created start.bat script")

        except Exception as e:
            self.logger.error(f"Failed to create startup script: {e}")

    def show_splash_screen(self):
        """Show splash screen during initialization"""
        splash = tk.Toplevel(self.root)
        splash.title("Loading...")
        splash.geometry("400x300")
        splash.resizable(False, False)
        splash.transient(self.root)
        splash.grab_set()

        # Center the splash screen over the main window
        splash.update_idletasks()
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()

        x = root_x + (root_width - 400) // 2
        y = root_y + (root_height - 300) // 2
        splash.geometry(f"400x300+{x}+{y}")

        # Splash content
        title_label = tk.Label(
            splash,
            text="*** Robotic Arm Control System",
            font=("Helvetica", 16, "bold")
        )
        title_label.pack(pady=20)

        status_label = tk.Label(
            splash,
            text="Initializing system...",
            font=("Helvetica", 10)
        )
        status_label.pack(pady=10)
        self.status_label = status_label

        # Progress bar
        from tkinter import ttk
        progress = ttk.Progressbar(splash, length=300, mode='indeterminate')
        progress.pack(pady=20)
        progress.start()

        # Update status
        def update_status(message):
            status_label.config(text=message)
            splash.update()

        # Simulate loading steps
        def loading_steps():
            steps = [
                "Initializing backend system...",
                "Loading hardware interfaces...",
                "Setting up GUI components...",
                "Checking Arduino connection...",
                "System ready!"
            ]

            for step in steps:
                update_status(step)
                time.sleep(0.5)

            splash.destroy()

        threading.Thread(target=loading_steps, daemon=True).start()

        return splash

    def launch(self):
        """Launch the complete system"""
        try:
            self.logger.info("Starting system launch sequence...")

            # Initialize GUI first (hidden)
            if not self.initialize_gui():
                return False

            # Hide the main window initially
            self.root.withdraw()

            # Show splash screen as Toplevel
            splash = self.show_splash_screen()

            # Initialize backend
            if not self.initialize_backend():
                splash.destroy()
                self.root.destroy()
                return False

            # Check Arduino connection
            self.check_arduino_connection()

            # Close splash screen
            splash.destroy()

            # Create startup scripts
            self.create_startup_script()

            # Show success message
            messagebox.showinfo(
                "System Ready",
                "[SUCCESS] Complete Robotic Arm Control System is ready!\n\n"
                "Features available:\n"
                "• Professional backend with hardware abstraction\n"
                "• Smooth 60 FPS animations\n"
                "• Event-driven architecture\n"
                "• Automation sequence builder\n"
                "• Real-time performance monitoring\n\n"
                "Click OK to start controlling your robotic arm!"
            )

            # Show main window and start GUI main loop
            self.root.deiconify()
            self.logger.info("Starting GUI main loop...")
            self.root.mainloop()
            self.system_ready = True

            return True

        except Exception as e:
            self.logger.error(f"Launch failed: {e}")
            messagebox.showerror(
                "Launch Error",
                f"Failed to launch system:\n\n{str(e)}\n\n"
                "Please check the logs in system_launch.log for details."
            )
            return False

    def cleanup(self):
        """Cleanup system resources"""
        self.logger.info("Cleaning up system...")

        try:
            # Cleanup GUI
            if self.gui_initialized and hasattr(self, 'root'):
                self.root.quit()
                self.root.destroy()

            # Cleanup backend
            if self.backend_initialized and hasattr(self, 'backend'):
                self.backend.cleanup()

            self.logger.info("Cleanup completed")

        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")


def main():
    """Main launch function"""
    print("*** Robotic Arm Control System Launcher ***")
    print("===========================================")

    # Create launcher
    launcher = SystemLauncher()

    try:
        # Launch system
        success = launcher.launch()

        if success:
            print("[SUCCESS] System launched successfully!")
        else:
            print("[ERROR] System launch failed!")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n[WARNING]  Interrupted by user")
        launcher.cleanup()
        sys.exit(0)

    except Exception as e:
        print(f"[ERROR] Fatal error: {e}")
        launcher.cleanup()
        sys.exit(1)

    finally:
        # Ensure cleanup
        launcher.cleanup()


if __name__ == "__main__":
    main()