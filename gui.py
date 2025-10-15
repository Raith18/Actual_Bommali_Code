"""
Enhanced Arduino Control System with Smooth Animations
Professional backend with butter-smooth motions and automated control systems
"""

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import serial
import serial.tools.list_ports
import threading
import time
import queue
import math
import random
import logging
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import os

# Import the professional backend system
try:
    from backend import (
        BackendManager, HardwareService, AutomationEngine,
        HardwareState, EventType, HardwareEvent, get_backend
    )
    BACKEND_AVAILABLE = True
except ImportError as e:
    # Fallback to local definitions if backend module not available
    print(f"Warning: Professional backend not available: {e}")
    print("Using simplified backend...")
    BackendManager = None
    BACKEND_AVAILABLE = False


class AnimationState(Enum):
    IDLE = "idle"
    SMOOTHING = "smoothing"
    AUTOMATED = "automated"
    MANUAL = "manual"


@dataclass
class MotionProfile:
    """Motion profile for smooth animations"""
    duration: float = 1.0
    easing: str = "ease_in_out"
    steps: int = 60
    current_step: int = 0
    start_value: float = 0.0
    end_value: float = 1.0
    current_value: float = 0.0


@dataclass
class AutomationSequence:
    """Automated control sequence"""
    name: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    duration: float = 5.0
    loop: bool = False
    enabled: bool = True


class MotionController:
    """Handles smooth motion animations"""

    def __init__(self):
        self.active_animations: Dict[str, MotionProfile] = {}
        self.animation_callbacks: Dict[str, callable] = {}

    def create_animation(self, name: str, start_val: float, end_val: float,
                        duration: float = 1.0, easing: str = "ease_in_out") -> MotionProfile:
        """Create a new motion profile"""
        profile = MotionProfile(
            duration=duration,
            easing=easing,
            start_value=start_val,
            end_value=end_val
        )
        self.active_animations[name] = profile
        return profile

    def update_animations(self) -> Dict[str, float]:
        """Update all active animations and return current values"""
        completed = []
        current_values = {}

        for name, profile in self.active_animations.items():
            if profile.current_step >= profile.steps:
                current_values[name] = profile.end_value
                completed.append(name)
                continue

            # Calculate progress
            progress = profile.current_step / profile.steps
            eased_progress = self._apply_easing(progress, profile.easing)

            # Calculate current value
            value_range = profile.end_value - profile.start_value
            profile.current_value = profile.start_value + (value_range * eased_progress)
            current_values[name] = profile.current_value

            # Update step
            step_time = profile.duration / profile.steps
            time.sleep(step_time)
            profile.current_step += 1

        # Remove completed animations
        for name in completed:
            del self.active_animations[name]

        return current_values

    def _apply_easing(self, t: float, easing_type: str) -> float:
        """Apply easing function to time value"""
        if easing_type == "linear":
            return t
        elif easing_type == "ease_in":
            return t * t
        elif easing_type == "ease_out":
            return 1 - (1 - t) ** 2
        elif easing_type == "ease_in_out":
            return 3 * t * t - 2 * t * t * t
        elif easing_type == "bounce":
            if t < 1/2.75:
                return 7.5625 * t * t
            elif t < 2/2.75:
                t -= 1.5/2.75
                return 7.5625 * t * t + 0.75
            elif t < 2.5/2.75:
                t -= 2.25/2.75
                return 7.5625 * t * t + 0.9375
            else:
                t -= 2.625/2.75
                return 7.5625 * t * t + 0.984375
        return t


class ArduinoBackend:
    """Enhanced backend class with smooth operations and automation"""

    def __init__(self):
        self.serial_port: Optional[serial.Serial] = None
        self.is_connected = False
        self.message_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.pin_states: Dict[int, int] = {}
        self.analog_values: Dict[str, int] = {}
        self.connection_history: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, float] = {}

    def connect(self, port: str, baudrate: int = 9600) -> bool:
        """Connect to Arduino with enhanced error handling"""
        try:
            self.serial_port = serial.Serial(port, baudrate, timeout=1)
            time.sleep(2)  # Wait for Arduino to initialize

            # Test connection
            if self._test_connection():
                self.is_connected = True
                self._record_connection_event("connected", port, baudrate)
                return True
            else:
                self.serial_port.close()
                return False
        except serial.SerialException as e:
            self._record_connection_event("failed", port, baudrate, str(e))
            return False

    def _test_connection(self) -> bool:
        """Test Arduino connection"""
        try:
            self.serial_port.write("GET_STATUS\n".encode())
            response = self.serial_port.readline().decode().strip()
            return response.startswith("STATUS:")
        except:
            return False

    def disconnect(self):
        """Enhanced disconnect with cleanup"""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.is_connected = False
        self._record_connection_event("disconnected")

    def send_command(self, command: str) -> str:
        """Enhanced command sending with performance tracking"""
        if not self.is_connected or not self.serial_port:
            return "Not connected"

        start_time = time.time()
        try:
            self.serial_port.write(f"{command}\n".encode())
            response = self.serial_port.readline().decode().strip()

            # Track performance
            response_time = time.time() - start_time
            self.performance_metrics[command] = response_time

            return response
        except Exception as e:
            response_time = time.time() - start_time
            self.performance_metrics[f"{command}_error"] = response_time
            return f"Error: {e}"

    def digital_write(self, pin: int, state: int) -> str:
        """Set digital pin state with state tracking"""
        response = self.send_command(f"DIGITAL_WRITE:{pin}:{state}")
        if response == "OK":
            self.pin_states[pin] = state
        return response

    def digital_read(self, pin: int) -> str:
        """Read digital pin state with caching"""
        response = self.send_command(f"DIGITAL_READ:{pin}")
        if response in ["0", "1"]:
            self.pin_states[pin] = int(response)
        return response

    def analog_read(self, pin: str) -> str:
        """Read analog pin value with smoothing"""
        pin_map = {'A0': 0, 'A1': 1, 'A2': 2, 'A3': 3, 'A4': 4, 'A5': 5}
        arduino_pin = pin_map.get(pin, pin)
        response = self.send_command(f"ANALOG_READ:{arduino_pin}")

        if response.isdigit():
            # Apply smoothing filter
            current_value = int(response)
            if pin in self.analog_values:
                # Exponential smoothing
                smoothed = 0.3 * current_value + 0.7 * self.analog_values[pin]
                self.analog_values[pin] = int(smoothed)
                return str(self.analog_values[pin])
            else:
                self.analog_values[pin] = current_value
                return response
        return response

    def set_pin_mode(self, pin: int, mode: str) -> str:
        """Set pin mode"""
        return self.send_command(f"PIN_MODE:{pin}:{mode}")

    def get_status(self) -> str:
        """Get Arduino status with enhanced parsing"""
        response = self.send_command("GET_STATUS")
        if response.startswith("STATUS:"):
            # Parse status string
            states = response[7:].split(',')
            for i, state in enumerate(states):
                pin_num = i + 2  # Pins start from 2
                self.pin_states[pin_num] = int(state)
        return response

    def _record_connection_event(self, event: str, port: str = "", baudrate: int = 0, error: str = ""):
        """Record connection events for debugging"""
        self.connection_history.append({
            "event": event,
            "timestamp": time.time(),
            "port": port,
            "baudrate": baudrate,
            "error": error
        })

    def get_performance_stats(self) -> Dict[str, float]:
        """Get performance statistics"""
        return self.performance_metrics.copy()

    def clear_performance_stats(self):
        """Clear performance metrics"""
        self.performance_metrics.clear()


class ArduinoGUI:
    """Enhanced GUI class with professional backend integration"""

    def __init__(self, root):
        self.root = root

        # Setup logging first
        self.logger = logging.getLogger("ArduinoGUI")

        # Initialize backend system
        if BACKEND_AVAILABLE and BackendManager:
            try:
                self.backend_manager = get_backend()
                self.backend = self.backend_manager.hardware_service
                self.logger.info("Using professional backend")
            except Exception as e:
                print(f"Professional backend error: {e}")
                print("Falling back to simple backend...")
                self.backend_manager = None
                self.backend = ArduinoBackend()
        else:
            # Use simple backend
            self.backend_manager = None
            self.backend = ArduinoBackend()
            print("Using simple backend")

        self.motion_controller = MotionController()
        self.animation_state = AnimationState.IDLE

        # Animation and automation settings
        self.animation_speed = 1.0
        self.auto_refresh_interval = 100  # milliseconds
        self.smooth_transitions = True
        self.butter_smooth = True

        # Event handling
        self.event_listeners_registered = False

        # Message queue for communication
        self.message_queue = queue.Queue()

        # Automation sequences storage
        self.automation_sequences = {}

        # Active sequence tracking
        self.active_sequence = None
        self.sequence_thread = None

        # Color themes for smooth visual feedback
        self.themes = {
            "connected": {"bg": "#e8f5e8", "fg": "#2e7d32"},
            "disconnected": {"bg": "#ffebee", "fg": "#c62828"},
            "active": {"bg": "#e3f2fd", "fg": "#1565c0"},
            "smooth": {"bg": "#fff3e0", "fg": "#ef6c00"}
        }

        self.root.title("6 DOF Robotic Arm Control System")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f5f5f5")

        # Create main interface with smooth styling
        self._create_main_interface()

        # Start background threads
        self.running = True
        self.animation_thread = threading.Thread(target=self._animation_loop, daemon=True)
        self.comm_thread = threading.Thread(target=self._communication_loop, daemon=True)
        self.animation_thread.start()
        self.comm_thread.start()

        # Register event listeners if using professional backend
        if self.backend_manager:
            self._register_event_listeners()

        # Initialize automation sequences
        self._initialize_automation_sequences()

        # Update available ports
        self._update_ports()

    def _register_event_listeners(self):
        """Register event listeners for professional backend"""
        if not self.backend_manager:
            return

        # Hardware state change listener
        def on_hardware_event(event: HardwareEvent):
            if event.event_type == EventType.CONNECTION_ESTABLISHED:
                self.root.after_idle(self._on_hardware_connected)
            elif event.event_type == EventType.CONNECTION_LOST:
                self.root.after_idle(self._on_hardware_disconnected)
            elif event.event_type == EventType.PIN_STATE_CHANGED:
                self.root.after_idle(self._on_pin_state_changed, event.data)
            elif event.event_type == EventType.ANALOG_VALUE_CHANGED:
                self.root.after_idle(self._on_analog_value_changed, event.data)
            elif event.event_type == EventType.SYSTEM_STATUS:
                self.root.after_idle(self._on_system_status, event.data)

        # Subscribe to all relevant events
        for event_type in [EventType.CONNECTION_ESTABLISHED, EventType.CONNECTION_LOST,
                          EventType.PIN_STATE_CHANGED, EventType.ANALOG_VALUE_CHANGED,
                          EventType.SYSTEM_STATUS]:
            self.backend_manager.events.subscribe(event_type, on_hardware_event)

        self.event_listeners_registered = True

    def _on_hardware_connected(self):
        """Handle hardware connection event"""
        self.connect_btn.config(state=tk.DISABLED)
        self.disconnect_btn.config(state=tk.NORMAL)
        self.status_var.set("✅ Connected")
        messagebox.showinfo("Success", "Connected to Arduino successfully")

    def _on_hardware_disconnected(self):
        """Handle hardware disconnection event"""
        self.connect_btn.config(state=tk.NORMAL)
        self.disconnect_btn.config(state=tk.DISABLED)
        self.status_var.set("❌ Disconnected")

    def _on_pin_state_changed(self, data: Dict[str, Any]):
        """Handle pin state change event"""
        pin = data.get("pin")
        state = data.get("state")
        if pin is not None and state is not None:
            state_text = "HIGH" if state == 1 else "LOW"
            if pin in self.digital_vars:
                self.digital_vars[pin].set(state_text)

    def _on_analog_value_changed(self, data: Dict[str, Any]):
        """Handle analog value change event"""
        pin = data.get("pin")
        value = data.get("value")
        if pin and value is not None:
            if pin in self.analog_vars:
                self.analog_vars[pin].set(str(value))

    def _on_system_status(self, data: Dict[str, Any]):
        """Handle system status update"""
        health_score = data.get("health_score", 0)
        response_time = data.get("response_time", 0)

        # Update performance indicator
        self.perf_var.set(f"⚡ Health: {health_score:.1f}% | RT: {response_time:.3f}s")

    def _create_main_interface(self):
        """Create the main enhanced interface"""
        # Main container with smooth styling
        self.main_container = tk.Frame(self.root, bg="#f5f5f5")
        self.main_container.pack(fill='both', expand=True)

        # Create animated title bar
        self._create_title_bar()

        # Create main notebook with enhanced styling
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Create enhanced tabs
        self.create_connection_tab()
        self.create_robotic_arm_tab()
        self.create_servo_control_tab()
        self.create_digital_io_tab()
        self.create_analog_io_tab()
        self.create_automation_tab()
        self.create_monitor_tab()
        self.create_settings_tab()

        # Enhanced status bar with animations
        self._create_enhanced_status_bar()

        # Apply custom styles
        self._apply_custom_styles()

    def _create_title_bar(self):
        """Create animated title bar"""
        title_frame = tk.Frame(self.main_container, bg="#2196F3", height=60)
        title_frame.pack(fill='x', padx=10, pady=5)
        title_frame.pack_propagate(False)

        # Animated title
        self.title_label = tk.Label(
            title_frame,
            text="🚀 Enhanced Arduino Control System",
            font=("Helvetica", 16, "bold"),
            fg="white",
            bg="#2196F3"
        )
        self.title_label.pack(side=tk.LEFT, padx=20, pady=10)

        # Animated status indicator
        self.status_canvas = tk.Canvas(
            title_frame,
            width=20,
            height=20,
            bg="#2196F3",
            highlightthickness=0
        )
        self.status_canvas.pack(side=tk.RIGHT, padx=20, pady=15)
        self.status_circle = self.status_canvas.create_oval(5, 5, 15, 15, fill="#ff4444")

    def _create_enhanced_status_bar(self):
        """Create enhanced status bar with animations"""
        self.status_frame = tk.Frame(self.main_container, bg="#e0e0e0", height=30)
        self.status_frame.pack(fill='x', padx=10, pady=5)
        self.status_frame.pack_propagate(False)

        # Connection status
        self.status_var = tk.StringVar(value="🔴 Disconnected")
        self.status_label = tk.Label(
            self.status_frame,
            textvariable=self.status_var,
            font=("Helvetica", 9),
            bg="#e0e0e0",
            fg="#333"
        )
        self.status_label.pack(side=tk.LEFT, padx=10)

        # Performance indicator
        self.perf_var = tk.StringVar(value="⚡ Ready")
        self.perf_label = tk.Label(
            self.status_frame,
            textvariable=self.perf_var,
            font=("Helvetica", 9),
            bg="#e0e0e0",
            fg="#666"
        )
        self.perf_label.pack(side=tk.RIGHT, padx=10)

        # Animation indicator
        self.anim_var = tk.StringVar(value="✨ Smooth Mode")
        self.anim_label = tk.Label(
            self.status_frame,
            textvariable=self.anim_var,
            font=("Helvetica", 9),
            bg="#e0e0e0",
            fg="#2196F3"
        )
        self.anim_label.pack(side=tk.RIGHT, padx=20)

    def _apply_custom_styles(self):
        """Apply custom styles for smooth appearance"""
        style = ttk.Style()

        # Custom notebook style
        style.configure('Custom.Notebook', background='#f5f5f5')
        style.configure('Custom.Notebook.Tab',
                       background='#e0e0e0',
                       foreground='#333',
                       padding=[10, 5],
                       font=("Helvetica", 10))

        # Enhanced button styles
        style.configure('Smooth.TButton',
                       background='#4CAF50',
                       foreground='white',
                       font=("Helvetica", 9, "bold"),
                       padding=8)

        style.map('Smooth.TButton',
                 background=[('active', '#45a049')])

        # Progress bar style
        style.configure('Smooth.Horizontal.TProgressbar',
                       background='#2196F3',
                       troughcolor='#e0e0e0',
                       borderwidth=0,
                       lightcolor='#2196F3',
                       darkcolor='#2196F3')

    def _animation_loop(self):
        """Main animation loop for smooth motions"""
        while self.running:
            try:
                if self.butter_smooth:
                    # Update animations
                    current_values = self.motion_controller.update_animations()

                    # Update GUI elements with smooth transitions
                    if current_values:
                        self.root.after_idle(self._update_animated_elements, current_values)

                    # Animate status indicator
                    self._animate_status_indicator()

                time.sleep(0.016)  # ~60 FPS for smooth animation
            except Exception as e:
                print(f"Animation error: {e}")
                time.sleep(0.1)

    def _animate_status_indicator(self):
        """Animate the status indicator circle"""
        if self.backend.is_connected:
            # Pulsing green animation when connected
            import math
            intensity = int(128 + 127 * math.sin(time.time() * 3))
            color = f"#{intensity:02x}ff{intensity:02x}"
            self.status_canvas.itemconfig(self.status_circle, fill=color)
        else:
            # Red when disconnected
            self.status_canvas.itemconfig(self.status_circle, fill="#ff4444")

    def _update_animated_elements(self, values: Dict[str, float]):
        """Update GUI elements with smooth animation values"""
        for element_name, value in values.items():
            if element_name.startswith("progress_"):
                # Update progress bars
                progress_bar = getattr(self, f"{element_name}_bar", None)
                if progress_bar:
                    progress_bar['value'] = value

    def create_connection_tab(self):
        """Create connection configuration tab"""
        conn_frame = ttk.Frame(self.notebook)
        self.notebook.add(conn_frame, text='Connection')

        # Port selection
        ttk.Label(conn_frame, text="Serial Port:").grid(row=0, column=0, padx=5, pady=5)
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(conn_frame, textvariable=self.port_var, width=30)
        self.port_combo.grid(row=0, column=1, padx=5, pady=5)

        # Refresh button
        ttk.Button(conn_frame, text="Refresh Ports",
                  command=self._update_ports).grid(row=0, column=2, padx=5, pady=5)

        # Baud rate
        ttk.Label(conn_frame, text="Baud Rate:").grid(row=1, column=0, padx=5, pady=5)
        self.baud_var = tk.StringVar(value="9600")
        baud_combo = ttk.Combobox(conn_frame, textvariable=self.baud_var,
                                 values=["9600", "115200", "38400", "19200"], width=10)
        baud_combo.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        # Connection buttons
        button_frame = ttk.Frame(conn_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=20)

        self.connect_btn = ttk.Button(button_frame, text="Connect",
                                     command=self._connect)
        self.connect_btn.pack(side=tk.LEFT, padx=5)

        self.disconnect_btn = ttk.Button(button_frame, text="Disconnect",
                                        command=self._disconnect, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=5)

        # Test connection
        ttk.Button(button_frame, text="Test Connection",
                  command=self._test_connection).pack(side=tk.LEFT, padx=5)

    def create_robotic_arm_tab(self):
        """Create robotic arm control tab"""
        arm_frame = ttk.Frame(self.notebook)
        self.notebook.add(arm_frame, text='🤖 Robotic Arm')

        # Robotic arm control panel
        control_panel = ttk.LabelFrame(arm_frame, text="6 DOF Arm Control")
        control_panel.pack(fill=tk.X, padx=5, pady=5)

        # Joint control sliders
        joint_frame = ttk.Frame(control_panel)
        joint_frame.pack(fill=tk.X, padx=5, pady=5)

        # Base rotation
        ttk.Label(joint_frame, text="Base:").grid(row=0, column=0, padx=5, pady=2)
        self.base_var = tk.IntVar(value=90)
        base_scale = ttk.Scale(joint_frame, from_=0, to=180, variable=self.base_var,
                              orient=tk.HORIZONTAL, command=self._update_base)
        base_scale.grid(row=0, column=1, padx=5, pady=2, sticky=tk.EW)

        # Shoulder
        ttk.Label(joint_frame, text="Shoulder:").grid(row=1, column=0, padx=5, pady=2)
        self.shoulder_var = tk.IntVar(value=90)
        shoulder_scale = ttk.Scale(joint_frame, from_=0, to=180, variable=self.shoulder_var,
                                  orient=tk.HORIZONTAL, command=self._update_shoulder)
        shoulder_scale.grid(row=1, column=1, padx=5, pady=2, sticky=tk.EW)

        # Elbow
        ttk.Label(joint_frame, text="Elbow:").grid(row=2, column=0, padx=5, pady=2)
        self.elbow_var = tk.IntVar(value=90)
        elbow_scale = ttk.Scale(joint_frame, from_=0, to=180, variable=self.elbow_var,
                               orient=tk.HORIZONTAL, command=self._update_elbow)
        elbow_scale.grid(row=2, column=1, padx=5, pady=2, sticky=tk.EW)

        # Wrist pitch
        ttk.Label(joint_frame, text="Wrist Pitch:").grid(row=3, column=0, padx=5, pady=2)
        self.wrist_pitch_var = tk.IntVar(value=90)
        wrist_pitch_scale = ttk.Scale(joint_frame, from_=0, to=180, variable=self.wrist_pitch_var,
                                     orient=tk.HORIZONTAL, command=self._update_wrist_pitch)
        wrist_pitch_scale.grid(row=3, column=1, padx=5, pady=2, sticky=tk.EW)

        # Wrist roll
        ttk.Label(joint_frame, text="Wrist Roll:").grid(row=4, column=0, padx=5, pady=2)
        self.wrist_roll_var = tk.IntVar(value=90)
        wrist_roll_scale = ttk.Scale(joint_frame, from_=0, to=180, variable=self.wrist_roll_var,
                                    orient=tk.HORIZONTAL, command=self._update_wrist_roll)
        wrist_roll_scale.grid(row=4, column=1, padx=5, pady=2, sticky=tk.EW)

        # Gripper
        ttk.Label(joint_frame, text="Gripper:").grid(row=5, column=0, padx=5, pady=2)
        self.gripper_var = tk.IntVar(value=90)
        gripper_scale = ttk.Scale(joint_frame, from_=0, to=180, variable=self.gripper_var,
                                 orient=tk.HORIZONTAL, command=self._update_gripper)
        gripper_scale.grid(row=5, column=1, padx=5, pady=2, sticky=tk.EW)

        # Control buttons
        btn_frame = ttk.Frame(control_panel)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(btn_frame, text="🏠 Home Position",
                  command=self._go_home, style='Smooth.TButton').pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text="📏 Zero Position",
                  command=self._go_zero, style='Smooth.TButton').pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text="🎯 Pick Position",
                  command=self._go_pick, style='Smooth.TButton').pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text="📦 Place Position",
                  command=self._go_place, style='Smooth.TButton').pack(side=tk.LEFT, padx=5)

        # Preset positions
        preset_frame = ttk.LabelFrame(arm_frame, text="Preset Positions")
        preset_frame.pack(fill=tk.X, padx=5, pady=5)

        preset_btn_frame = ttk.Frame(preset_frame)
        preset_btn_frame.pack(fill=tk.X, padx=5, pady=5)

        presets = [
            ("Position 1", self._preset_1),
            ("Position 2", self._preset_2),
            ("Position 3", self._preset_3),
            ("Position 4", self._preset_4)
        ]

        for name, command in presets:
            ttk.Button(preset_btn_frame, text=name, command=command,
                      style='Smooth.TButton').pack(side=tk.LEFT, padx=5)

    def create_servo_control_tab(self):
        """Create servo control tab"""
        servo_frame = ttk.Frame(self.notebook)
        self.notebook.add(servo_frame, text='🎛️ Servo Control')

        # Servo control panel
        control_panel = ttk.LabelFrame(servo_frame, text="Individual Servo Control")
        control_panel.pack(fill=tk.X, padx=5, pady=5)

        # Servo selection
        servo_select_frame = ttk.Frame(control_panel)
        servo_select_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(servo_select_frame, text="Servo:").grid(row=0, column=0, padx=5, pady=2)
        self.servo_var = tk.StringVar()
        servo_combo = ttk.Combobox(servo_select_frame, textvariable=self.servo_var,
                                  values=["Base", "Shoulder", "Elbow", "Wrist Pitch", "Wrist Roll", "Gripper"],
                                  width=15)
        servo_combo.grid(row=0, column=1, padx=5, pady=2)
        servo_combo.set("Base")

        # Angle control
        ttk.Label(servo_select_frame, text="Angle:").grid(row=0, column=2, padx=5, pady=2)
        self.servo_angle_var = tk.IntVar(value=90)
        angle_scale = ttk.Scale(servo_select_frame, from_=0, to=180, variable=self.servo_angle_var,
                               orient=tk.HORIZONTAL, command=self._update_servo_angle)
        angle_scale.grid(row=0, column=3, padx=5, pady=2, sticky=tk.EW)

        # Speed control
        ttk.Label(servo_select_frame, text="Speed:").grid(row=1, column=0, padx=5, pady=2)
        self.servo_speed_var = tk.IntVar(value=50)
        speed_scale = ttk.Scale(servo_select_frame, from_=1, to=100, variable=self.servo_speed_var,
                               orient=tk.HORIZONTAL, command=self._update_servo_speed)
        speed_scale.grid(row=1, column=1, padx=5, pady=2, sticky=tk.EW)

        # Servo buttons
        servo_btn_frame = ttk.Frame(control_panel)
        servo_btn_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(servo_btn_frame, text="Move",
                  command=self._move_servo, style='Smooth.TButton').pack(side=tk.LEFT, padx=5)

        ttk.Button(servo_btn_frame, text="Center",
                  command=self._center_servo, style='Smooth.TButton').pack(side=tk.LEFT, padx=5)

        ttk.Button(servo_btn_frame, text="Test Range",
                  command=self._test_servo_range, style='Smooth.TButton').pack(side=tk.LEFT, padx=5)

        # Bus servo control (for advanced servos)
        bus_servo_frame = ttk.LabelFrame(servo_frame, text="Bus Servo Control")
        bus_servo_frame.pack(fill=tk.X, padx=5, pady=5)

        bus_btn_frame = ttk.Frame(bus_servo_frame)
        bus_btn_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(bus_btn_frame, text="🔍 Scan Bus",
                  command=self._scan_bus_servos, style='Smooth.TButton').pack(side=tk.LEFT, padx=5)

        ttk.Button(bus_btn_frame, text="⚙️ Configure",
                  command=self._configure_bus_servos, style='Smooth.TButton').pack(side=tk.LEFT, padx=5)

        ttk.Button(bus_btn_frame, text="🔄 Sync Move",
                  command=self._sync_move_servos, style='Smooth.TButton').pack(side=tk.LEFT, padx=5)

    def create_digital_io_tab(self):
        """Create digital I/O control tab"""
        dio_frame = ttk.Frame(self.notebook)
        self.notebook.add(dio_frame, text='Digital I/O')

        # Digital pins 2-13
        self.digital_vars = {}
        self.digital_labels = {}

        for i in range(2, 14):
            # Pin label
            ttk.Label(dio_frame, text=f"Pin {i}:").grid(row=i-2, column=0, padx=5, pady=2)

            # State variable and label
            self.digital_vars[i] = tk.StringVar(value="LOW")
            self.digital_labels[i] = ttk.Label(dio_frame, textvariable=self.digital_vars[i],
                                              width=8)
            self.digital_labels[i].grid(row=i-2, column=1, padx=5, pady=2)

            # HIGH/LOW buttons
            btn_frame = ttk.Frame(dio_frame)
            btn_frame.grid(row=i-2, column=2, padx=5, pady=2)

            ttk.Button(btn_frame, text="HIGH",
                      command=lambda p=i: self._set_digital_high(p),
                      width=6).pack(side=tk.LEFT)
            ttk.Button(btn_frame, text="LOW",
                      command=lambda p=i: self._set_digital_low(p),
                      width=6).pack(side=tk.LEFT, padx=(2,0))

            # Read button
            ttk.Button(btn_frame, text="Read",
                      command=lambda p=i: self._read_digital(p),
                      width=6).pack(side=tk.LEFT, padx=(5,0))

    def create_analog_io_tab(self):
        """Create analog I/O control tab"""
        aio_frame = ttk.Frame(self.notebook)
        self.notebook.add(aio_frame, text='Analog I/O')

        # Analog pins A0-A5
        self.analog_vars = {}
        self.analog_labels = {}

        for i, pin_name in enumerate(['A0', 'A1', 'A2', 'A3', 'A4', 'A5']):
            ttk.Label(aio_frame, text=f"{pin_name}:").grid(row=i, column=0, padx=5, pady=5)

            self.analog_vars[pin_name] = tk.StringVar(value="0")
            self.analog_labels[pin_name] = ttk.Label(aio_frame,
                                                    textvariable=self.analog_vars[pin_name],
                                                    width=10)
            self.analog_labels[pin_name].grid(row=i, column=1, padx=5, pady=5)

            ttk.Button(aio_frame, text="Read",
                      command=lambda p=pin_name: self._read_analog(p),
                      width=8).grid(row=i, column=2, padx=5, pady=5)

    def create_monitor_tab(self):
        """Create monitoring tab"""
        monitor_frame = ttk.Frame(self.notebook)
        self.notebook.add(monitor_frame, text='Monitor')

        # Status display
        status_frame = ttk.LabelFrame(monitor_frame, text="Arduino Status")
        status_frame.pack(fill=tk.X, padx=5, pady=5)

        self.status_text = tk.Text(status_frame, height=10, width=80)
        scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL,
                                 command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=scrollbar.set)

        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Control buttons
        btn_frame = ttk.Frame(monitor_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(btn_frame, text="Get Status",
                  command=self._get_arduino_status).pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text="Clear Monitor",
                  command=self._clear_monitor).pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text="Auto Refresh",
                  command=self._toggle_auto_refresh).pack(side=tk.LEFT, padx=5)

        self.auto_refresh = False

    def create_automation_tab(self):
        """Create automation control tab with smooth workflows"""
        auto_frame = ttk.Frame(self.notebook)
        self.notebook.add(auto_frame, text='🎭 Automation')

        # Automation control panel
        control_panel = ttk.LabelFrame(auto_frame, text="Automation Control")
        control_panel.pack(fill=tk.X, padx=5, pady=5)

        # Sequence selection
        ttk.Label(control_panel, text="Sequence:").grid(row=0, column=0, padx=5, pady=5)
        self.sequence_var = tk.StringVar()
        self.sequence_combo = ttk.Combobox(control_panel, textvariable=self.sequence_var, width=30)
        self.sequence_combo.grid(row=0, column=1, padx=5, pady=5)

        # Control buttons
        btn_frame = ttk.Frame(control_panel)
        btn_frame.grid(row=0, column=2, padx=5, pady=5)

        self.start_seq_btn = ttk.Button(btn_frame, text="▶️ Start",
                                       command=self._start_sequence, style='Smooth.TButton')
        self.start_seq_btn.pack(side=tk.LEFT, padx=2)

        self.stop_seq_btn = ttk.Button(btn_frame, text="⏹️ Stop",
                                      command=self._stop_sequence, state=tk.DISABLED)
        self.stop_seq_btn.pack(side=tk.LEFT, padx=2)

        # Sequence builder
        builder_frame = ttk.LabelFrame(auto_frame, text="Sequence Builder")
        builder_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Step list
        self.step_tree = ttk.Treeview(builder_frame, columns=("pin", "action", "value", "delay"),
                                     show="headings", height=8)
        self.step_tree.heading("pin", text="Pin")
        self.step_tree.heading("action", text="Action")
        self.step_tree.heading("value", text="Value")
        self.step_tree.heading("delay", text="Delay (s)")
        self.step_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbar for tree
        scrollbar = ttk.Scrollbar(builder_frame, orient=tk.VERTICAL, command=self.step_tree.yview)
        self.step_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Step controls
        step_frame = ttk.Frame(builder_frame)
        step_frame.pack(fill=tk.X, padx=5, pady=5)

        # Add step controls
        ttk.Label(step_frame, text="Pin:").grid(row=0, column=0, padx=2)
        self.step_pin_var = tk.StringVar()
        step_pin_combo = ttk.Combobox(step_frame, textvariable=self.step_pin_var,
                                     values=[str(i) for i in range(2, 14)] + ['A0', 'A1', 'A2', 'A3', 'A4', 'A5'],
                                     width=8)
        step_pin_combo.grid(row=0, column=1, padx=2)

        ttk.Label(step_frame, text="Action:").grid(row=0, column=2, padx=2)
        self.step_action_var = tk.StringVar()
        step_action_combo = ttk.Combobox(step_frame, textvariable=self.step_action_var,
                                        values=["HIGH", "LOW", "READ", "WAIT"],
                                        width=8)
        step_action_combo.grid(row=0, column=3, padx=2)

        ttk.Label(step_frame, text="Value:").grid(row=0, column=4, padx=2)
        self.step_value_var = tk.StringVar()
        step_value_entry = ttk.Entry(step_frame, textvariable=self.step_value_var, width=10)
        step_value_entry.grid(row=0, column=5, padx=2)

        # Step buttons
        self.add_step_btn = ttk.Button(step_frame, text="➕ Add Step",
                                      command=self._add_step, style='Smooth.TButton')
        self.add_step_btn.grid(row=0, column=6, padx=5)

        self.remove_step_btn = ttk.Button(step_frame, text="➖ Remove",
                                         command=self._remove_step)
        self.remove_step_btn.grid(row=0, column=7, padx=2)

        # Sequence settings
        settings_frame = ttk.LabelFrame(auto_frame, text="Sequence Settings")
        settings_frame.pack(fill=tk.X, padx=5, pady=5)

        # Duration and loop settings
        ttk.Label(settings_frame, text="Duration (s):").grid(row=0, column=0, padx=5)
        self.duration_var = tk.StringVar(value="5.0")
        duration_spin = ttk.Spinbox(settings_frame, from_=1.0, to=300.0, increment=0.5,
                                   textvariable=self.duration_var, width=8)
        duration_spin.grid(row=0, column=1, padx=5)

        self.loop_var = tk.BooleanVar()
        loop_check = ttk.Checkbutton(settings_frame, text="Loop", variable=self.loop_var)
        loop_check.grid(row=0, column=2, padx=10)

        # Save/Load buttons
        save_btn = ttk.Button(settings_frame, text="💾 Save Sequence",
                             command=self._save_sequence, style='Smooth.TButton')
        save_btn.grid(row=0, column=3, padx=5)

        load_btn = ttk.Button(settings_frame, text="📁 Load Sequence",
                             command=self._load_sequence)
        load_btn.grid(row=0, column=4, padx=5)

        # Animation preview
        preview_frame = ttk.LabelFrame(auto_frame, text="Animation Preview")
        preview_frame.pack(fill=tk.X, padx=5, pady=5)

        self.preview_canvas = tk.Canvas(preview_frame, height=100, bg="white")
        self.preview_canvas.pack(fill=tk.X, padx=5, pady=5)

        # Animation controls
        anim_frame = ttk.Frame(preview_frame)
        anim_frame.pack(fill=tk.X, padx=5, pady=5)

        self.preview_btn = ttk.Button(anim_frame, text="🎬 Preview",
                                     command=self._preview_animation, style='Smooth.TButton')
        self.preview_btn.pack(side=tk.LEFT, padx=5)

        self.easing_var = tk.StringVar(value="ease_in_out")
        easing_combo = ttk.Combobox(anim_frame, textvariable=self.easing_var,
                                   values=["linear", "ease_in", "ease_out", "ease_in_out", "bounce"],
                                   width=12)
        easing_combo.pack(side=tk.RIGHT, padx=5)

    def _initialize_automation_sequences(self):
        """Initialize default automation sequences"""
        # LED blink sequence
        blink_seq = AutomationSequence("LED Blink", duration=3.0, loop=True)
        blink_seq.steps = [
            {"pin": "13", "action": "HIGH", "delay": 0.5},
            {"pin": "13", "action": "LOW", "delay": 0.5}
        ]
        self.automation_sequences["blink"] = blink_seq

        # Fade sequence
        fade_seq = AutomationSequence("Smooth Fade", duration=4.0, loop=True)
        fade_seq.steps = [
            {"pin": "11", "action": "HIGH", "delay": 2.0},
            {"pin": "11", "action": "LOW", "delay": 2.0}
        ]
        self.automation_sequences["fade"] = fade_seq

        # Update sequence combo
        self._update_sequence_combo()

    def _update_sequence_combo(self):
        """Update sequence selection combo box"""
        sequences = list(self.automation_sequences.keys())
        self.sequence_combo['values'] = sequences
        if sequences:
            self.sequence_var.set(sequences[0])

    def _add_step(self):
        """Add step to current sequence"""
        pin = self.step_pin_var.get()
        action = self.step_action_var.get()
        value = self.step_value_var.get()

        if not pin or not action:
            messagebox.showerror("Error", "Please select pin and action")
            return

        # Calculate delay
        delay = 1.0
        if action == "WAIT":
            try:
                delay = float(value) if value else 1.0
                value = ""
            except:
                delay = 1.0

        # Add to tree
        self.step_tree.insert("", tk.END, values=(pin, action, value, f"{delay:.1f}s"))

        # Clear inputs
        self.step_pin_var.set("")
        self.step_action_var.set("")
        self.step_value_var.set("")

    def _remove_step(self):
        """Remove selected step"""
        selection = self.step_tree.selection()
        if selection:
            self.step_tree.delete(selection[0])

    def _start_sequence(self):
        """Start automation sequence"""
        sequence_name = self.sequence_var.get()
        if not sequence_name or sequence_name not in self.automation_sequences:
            messagebox.showerror("Error", "Please select a valid sequence")
            return

        sequence = self.automation_sequences[sequence_name]
        if not sequence.enabled:
            messagebox.showerror("Error", "Sequence is disabled")
            return

        self.active_sequence = sequence_name
        self.animation_state = AnimationState.AUTOMATED

        # Update UI
        self.start_seq_btn.config(state=tk.DISABLED)
        self.stop_seq_btn.config(state=tk.NORMAL)

        # Start sequence thread
        self.sequence_thread = threading.Thread(target=self._run_sequence, args=(sequence,), daemon=True)
        self.sequence_thread.start()

    def _stop_sequence(self):
        """Stop automation sequence"""
        self.active_sequence = None
        self.animation_state = AnimationState.IDLE

        # Update UI
        self.start_seq_btn.config(state=tk.NORMAL)
        self.stop_seq_btn.config(state=tk.DISABLED)

    def _run_sequence(self, sequence: AutomationSequence):
        """Run automation sequence with smooth timing"""
        while self.active_sequence and sequence.enabled:
            for step in sequence.steps:
                if not self.active_sequence:
                    break

                # Execute step
                self._execute_step(step)

                # Wait with smooth timing
                delay = step.get("delay", 1.0)
                time.sleep(delay)

            if not sequence.loop:
                break

        # Sequence completed
        self.root.after_idle(self._sequence_completed)

    def _execute_step(self, step: Dict[str, Any]):
        """Execute a single automation step"""
        pin = step.get("pin")
        action = step.get("action")
        value = step.get("value", "")

        if not pin or not action:
            return

        try:
            if action == "HIGH":
                self.backend.digital_write(int(pin), 1)
            elif action == "LOW":
                self.backend.digital_write(int(pin), 0)
            elif action == "READ":
                if pin.startswith('A'):
                    self.backend.analog_read(pin)
                else:
                    self.backend.digital_read(int(pin))
        except Exception as e:
            print(f"Step execution error: {e}")

    def _sequence_completed(self):
        """Handle sequence completion"""
        self.active_sequence = None
        self.animation_state = AnimationState.IDLE
        self.start_seq_btn.config(state=tk.NORMAL)
        self.stop_seq_btn.config(state=tk.DISABLED)

    def _save_sequence(self):
        """Save current sequence to file"""
        # Get steps from tree
        steps = []
        for item in self.step_tree.get_children():
            values = self.step_tree.item(item)["values"]
            steps.append({
                "pin": values[0],
                "action": values[1],
                "value": values[2],
                "delay": float(values[3].replace('s', ''))
            })

        if not steps:
            messagebox.showerror("Error", "No steps to save")
            return

        # Create sequence
        sequence = AutomationSequence(
            name=f"Custom_{int(time.time())}",
            steps=steps,
            duration=float(self.duration_var.get()),
            loop=self.loop_var.get()
        )

        # Save to file
        filename = f"sequence_{sequence.name}.json"
        try:
            with open(filename, 'w') as f:
                json.dump({
                    "name": sequence.name,
                    "steps": sequence.steps,
                    "duration": sequence.duration,
                    "loop": sequence.loop
                }, f, indent=2)
            messagebox.showinfo("Success", f"Sequence saved as {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save sequence: {e}")

    def _load_sequence(self):
        """Load sequence from file"""
        from tkinter import filedialog
        filename = filedialog.askopenfilename(
            title="Load Sequence",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)

                # Clear existing steps
                for item in self.step_tree.get_children():
                    self.step_tree.delete(item)

                # Add loaded steps
                for step in data.get("steps", []):
                    self.step_tree.insert("", tk.END, values=(
                        step.get("pin", ""),
                        step.get("action", ""),
                        step.get("value", ""),
                        f"{step.get('delay', 1.0):.1f}s"
                    ))

                # Update settings
                self.duration_var.set(str(data.get("duration", 5.0)))
                self.loop_var.set(data.get("loop", False))

                messagebox.showinfo("Success", "Sequence loaded successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load sequence: {e}")

    def _preview_animation(self):
        """Preview animation with smooth motion"""
        if not self.butter_smooth:
            messagebox.showinfo("Info", "Enable Butter Smooth mode for animation preview")
            return

        # Create smooth animation preview
        self._animate_preview_wave()

    def _animate_preview_wave(self):
        """Animate a smooth wave pattern"""
        # Clear canvas
        self.preview_canvas.delete("all")

        # Draw smooth wave
        width = int(self.preview_canvas['width'])
        height = int(self.preview_canvas['height'])

        # Animate wave
        for x in range(0, width, 2):
            # Calculate smooth wave using easing
            t = x / width
            eased_t = self._apply_easing(t, self.easing_var.get())

            y = height/2 * (1 - eased_t) + 20 * math.sin(t * 4 * math.pi)

            # Draw smooth line
            color_intensity = int(255 * eased_t)
            color = f"#{color_intensity:02x}{100:02x}{255-color_intensity:02x}"

            self.preview_canvas.create_oval(x-1, y-1, x+1, y+1, fill=color, outline="")

        # Schedule next frame for smooth animation
        if self.butter_smooth:
            self.root.after(50, self._animate_preview_wave)

    def _apply_easing(self, t: float, easing_type: str) -> float:
        """Apply easing function"""
        if easing_type == "linear":
            return t
        elif easing_type == "ease_in":
            return t * t
        elif easing_type == "ease_out":
            return 1 - (1 - t) ** 2
        elif easing_type == "ease_in_out":
            return 3 * t * t - 2 * t * t * t
        elif easing_type == "bounce":
            if t < 1/2.75:
                return 7.5625 * t * t
            elif t < 2/2.75:
                t -= 1.5/2.75
                return 7.5625 * t * t + 0.75
            elif t < 2.5/2.75:
                t -= 2.25/2.75
                return 7.5625 * t * t + 0.9375
            else:
                t -= 2.625/2.75
                return 7.5625 * t * t + 0.984375
        return t

    def _update_ports(self):
        """Update list of available serial ports"""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo['values'] = ports
        if ports and not self.port_var.get():
            self.port_var.set(ports[0])

    def _connect(self):
        """Connect to Arduino using professional backend"""
        port = self.port_var.get()
        if not port:
            messagebox.showerror("Error", "Please select a serial port")
            return

        baudrate = int(self.baud_var.get())

        if self.backend_manager:
            # Use professional backend
            if self.backend_manager.connect_hardware(port, baudrate):
                self._on_hardware_connected()
            else:
                messagebox.showerror("Error", "Failed to connect to Arduino")
        else:
            # Use simple backend
            if self.backend.connect(port, baudrate):
                self.connect_btn.config(state=tk.DISABLED)
                self.disconnect_btn.config(state=tk.NORMAL)
                self.status_var.set(f"Connected to {port}")
                messagebox.showinfo("Success", f"Connected to Arduino on {port}")
            else:
                messagebox.showerror("Error", "Failed to connect to Arduino")

    def _disconnect(self):
        """Disconnect from Arduino using professional backend"""
        if self.backend_manager:
            # Use professional backend
            self.backend_manager.disconnect_hardware()
            self._on_hardware_disconnected()
        else:
            # Use simple backend
            self.backend.disconnect()
            self.connect_btn.config(state=tk.NORMAL)
            self.disconnect_btn.config(state=tk.DISABLED)
            self.status_var.set("Disconnected")

    def _test_connection(self):
        """Test Arduino connection"""
        if not self.backend.is_connected:
            messagebox.showerror("Error", "Not connected to Arduino")
            return

        response = self.backend.send_command("GET_STATUS")
        if response.startswith("STATUS:"):
            messagebox.showinfo("Connection Test", "Arduino is responding correctly")
        else:
            messagebox.showerror("Connection Test", f"Unexpected response: {response}")

    def _set_digital_high(self, pin: int):
        """Set digital pin HIGH using professional backend"""
        if self.backend_manager:
            # Use professional backend
            if self.backend_manager.hardware_service.digital_write(pin, 1):
                self.digital_vars[pin].set("HIGH")
            else:
                messagebox.showerror("Error", f"Failed to set pin {pin} HIGH")
        else:
            # Use simple backend
            if self.backend.is_connected:
                response = self.backend.digital_write(pin, 1)
                if response == "OK":
                    self.digital_vars[pin].set("HIGH")
                else:
                    messagebox.showerror("Error", f"Failed to set pin {pin} HIGH: {response}")

    def _set_digital_low(self, pin: int):
        """Set digital pin LOW using professional backend"""
        if self.backend_manager:
            # Use professional backend
            if self.backend_manager.hardware_service.digital_write(pin, 0):
                self.digital_vars[pin].set("LOW")
            else:
                messagebox.showerror("Error", f"Failed to set pin {pin} LOW")
        else:
            # Use simple backend
            if self.backend.is_connected:
                response = self.backend.digital_write(pin, 0)
                if response == "OK":
                    self.digital_vars[pin].set("LOW")
                else:
                    messagebox.showerror("Error", f"Failed to set pin {pin} LOW: {response}")

    def _read_digital(self, pin: int):
        """Read digital pin state using professional backend"""
        if self.backend_manager:
            # Use professional backend
            state = self.backend_manager.hardware_service.digital_read(pin)
            if state is not None:
                state_text = "HIGH" if state == 1 else "LOW"
                self.digital_vars[pin].set(state_text)
            else:
                messagebox.showerror("Error", f"Failed to read pin {pin}")
        else:
            # Use simple backend
            if self.backend.is_connected:
                response = self.backend.digital_read(pin)
                if response in ["0", "1"]:
                    state = "HIGH" if response == "1" else "LOW"
                    self.digital_vars[pin].set(state)
                else:
                    messagebox.showerror("Error", f"Failed to read pin {pin}: {response}")

    def _read_analog(self, pin: str):
        """Read analog pin value using professional backend"""
        if self.backend_manager:
            # Use professional backend
            value = self.backend_manager.hardware_service.analog_read(pin)
            if value is not None:
                self.analog_vars[pin].set(str(value))
            else:
                messagebox.showerror("Error", f"Failed to read {pin}")
        else:
            # Use simple backend
            if self.backend.is_connected:
                response = self.backend.analog_read(pin)
                if response.isdigit():
                    self.analog_vars[pin].set(response)
                else:
                    messagebox.showerror("Error", f"Failed to read {pin}: {response}")

    def _get_arduino_status(self):
        """Get Arduino status using professional backend"""
        if self.backend_manager:
            # Use professional backend
            status = self.backend_manager.get_system_status()
            health_score = status.get("hardware", {}).get("health_score", 0)
            response_time = status.get("hardware", {}).get("response_time", 0)

            status_text = f"Health Score: {health_score:.1f}%\n"
            status_text += f"Response Time: {response_time:.3f}s\n"
            status_text += f"Total Commands: {status.get('hardware', {}).get('total_commands', 0)}\n"
            status_text += f"Errors: {status.get('hardware', {}).get('error_count', 0)}\n"

            self._add_to_monitor(f"System Status:\n{status_text}\n")
        else:
            # Use simple backend
            if self.backend.is_connected:
                response = self.backend.get_status()
                self._add_to_monitor(f"Status: {response}\n")

    def _clear_monitor(self):
        """Clear monitor text"""
        self.status_text.delete(1.0, tk.END)

    def _toggle_auto_refresh(self):
        """Toggle auto refresh"""
        self.auto_refresh = not self.auto_refresh
        if self.auto_refresh:
            self._auto_refresh_status()

    def _auto_refresh_status(self):
        """Auto refresh Arduino status"""
        if self.auto_refresh and self.backend.is_connected:
            self._get_arduino_status()
            self.root.after(1000, self._auto_refresh_status)  # Refresh every second

    def _add_to_monitor(self, text: str):
        """Add text to monitor"""
        self.status_text.insert(tk.END, text)
        self.status_text.see(tk.END)

    def _communication_loop(self):
        """Background communication loop"""
        while self.running:
            try:
                # Process any queued messages
                while not self.message_queue.empty():
                    message = self.message_queue.get_nowait()
                    # Handle incoming messages if needed
                    pass
            except Exception as e:
                print(f"Communication error: {e}")

            time.sleep(0.1)

    def create_settings_tab(self):
        """Create settings tab for smooth motion configuration"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text='⚙️ Settings')

        # Animation settings
        anim_frame = ttk.LabelFrame(settings_frame, text="Animation Settings")
        anim_frame.pack(fill=tk.X, padx=5, pady=5)

        # Butter smooth mode
        self.butter_smooth_var = tk.BooleanVar(value=True)
        smooth_check = ttk.Checkbutton(
            anim_frame,
            text="🧈 Butter Smooth Mode (60 FPS animations)",
            variable=self.butter_smooth_var,
            command=self._toggle_butter_smooth
        )
        smooth_check.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)

        # Animation speed
        ttk.Label(anim_frame, text="Animation Speed:").grid(row=1, column=0, padx=5, pady=5)
        self.anim_speed_var = tk.DoubleVar(value=1.0)
        speed_scale = ttk.Scale(
            anim_frame,
            from_=0.1,
            to=3.0,
            variable=self.anim_speed_var,
            orient=tk.HORIZONTAL,
            command=self._update_animation_speed
        )
        speed_scale.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)

        # Smooth transitions
        self.smooth_transitions_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            anim_frame,
            text="Smooth Transitions",
            variable=self.smooth_transitions_var
        ).grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)

        # Performance settings
        perf_frame = ttk.LabelFrame(settings_frame, text="Performance Settings")
        perf_frame.pack(fill=tk.X, padx=5, pady=5)

        # Auto refresh interval
        ttk.Label(perf_frame, text="Auto Refresh (ms):").grid(row=0, column=0, padx=5, pady=5)
        self.refresh_interval_var = tk.IntVar(value=100)
        refresh_scale = ttk.Scale(
            perf_frame,
            from_=50,
            to=1000,
            variable=self.refresh_interval_var,
            orient=tk.HORIZONTAL,
            command=self._update_refresh_interval
        )
        refresh_scale.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

        # Connection timeout
        ttk.Label(perf_frame, text="Connection Timeout (s):").grid(row=1, column=0, padx=5, pady=5)
        self.timeout_var = tk.DoubleVar(value=2.0)
        timeout_scale = ttk.Scale(
            perf_frame,
            from_=1.0,
            to=10.0,
            variable=self.timeout_var,
            orient=tk.HORIZONTAL
        )
        timeout_scale.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)

        # Visual settings
        visual_frame = ttk.LabelFrame(settings_frame, text="Visual Settings")
        visual_frame.pack(fill=tk.X, padx=5, pady=5)

        # Theme selection
        ttk.Label(visual_frame, text="Theme:").grid(row=0, column=0, padx=5, pady=5)
        self.theme_var = tk.StringVar(value="smooth")
        theme_combo = ttk.Combobox(
            visual_frame,
            textvariable=self.theme_var,
            values=["smooth", "classic", "dark", "colorful"],
            width=15
        )
        theme_combo.grid(row=0, column=1, padx=5, pady=5)

        # Apply theme button
        ttk.Button(
            visual_frame,
            text="🎨 Apply Theme",
            command=self._apply_theme,
            style='Smooth.TButton'
        ).grid(row=0, column=2, padx=5, pady=5)

        # Color customization
        color_frame = ttk.Frame(visual_frame)
        color_frame.grid(row=1, column=0, columnspan=3, padx=5, pady=5)

        self.color_vars = {}
        colors = ["Primary", "Secondary", "Accent", "Background"]

        for i, color_name in enumerate(colors):
            ttk.Label(color_frame, text=f"{color_name}:").grid(row=i, column=0, padx=2)
            self.color_vars[color_name.lower()] = tk.StringVar(value="#2196F3")
            color_entry = ttk.Entry(color_frame, textvariable=self.color_vars[color_name.lower()], width=10)
            color_entry.grid(row=i, column=1, padx=2)

            ttk.Button(
                color_frame,
                text="🎨",
                command=lambda c=color_name.lower(): self._choose_color(c),
                width=3
            ).grid(row=i, column=2, padx=2)

        # Advanced settings
        adv_frame = ttk.LabelFrame(settings_frame, text="Advanced Settings")
        adv_frame.pack(fill=tk.X, padx=5, pady=5)

        # Debug mode
        self.debug_var = tk.BooleanVar()
        ttk.Checkbutton(
            adv_frame,
            text="Debug Mode (Show performance metrics)",
            variable=self.debug_var,
            command=self._toggle_debug_mode
        ).grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)

        # Log to file
        self.log_var = tk.BooleanVar()
        ttk.Checkbutton(
            adv_frame,
            text="Log to File",
            variable=self.log_var,
            command=self._toggle_logging
        ).grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)

        # Reset settings button
        ttk.Button(
            adv_frame,
            text="🔄 Reset to Defaults",
            command=self._reset_settings,
            style='Smooth.TButton'
        ).grid(row=2, column=0, columnspan=2, pady=10)

    def _update_base(self, value):
        """Update base rotation"""
        if self.backend.is_connected:
            self.backend.digital_write(2, int(float(value)))

    def _update_shoulder(self, value):
        """Update shoulder angle"""
        if self.backend.is_connected:
            self.backend.digital_write(3, int(float(value)))

    def _update_elbow(self, value):
        """Update elbow angle"""
        if self.backend.is_connected:
            self.backend.digital_write(4, int(float(value)))

    def _update_wrist_pitch(self, value):
        """Update wrist pitch angle"""
        if self.backend.is_connected:
            self.backend.digital_write(5, int(float(value)))

    def _update_wrist_roll(self, value):
        """Update wrist roll angle"""
        if self.backend.is_connected:
            self.backend.digital_write(6, int(float(value)))

    def _update_gripper(self, value):
        """Update gripper position"""
        if self.backend.is_connected:
            self.backend.digital_write(7, int(float(value)))

    def _go_home(self):
        """Move to home position"""
        self.base_var.set(90)
        self.shoulder_var.set(90)
        self.elbow_var.set(90)
        self.wrist_pitch_var.set(90)
        self.wrist_roll_var.set(90)
        self.gripper_var.set(90)

        # Apply positions
        self._update_base(90)
        self._update_shoulder(90)
        self._update_elbow(90)
        self._update_wrist_pitch(90)
        self._update_wrist_roll(90)
        self._update_gripper(90)

    def _go_zero(self):
        """Move to zero position"""
        self.base_var.set(0)
        self.shoulder_var.set(0)
        self.elbow_var.set(0)
        self.wrist_pitch_var.set(0)
        self.wrist_roll_var.set(0)
        self.gripper_var.set(0)

        # Apply positions
        self._update_base(0)
        self._update_shoulder(0)
        self._update_elbow(0)
        self._update_wrist_pitch(0)
        self._update_wrist_roll(0)
        self._update_gripper(0)

    def _go_pick(self):
        """Move to pick position"""
        self.base_var.set(45)
        self.shoulder_var.set(120)
        self.elbow_var.set(60)
        self.wrist_pitch_var.set(90)
        self.wrist_roll_var.set(90)
        self.gripper_var.set(140)

        # Apply positions
        self._update_base(45)
        self._update_shoulder(120)
        self._update_elbow(60)
        self._update_wrist_pitch(90)
        self._update_wrist_roll(90)
        self._update_gripper(140)

    def _go_place(self):
        """Move to place position"""
        self.base_var.set(135)
        self.shoulder_var.set(120)
        self.elbow_var.set(60)
        self.wrist_pitch_var.set(90)
        self.wrist_roll_var.set(90)
        self.gripper_var.set(140)

        # Apply positions
        self._update_base(135)
        self._update_shoulder(120)
        self._update_elbow(60)
        self._update_wrist_pitch(90)
        self._update_wrist_roll(90)
        self._update_gripper(140)

    def _preset_1(self):
        """Preset position 1"""
        self.base_var.set(30)
        self.shoulder_var.set(60)
        self.elbow_var.set(120)
        self.wrist_pitch_var.set(45)
        self.wrist_roll_var.set(90)
        self.gripper_var.set(90)

    def _preset_2(self):
        """Preset position 2"""
        self.base_var.set(150)
        self.shoulder_var.set(60)
        self.elbow_var.set(120)
        self.wrist_pitch_var.set(135)
        self.wrist_roll_var.set(90)
        self.gripper_var.set(90)

    def _preset_3(self):
        """Preset position 3"""
        self.base_var.set(90)
        self.shoulder_var.set(30)
        self.elbow_var.set(150)
        self.wrist_pitch_var.set(90)
        self.wrist_roll_var.set(45)
        self.gripper_var.set(90)

    def _preset_4(self):
        """Preset position 4"""
        self.base_var.set(90)
        self.shoulder_var.set(150)
        self.elbow_var.set(30)
        self.wrist_pitch_var.set(90)
        self.wrist_roll_var.set(135)
        self.gripper_var.set(90)

    def _update_servo_angle(self, value):
        """Update servo angle"""
        pass  # Placeholder for servo angle updates

    def _update_servo_speed(self, value):
        """Update servo speed"""
        pass  # Placeholder for servo speed updates

    def _move_servo(self):
        """Move selected servo"""
        servo = self.servo_var.get()
        angle = self.servo_angle_var.get()
        if servo and self.backend.is_connected:
            # Map servo names to pins
            servo_map = {
                "Base": 2,
                "Shoulder": 3,
                "Elbow": 4,
                "Wrist Pitch": 5,
                "Wrist Roll": 6,
                "Gripper": 7
            }
            pin = servo_map.get(servo)
            if pin:
                self.backend.digital_write(pin, angle)

    def _center_servo(self):
        """Center selected servo"""
        self.servo_angle_var.set(90)
        self._move_servo()

    def _test_servo_range(self):
        """Test servo range"""
        servo = self.servo_var.get()
        if servo and self.backend.is_connected:
            # Test from 0 to 180 degrees
            for angle in range(0, 181, 10):
                self.servo_angle_var.set(angle)
                self._move_servo()
                time.sleep(0.1)

    def _scan_bus_servos(self):
        """Scan for bus servos"""
        if self.backend.is_connected:
            response = self.backend.send_command("SCAN_BUS")
            messagebox.showinfo("Bus Scan", f"Scan result: {response}")

    def _configure_bus_servos(self):
        """Configure bus servos"""
        if self.backend.is_connected:
            response = self.backend.send_command("CONFIG_BUS")
            messagebox.showinfo("Bus Config", f"Config result: {response}")

    def _sync_move_servos(self):
        """Synchronously move all servos"""
        if self.backend.is_connected:
            # Send all servo positions at once
            positions = f"SYNC:{self.base_var.get()},{self.shoulder_var.get()},{self.elbow_var.get()},"
            positions += f"{self.wrist_pitch_var.get()},{self.wrist_roll_var.get()},{self.gripper_var.get()}"
            response = self.backend.send_command(positions)
            messagebox.showinfo("Sync Move", f"Sync result: {response}")

    def _toggle_butter_smooth(self):
        """Toggle butter smooth animation mode"""
        self.butter_smooth = self.butter_smooth_var.get()
        if self.butter_smooth:
            self.anim_var.set("✨ Butter Smooth (60 FPS)")
        else:
            self.anim_var.set("⚡ Fast Mode")

    def _update_animation_speed(self, value):
        """Update animation speed"""
        self.animation_speed = float(value)
        self.motion_controller.animation_speed = self.animation_speed

    def _update_refresh_interval(self, value):
        """Update auto refresh interval"""
        self.auto_refresh_interval = int(float(value))

    def _apply_theme(self):
        """Apply selected theme"""
        theme = self.theme_var.get()

        if theme == "smooth":
            self._apply_smooth_theme()
        elif theme == "dark":
            self._apply_dark_theme()
        elif theme == "classic":
            self._apply_classic_theme()
        elif theme == "colorful":
            self._apply_colorful_theme()

        messagebox.showinfo("Theme Applied", f"{theme.title()} theme applied successfully!")

    def _apply_smooth_theme(self):
        """Apply smooth theme colors"""
        self.root.configure(bg="#f5f5f5")
        # Update other elements...

    def _apply_dark_theme(self):
        """Apply dark theme"""
        self.root.configure(bg="#333333")
        # Update other elements...

    def _apply_classic_theme(self):
        """Apply classic theme"""
        self.root.configure(bg="#ffffff")
        # Update other elements...

    def _apply_colorful_theme(self):
        """Apply colorful theme"""
        self.root.configure(bg="#e8f4f8")
        # Update other elements...

    def _choose_color(self, color_type):
        """Choose custom color"""
        color = colorchooser.askcolor(title=f"Choose {color_type} color")
        if color[1]:
            self.color_vars[color_type].set(color[1])

    def _toggle_debug_mode(self):
        """Toggle debug mode"""
        if self.debug_var.get():
            self.perf_label.grid()
        else:
            self.perf_label.grid_remove()

    def _toggle_logging(self):
        """Toggle file logging"""
        if self.log_var.get():
            # Start logging
            self.log_file = open("arduino_control.log", "a")
        else:
            # Stop logging
            if hasattr(self, 'log_file'):
                self.log_file.close()

    def _reset_settings(self):
        """Reset all settings to defaults"""
        self.butter_smooth_var.set(True)
        self.anim_speed_var.set(1.0)
        self.refresh_interval_var.set(100)
        self.timeout_var.set(2.0)
        self.theme_var.set("smooth")
        self.debug_var.set(False)
        self.log_var.set(False)

        # Apply defaults
        self._toggle_butter_smooth()
        self._update_animation_speed(1.0)
        self._update_refresh_interval(100)
        self._apply_theme()

    def __del__(self):
        """Enhanced cleanup with professional backend support"""
        self.running = False

        # Cleanup professional backend
        if self.backend_manager:
            # Unregister event listeners
            if self.event_listeners_registered:
                # Note: In a real implementation, you'd track and remove specific listeners
                pass

            # Cleanup backend
            self.backend_manager.cleanup()
        else:
            # Cleanup simple backend
            if hasattr(self, 'backend'):
                self.backend.disconnect()


def main():
    """Main function"""
    root = tk.Tk()
    app = ArduinoGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()