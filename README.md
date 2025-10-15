# 🚀 6 DOF Robotic Arm Control System

A professional, enterprise-grade control system for custom 6 DOF robotic arms with smooth animations, automated control sequences, and comprehensive hardware monitoring.

## ✨ Features

### 🎛️ **Professional Backend Architecture**
- **Hardware Abstraction Layer** - Clean interface for all hardware components
- **Service Layer** - Business logic encapsulation with error handling
- **Event-Driven Architecture** - Real-time hardware-software communication
- **Performance Monitoring** - Health scores and response time tracking

### 🎨 **Butter-Smooth GUI**
- **60 FPS Animations** - Ultra-smooth visual transitions
- **Professional Styling** - Modern, responsive interface design
- **Real-time Feedback** - Live status updates and monitoring
- **Customizable Themes** - Multiple visual themes and color schemes

### 🤖 **Robotic Arm Control**
- **PWM Servo Control** - Digital pins 2-13 for servo positioning
- **Waveshare Bus Servo Support** - Serial communication protocol
- **Smooth Motion Profiles** - Eased movements and transitions
- **Automation Sequences** - Complex movement pattern builder

### 📊 **Advanced Monitoring**
- **System Health Tracking** - Real-time performance metrics
- **Error Logging** - Comprehensive error tracking and analysis
- **Connection Monitoring** - Automatic reconnection and recovery
- **Performance Analytics** - Response time and throughput monitoring

## 🛠️ **Hardware Requirements**
 
### STM32 Nucleo G474RE
- **PWM Servos**: Base and shoulder joints (Timer PWM outputs)
- **Waveshare Bus Servos**: Remaining joints (Joints 3-6) via UART
- **Serial Communication**: USB CDC ACM (115200 baud default)
- **High-Performance**: ARM Cortex-M4 @ 170MHz with FPU
- **Memory**: 128KB SRAM, 512KB Flash
- **Additional Peripherals**: Speakers, webcam, microphone (optional)

### Computer Requirements
- **Python**: 3.8 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **USB Ports**: Available for STM32 Nucleo connection
- **Display**: 1024x768 minimum resolution
- **STM32 Tools**: STM32CubeIDE or PlatformIO for firmware development

## 🎛️ **STM32 Nucleo G474RE Features**

### **High-Performance Capabilities**
- **ARM Cortex-M4** @ 170MHz with FPU and DSP instructions
- **512KB Flash** memory for complex applications
- **128KB SRAM** for data processing and buffering
- **Hardware Timer** support for precise PWM servo control
- **DMA** for efficient UART communication with bus servos

### **Advanced Servo Control**
- **7 PWM Channels** - 2 for PWM servos, 5 for extended control
- **High-Resolution PWM** - 16-bit timer resolution for smooth servo movement
- **Real-Time Operating** - Sub-millisecond response times
- **Trajectory Planning** - Advanced motion profiles with quintic easing
- **CPG Support** - Central Pattern Generator for natural movements

### **Communication Protocols**
- **USB CDC ACM** - Virtual COM port for PC communication
- **UART (1Mbps)** - High-speed communication with Waveshare bus servos
- **Command Protocol** - Efficient binary command structure
- **Real-Time Feedback** - 50Hz position feedback updates

### **Development Tools**
- **STM32CubeIDE** - Official STMicroelectronics IDE (Free)
- **PlatformIO** - Cross-platform development environment
- **HAL Libraries** - Hardware Abstraction Layer for easy development
- **ST-Link Debugger** - Built-in debugging and programming

## 🚀 **Quick Start**

### 1. **Installation**
```bash
# Clone or download the project files
# Run the installation script
python install.py
```

### 2. **STM32 Setup**
```bash
# 1. Open STM32CubeIDE or PlatformIO
# 2. Import the STM32 project files
# 3. Connect your STM32 Nucleo G474RE board
# 4. Build and upload the firmware
# 5. Note the serial port (COMx or /dev/ttyACM*)
```

### 3. **Launch Application**
```bash
# Method 1: Using launcher
python launch.py

# Method 2: Using startup script
./start.sh    # Linux/Mac
start.bat     # Windows

# Method 3: Direct launch
python gui.py
```

## 📁 **Project Structure**
 
```
robotic-arm-control/
├── 🚀 launch.py           # Main launcher (RECOMMENDED)
├── 📦 install.py          # Installation script
├── ⚙️ gui.py              # Main GUI application
├── 🔧 backend.py          # Professional backend system
├── 📋 requirements.txt    # Python dependencies
├── 🤖 stm32_nucleo/       # STM32 firmware directory
│   ├── 🔧 Core/          # STM32CubeIDE project files
│   ├── 📝 main.c         # Main application code
│   ├── 🎛️ servo.c        # Servo control implementation
│   ├── 📡 communication.c # Serial communication protocol
│   └── ⚙️ stm32g4xx_hal.c # Hardware abstraction layer
├── 📖 README.md           # This file
├── 📜 start.sh           # Linux/Mac startup script
└── 📜 start.bat          # Windows startup script
```

## 🎯 **Usage Guide**

### **Connection Tab**
1. **Select Serial Port** - Choose your STM32 Nucleo G474RE's COM port (usually /dev/ttyACM*)
2. **Set Baud Rate** - Use 115200 (default)
3. **Click Connect** - Establish hardware communication
4. **Test Connection** - Verify STM32 responsiveness

### **Digital I/O Tab**
- **Pins 2-13** - Control PWM servos and digital outputs
- **HIGH/LOW Buttons** - Set pin states
- **Read Buttons** - Monitor current pin states
- **Real-time Updates** - Live state synchronization

### **Analog I/O Tab**
- **Pins A0-A5** - Monitor analog sensor inputs
- **Read Buttons** - Get current analog values
- **Smoothed Values** - Filtered for stable readings

### **Automation Tab**
- **Sequence Builder** - Create complex movement patterns
- **Step Editor** - Add pins, actions, and delays
- **Loop Control** - Enable/disable sequence repetition
- **Save/Load** - Persistent sequence storage

### **Monitor Tab**
- **System Status** - Real-time health and performance
- **Connection Info** - Hardware connection details
- **Performance Metrics** - Response times and error rates

### **Settings Tab**
- **Animation Control** - Butter smooth mode settings
- **Performance Tuning** - Refresh intervals and timeouts
- **Visual Themes** - Interface appearance customization

## 🔧 **Configuration**
 
### **STM32 Pin Mapping**
```cpp
// PWM Servos (Base & Shoulder)
TIM2_CH1: PA0 - Base servo PWM
TIM2_CH2: PA1 - Shoulder servo PWM

// UART Communication (Bus Servos)
USART1_TX: PA9  - Serial data to bus servos
USART1_RX: PA10 - Serial data from bus servos

// Serial Communication (USB CDC)
USB_OTG_FS - Virtual COM port
Baud Rate: 115200
Protocol: Command-response based
```

### **Servo Control Protocol**
```bash
# Digital pin control for PWM servos
DIGITAL_WRITE:pin:state

# Analog reading for sensors
ANALOG_READ:pin

# Get system status
GET_STATUS
```

## 🎭 **Automation Examples**

### **Basic LED Blink**
```json
{
  "name": "LED Blink",
  "steps": [
    {"pin": "13", "action": "HIGH", "delay": 0.5},
    {"pin": "13", "action": "LOW", "delay": 0.5}
  ],
  "loop": true
}
```

### **Servo Movement Sequence**
```json
{
  "name": "Servo Wave",
  "steps": [
    {"pin": "9", "action": "HIGH", "delay": 1.0},
    {"pin": "10", "action": "HIGH", "delay": 1.0},
    {"pin": "11", "action": "HIGH", "delay": 1.0}
  ],
  "loop": false
}
```

## 🛠️ **Troubleshooting**

### **Connection Issues**
1. **Check USB Connection** - Ensure STM32 Nucleo is properly connected
2. **Verify Serial Port** - Use STM32CubeIDE or device manager to confirm port
3. **Check Baud Rate** - Ensure 115200 baud is set
4. **Restart Application** - Close and reopen if needed

### **Performance Issues**
1. **Enable Butter Smooth Mode** - For 60 FPS animations
2. **Adjust Refresh Interval** - In Settings tab
3. **Check System Resources** - Monitor CPU and memory usage
4. **Update Drivers** - Ensure STM32 drivers and ST-Link are current

### **Servo Control Problems**
1. **Verify Pin Configuration** - Check STM32 timer and GPIO setup
2. **Test Individual Pins** - Use Digital I/O tab
3. **Check Power Supply** - Ensure adequate servo power
4. **Monitor Temperature** - Prevent servo overheating

## 🔍 **System Architecture**

### **Backend Layers**
1. **Hardware Interface** - Direct Arduino communication
2. **Service Layer** - Business logic and state management
3. **Event System** - Real-time notification system
4. **Monitoring** - Health and performance tracking

### **GUI Components**
1. **Connection Management** - Serial port handling
2. **Hardware Control** - Pin state management
3. **Automation Engine** - Sequence execution
4. **Visual Feedback** - Real-time status display

## 📈 **Performance Metrics**

### **System Health Score**
- **100%** - Perfect operation
- **80-99%** - Good performance
- **60-79%** - Acceptable performance
- **<60%** - Performance issues detected

### **Response Times**
- **<100ms** - Excellent
- **100-200ms** - Good
- **200-500ms** - Acceptable
- **>500ms** - Performance issues

## 🔄 **Update Instructions**

### **Software Updates**
```bash
# Update dependencies
pip install -r requirements.txt --upgrade

# Check for new versions
python launch.py --check-updates
```

### **STM32 Firmware Updates**
1. **Open STM32CubeIDE** or PlatformIO
2. **Make necessary changes** to the source files
3. **Build and upload** firmware via ST-Link
4. **Restart application** to use new firmware

## 📝 **Development Notes**

### **Code Organization**
- **gui.py** - Main GUI application with smooth animations
- **backend.py** - Professional hardware abstraction layer
- **launch.py** - System launcher and initialization
- **stm32_nucleo/** - STM32 firmware directory
  - **main.c** - Main application and control logic
  - **servo.c** - Servo control implementation
  - **communication.c** - Serial communication protocol

### **Design Patterns**
- **MVC Architecture** - Model-View-Controller separation
- **Observer Pattern** - Event-driven communication
- **Factory Pattern** - Hardware interface creation
- **Singleton Pattern** - Backend manager instance

## 🆘 **Support**

### **Getting Help**
1. **Check Logs** - Review system_launch.log for errors
2. **Verify Connections** - Ensure hardware is properly connected
3. **Test Components** - Use individual tabs to isolate issues
4. **Check Documentation** - Review this README thoroughly

### **Common Issues**
- **Import Errors** - Run `python install.py` to fix dependencies
- **Connection Failures** - Check USB cable and STM32 drivers
- **Performance Issues** - Enable Butter Smooth mode in settings
- **Servo Problems** - Verify power supply and STM32 timer configurations

## 📄 **License**

This project is designed for educational and research purposes. Please ensure proper safety measures when controlling robotic hardware.

## 🎯 **Version History**

- **v1.0.0** - Initial release with professional backend
- **v1.1.0** - Added automation sequence builder
- **v1.2.0** - Enhanced smooth animations and themes
- **v1.3.0** - Added comprehensive monitoring and health checks

---

**🎉 Enjoy controlling your 6 DOF robotic arm with professional-grade software!**