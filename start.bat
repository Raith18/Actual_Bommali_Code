@echo off
echo Starting 6 DOF Robotic Arm Control System...
echo =============================================

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing/updating dependencies...
pip install pyserial pyautogui pillow requests

REM Launch application
echo Launching application...
python launch.py

echo Application closed.
pause
