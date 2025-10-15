# 6 DOF Robotic Arm Control System

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-STM32-green.svg)
![Status](https://img.shields.io/badge/status-active-brightgreen.svg)

## Overview

A professional, enterprise-grade control system for custom 6 Degrees of Freedom (DOF) robotic arms powered by STM32 microcontrollers. This system provides smooth real-time motion control, automated operation sequences, and comprehensive hardware diagnostics for research and industrial applications.

Built with a modern software architecture that separates hardware abstraction, business logic, and presentation layers, this project enables precise servo control, advanced motion planning, and intuitive user interaction.

---

## Features

### Professional Backend Architecture
- **Hardware Abstraction Layer (HAL)** – STM32-based modular I/O and servo control interface
- **Service Layer** – Encapsulated business logic with robust error handling and validation
- **Event-Driven Architecture** – Real-time communication between software and embedded controller
- **Health & Performance Monitoring** – Tracks latency, uptime, system stability, and diagnostics

### Smooth & Interactive GUI
- **60 FPS Animations** – Seamless visual updates providing real-time feedback
- **Dynamic UI** – Modern, responsive interface for intuitive control and monitoring
- **Real-Time Status Display** – Live servo angles, voltage readings, and system alerts
- **Customizable Themes** – Light/dark modes and research-grade visual configurations

### Robotic Arm Control
- **PWM Servo Control** – STM32 hardware timers for precise angular positioning
- **Waveshare Bus Servo Support** – UART-based communication for advanced servo joints
- **Smooth Motion Profiles** – Quintic interpolation algorithms for natural joint transitions
- **Automation Sequences** – Define, save, and execute complex multi-step operations

### Advanced Monitoring & Diagnostics
- **Health Diagnostics** – Real-time power supply, temperature, and signal integrity tracking
- **Error Logging** – Hardware-level exception capture and response analysis
- **Connection Monitoring** – Automatic USB/serial reconnection with fault tolerance
- **Performance Analytics** – Control loop latency logging and command throughput metrics

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Presentation Layer                    │
│            (GUI - Python/Qt or Tkinter)                │
├─────────────────────────────────────────────────────────┤
│                    Service Layer                        │
│         (Motion Planning, Sequence Control)            │
├─────────────────────────────────────────────────────────┤
│              Hardware Abstraction Layer                 │
│           (Serial Communication, HAL API)              │
├─────────────────────────────────────────────────────────┤
│                 STM32 Microcontroller                   │
│         (PWM Generation, UART, Servo Control)          │
├─────────────────────────────────────────────────────────┤
│                  Hardware Interface                     │
│        (Servos, Sensors, Power Management)             │
└─────────────────────────────────────────────────────────┘
```

**Key Components:**
- **STM32 Firmware** – Low-level servo control, PWM signal generation, communication protocols
- **Python Control Software** – High-level planning, GUI, automation, and monitoring
- **Serial Protocol** – Custom binary/text protocol for reliable host-to-controller communication

---

## Requirements

### Hardware
- STM32 Development Board (e.g., STM32F4, STM32F7, or compatible)
- 6x Standard PWM Servos or Waveshare Bus Servos
- 5-7V Power Supply (sufficient current for all servos)
- USB-to-Serial adapter or onboard ST-LINK

### Software
- **STM32CubeIDE** or **Keil MDK** for firmware development
- **Python 3.8+** with the following packages:
  - `pyserial` – Serial communication
  - `numpy` – Motion interpolation calculations
  - `PyQt5` or `tkinter` – GUI framework
  - `matplotlib` (optional) – Performance visualization

### Dependencies Installation

```bash
pip install pyserial numpy PyQt5 matplotlib
```

---

## Quick Start

### 1. Flash Firmware to STM32

1. Open the firmware project in STM32CubeIDE
2. Configure your specific board and peripherals in `.ioc` file
3. Build and flash to STM32 board via ST-LINK or UART bootloader

### 2. Connect Hardware

- Connect servos to designated PWM/UART pins (see pinout documentation)
- Connect STM32 to computer via USB or UART adapter
- Ensure adequate power supply for servos

### 3. Run Control Software

```bash
python main.py --port /dev/ttyUSB0 --baudrate 115200
```

*On Windows, replace `/dev/ttyUSB0` with appropriate COM port (e.g., `COM3`)*

### 4. Test Basic Operation

- Verify connection status in GUI
- Use manual control sliders to test individual joint movement
- Load and execute pre-defined automation sequences

---

## Usage

### Manual Control Mode

Control individual servo joints using sliders or numeric input:

```python
from arm_controller import ArmController

arm = ArmController(port='/dev/ttyUSB0')
arm.connect()
arm.set_joint_angle(joint_id=1, angle=90)  # Set joint 1 to 90 degrees
arm.move_smooth(target_angles=[0, 45, 90, 45, 0, 0], duration=2.0)
```

### Automation Sequences

Define and execute multi-step operations:

```python
sequence = [
    {'joints': [0, 0, 0, 0, 0, 0], 'duration': 1.0},
    {'joints': [90, 45, 30, 0, 45, 90], 'duration': 2.0},
    {'joints': [45, 90, 60, 30, 30, 45], 'duration': 1.5},
]

arm.execute_sequence(sequence, loop=False)
```

### Real-Time Monitoring

Access system diagnostics and health metrics:

```python
status = arm.get_system_status()
print(f"Connection: {status['connected']}")
print(f"Voltage: {status['voltage']}V")
print(f"Latency: {status['latency_ms']}ms")
print(f"Errors: {status['error_count']}")
```

---

## Project Structure

```
Actual_Bommali_Code/
├── firmware/
│   ├── Core/
│   │   ├── Src/
│   │   │   ├── main.c              # Main firmware entry
│   │   │   ├── servo_control.c     # PWM servo control
│   │   │   └── uart_handler.c      # Communication protocol
│   │   └── Inc/                    # Header files
│   └── STM32F4.ioc                 # Hardware configuration
├── software/
│   ├── arm_controller.py           # Main control class
│   ├── motion_planner.py           # Trajectory generation
│   ├── gui_main.py                 # GUI application
│   ├── health_monitor.py           # Diagnostics and logging
│   └── serial_protocol.py          # Communication layer
├── docs/
│   ├── API_Reference.md            # Software API documentation
│   ├── Protocol_Spec.md            # Serial communication protocol
│   └── Hardware_Setup.md           # Wiring and configuration guide
├── examples/
│   ├── basic_movement.py
│   ├── automation_demo.py
│   └── diagnostic_test.py
├── tests/
│   ├── test_motion.py
│   └── test_communication.py
├── README.md                       # This file
└── LICENSE                         # MIT License
```

---

## Configuration

### Servo Configuration

Edit `config.json` to define servo parameters:

```json
{
  "servos": [
    {"id": 1, "type": "pwm", "pin": "PA0", "min_angle": 0, "max_angle": 180},
    {"id": 2, "type": "pwm", "pin": "PA1", "min_angle": 0, "max_angle": 180},
    {"id": 3, "type": "waveshare", "uart": "UART2", "servo_id": 1}
  ],
  "communication": {
    "port": "/dev/ttyUSB0",
    "baudrate": 115200,
    "timeout": 1.0
  },
  "motion": {
    "default_speed": 1.0,
    "interpolation": "quintic"
  }
}
```

### GUI Customization

Themes and display options can be modified in `gui_settings.py`.

---

## Performance Metrics

- **Control Loop Frequency:** Up to 100 Hz
- **Servo Update Rate:** 50 Hz (PWM), 30 Hz (UART Bus Servos)
- **Communication Latency:** < 10ms (typical)
- **Motion Smoothness:** Quintic interpolation with configurable velocity/acceleration limits

---

## Development Notes

### Building the Firmware

1. Import project into STM32CubeIDE
2. Configure clock tree and peripherals via `.ioc` file
3. Compile with optimization level `-O2` for balanced performance
4. Flash using ST-LINK debugger

### Extending Functionality

- **Adding New Servo Types:** Implement interface in `servo_control.c`
- **Custom Motion Profiles:** Extend `motion_planner.py` with new interpolation algorithms
- **GUI Enhancements:** Modify `gui_main.py` using Qt Designer or programmatically

### Testing

Run unit tests:

```bash
python -m pytest tests/
```

Run hardware integration tests:

```bash
python tests/integration_test.py --port /dev/ttyUSB0
```

---

## Troubleshooting

**Issue:** Servos not responding
- Check power supply voltage and current capacity
- Verify servo connections and pinout configuration
- Ensure firmware flashed successfully to STM32

**Issue:** High latency or dropped commands
- Reduce communication baudrate if cable quality is poor
- Check for electromagnetic interference near servo cables
- Monitor USB connection stability

**Issue:** Jerky motion
- Increase interpolation duration for smoother transitions
- Verify servo update rate is consistent
- Check for CPU overload on STM32 (reduce control frequency if needed)

---

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-capability`)
3. Commit changes with clear messages
4. Submit a pull request with detailed description

---

## License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2025 Raith18

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORs OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Acknowledgments

- STMicroelectronics for the STM32 HAL library and development tools
- Waveshare for bus servo hardware and documentation
- Open-source robotics community for inspiration and best practices

---

## Contact & Support

For questions, issues, or collaboration opportunities:
- **GitHub Issues:** [Report a bug or request a feature](https://github.com/Raith18/Actual_Bommali_Code/issues)
- **Email:** Available upon request
- **Documentation:** See `/docs` folder for detailed technical references

---

**Last Updated:** October 2025
