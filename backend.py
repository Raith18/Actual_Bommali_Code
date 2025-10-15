"""
Professional Backend System for STM32 Nucleo G474RE Hardware Control
High-performance ARM Cortex-M4 microcontroller with advanced servo control
Provides proper hardware abstraction, service layers, and event-driven architecture
"""

import serial
import serial.tools.list_ports
import threading
import time
import queue
import logging
from typing import Optional, Dict, Any, List, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import json
import os
from datetime import datetime


class HardwareState(Enum):
    """Hardware connection states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RECONNECTING = "reconnecting"


class EventType(Enum):
    """System event types"""
    CONNECTION_ESTABLISHED = "connection_established"
    CONNECTION_LOST = "connection_lost"
    HARDWARE_ERROR = "hardware_error"
    PIN_STATE_CHANGED = "pin_state_changed"
    ANALOG_VALUE_CHANGED = "analog_value_changed"
    SEQUENCE_STARTED = "sequence_started"
    SEQUENCE_COMPLETED = "sequence_completed"
    SYSTEM_STATUS = "system_status"


@dataclass
class HardwareEvent:
    """Hardware event data structure"""
    event_type: EventType
    timestamp: float
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = "hardware"


@dataclass
class PinConfiguration:
    """Pin configuration settings"""
    pin_number: int
    mode: str  # INPUT, OUTPUT, INPUT_PULLUP
    initial_state: int = 0
    debounce_ms: int = 50
    smoothing_enabled: bool = True
    smoothing_factor: float = 0.3


@dataclass
class HardwareStatus:
    """Hardware status information"""
    state: HardwareState
    connected_at: Optional[float] = None
    last_command: Optional[float] = None
    total_commands: int = 0
    successful_commands: int = 0
    error_count: int = 0
    average_response_time: float = 0.0
    pin_states: Dict[int, int] = field(default_factory=dict)
    analog_values: Dict[str, int] = field(default_factory=dict)


class HardwareMonitor:
    """Monitors hardware health and performance"""

    def __init__(self):
        self.status = HardwareStatus(HardwareState.DISCONNECTED)
        self.response_times: List[float] = []
        self.error_log: List[Dict[str, Any]] = []
        self.performance_history: List[Dict[str, Any]] = []

    def update_response_time(self, response_time: float):
        """Update response time tracking"""
        self.response_times.append(response_time)
        if len(self.response_times) > 100:  # Keep last 100 measurements
            self.response_times.pop(0)

        # Update average
        self.status.average_response_time = sum(self.response_times) / len(self.response_times)

    def record_command(self, success: bool):
        """Record command execution"""
        self.status.total_commands += 1
        if success:
            self.status.successful_commands += 1
        else:
            self.status.error_count += 1

    def record_error(self, error: str, context: str = ""):
        """Record hardware error"""
        self.status.error_count += 1
        error_entry = {
            "timestamp": time.time(),
            "error": error,
            "context": context,
            "state": self.status.state.value
        }
        self.error_log.append(error_entry)

        # Keep only last 50 errors
        if len(self.error_log) > 50:
            self.error_log.pop(0)

    def get_health_score(self) -> float:
        """Calculate hardware health score (0-100)"""
        if self.status.total_commands == 0:
            return 100.0 if self.status.state == HardwareState.CONNECTED else 0.0

        success_rate = self.status.successful_commands / self.status.total_commands

        # Factor in response time (ideal < 100ms)
        response_penalty = min(20.0, max(0, (self.status.average_response_time - 0.1) * 100))

        # Factor in error rate
        error_penalty = (self.status.error_count / max(1, self.status.total_commands)) * 30

        health_score = (success_rate * 100) - response_penalty - error_penalty
        return max(0.0, min(100.0, health_score))


class EventManager:
    """Event-driven system for hardware notifications"""

    def __init__(self):
        self.listeners: Dict[EventType, List[Callable]] = {}
        self.event_queue = queue.Queue()
        self.running = False
        self.event_thread: Optional[threading.Thread] = None

    def start(self):
        """Start event processing thread"""
        self.running = True
        self.event_thread = threading.Thread(target=self._process_events, daemon=True)
        self.event_thread.start()

    def stop(self):
        """Stop event processing"""
        self.running = False
        if self.event_thread:
            self.event_thread.join(timeout=1.0)

    def subscribe(self, event_type: EventType, callback: Callable):
        """Subscribe to event notifications"""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(callback)

    def unsubscribe(self, event_type: EventType, callback: Callable):
        """Unsubscribe from event notifications"""
        if event_type in self.listeners:
            try:
                self.listeners[event_type].remove(callback)
            except ValueError:
                pass

    def emit(self, event: HardwareEvent):
        """Emit hardware event"""
        self.event_queue.put(event)

    def _process_events(self):
        """Process events in background thread"""
        while self.running:
            try:
                event = self.event_queue.get(timeout=0.1)

                # Notify all listeners for this event type
                if event.event_type in self.listeners:
                    for callback in self.listeners[event.event_type]:
                        try:
                            callback(event)
                        except Exception as e:
                            logging.error(f"Event callback error: {e}")

                self.event_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Event processing error: {e}")


class HardwareInterface(ABC):
    """Abstract hardware interface"""

    @abstractmethod
    def connect(self, port: str, baudrate: int = 115200) -> bool:
        """Connect to hardware"""
        pass

    @abstractmethod
    def disconnect(self):
        """Disconnect from hardware"""
        pass

    @abstractmethod
    def send_command(self, command: str) -> str:
        """Send command to hardware"""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check connection status"""
        pass


class STM32HardwareInterface(HardwareInterface):
    """STM32 Nucleo G474RE hardware interface implementation"""

    def __init__(self, monitor: HardwareMonitor):
        self.serial_port: Optional[serial.Serial] = None
        self.monitor = monitor
        self.command_lock = threading.Lock()

    def connect(self, port: str, baudrate: int = 115200) -> bool:
        """Connect to STM32 Nucleo with proper initialization"""
        try:
            self.serial_port = serial.Serial(port, baudrate, timeout=1)
            time.sleep(2)  # Allow Arduino to initialize

            # Test connection
            if self._test_connection():
                self.monitor.status.state = HardwareState.CONNECTED
                self.monitor.status.connected_at = time.time()
                return True
            else:
                self.serial_port.close()
                return False
        except serial.SerialException as e:
            self.monitor.record_error(f"Connection failed: {e}", f"Port: {port}, Baud: {baudrate}")
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
        """Disconnect from Arduino"""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.monitor.status.state = HardwareState.DISCONNECTED

    def send_command(self, command: str) -> str:
        """Send command with proper error handling"""
        if not self.is_connected():
            return "Hardware not connected"

        with self.command_lock:
            start_time = time.time()
            try:
                self.serial_port.write(f"{command}\n".encode())
                response = self.serial_port.readline().decode().strip()

                # Update monitoring
                response_time = time.time() - start_time
                self.monitor.update_response_time(response_time)
                self.monitor.record_command(True)
                self.monitor.status.last_command = time.time()

                return response
            except Exception as e:
                response_time = time.time() - start_time
                self.monitor.update_response_time(response_time)
                self.monitor.record_command(False)
                self.monitor.record_error(str(e), command)
                return f"Command error: {e}"

    def is_connected(self) -> bool:
        """Check if hardware is connected"""
        return (self.serial_port is not None and
                self.serial_port.is_open and
                self.monitor.status.state == HardwareState.CONNECTED)


class HardwareService:
    """Service layer for hardware operations"""

    def __init__(self, hardware_interface: HardwareInterface, event_manager: EventManager):
        self.hardware = hardware_interface
        self.events = event_manager
        self.pin_configs: Dict[int, PinConfiguration] = {}
        self.analog_smoothing: Dict[str, List[int]] = {}
        self.smoothing_window = 5

        # Subscribe to relevant events
        self.events.subscribe(EventType.CONNECTION_ESTABLISHED, self._on_connection_established)
        self.events.subscribe(EventType.CONNECTION_LOST, self._on_connection_lost)

    def configure_pin(self, pin: int, mode: str, debounce_ms: int = 50,
                     smoothing: bool = True) -> bool:
        """Configure pin with specified settings"""
        try:
            response = self.hardware.send_command(f"PIN_MODE:{pin}:{mode}")
            if response == "OK":
                config = PinConfiguration(
                    pin_number=pin,
                    mode=mode,
                    debounce_ms=debounce_ms,
                    smoothing_enabled=smoothing
                )
                self.pin_configs[pin] = config
                return True
        except Exception as e:
            logging.error(f"Pin configuration error: {e}")
        return False

    def digital_write(self, pin: int, state: int) -> bool:
        """Write digital value to pin"""
        if pin not in self.pin_configs:
            # Auto-configure if not configured
            self.configure_pin(pin, "OUTPUT")

        try:
            response = self.hardware.send_command(f"DIGITAL_WRITE:{pin}:{state}")
            if response == "OK":
                # Emit state change event
                event = HardwareEvent(
                    EventType.PIN_STATE_CHANGED,
                    time.time(),
                    {"pin": pin, "state": state, "type": "digital"}
                )
                self.events.emit(event)
                return True
        except Exception as e:
            logging.error(f"Digital write error: {e}")
        return False

    def digital_read(self, pin: int) -> Optional[int]:
        """Read digital value from pin"""
        try:
            response = self.hardware.send_command(f"DIGITAL_READ:{pin}")
            if response in ["0", "1"]:
                state = int(response)

                # Emit state change event
                event = HardwareEvent(
                    EventType.PIN_STATE_CHANGED,
                    time.time(),
                    {"pin": pin, "state": state, "type": "digital"}
                )
                self.events.emit(event)

                return state
        except Exception as e:
            logging.error(f"Digital read error: {e}")
        return None

    def analog_read(self, pin: str) -> Optional[int]:
        """Read analog value with smoothing"""
        try:
            response = self.hardware.send_command(f"ANALOG_READ:{pin}")
            if response.isdigit():
                value = int(response)

                # Apply smoothing if enabled
                if pin in self.analog_smoothing:
                    smoothed = self._apply_smoothing(pin, value)
                    final_value = int(smoothed)
                else:
                    final_value = value
                    self.analog_smoothing[pin] = [value] * self.smoothing_window

                # Emit value change event
                event = HardwareEvent(
                    EventType.ANALOG_VALUE_CHANGED,
                    time.time(),
                    {"pin": pin, "value": final_value, "raw_value": value}
                )
                self.events.emit(event)

                return final_value
        except Exception as e:
            logging.error(f"Analog read error: {e}")
        return None

    def _apply_smoothing(self, pin: str, new_value: int) -> float:
        """Apply smoothing filter to analog values"""
        values = self.analog_smoothing[pin]

        # Exponential smoothing
        smoothed = values[-1] * 0.7 + new_value * 0.3

        # Update smoothing window
        values.append(int(smoothed))
        if len(values) > self.smoothing_window:
            values.pop(0)

        return smoothed

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive hardware status"""
        try:
            response = self.hardware.send_command("GET_STATUS")
            if response.startswith("STATUS:"):
                # Parse status string
                states = response[7:].split(',')
                pin_states = {}
                for i, state in enumerate(states):
                    pin_num = i + 2  # Pins start from 2
                    pin_states[pin_num] = int(state)

                # Update monitor
                self.hardware.monitor.status.pin_states = pin_states

                # Emit status event
                event = HardwareEvent(
                    EventType.SYSTEM_STATUS,
                    time.time(),
                    {
                        "pin_states": pin_states,
                        "health_score": self.hardware.monitor.get_health_score(),
                        "response_time": self.hardware.monitor.status.average_response_time
                    }
                )
                self.events.emit(event)

                return {
                    "pin_states": pin_states,
                    "health_score": self.hardware.monitor.get_health_score(),
                    "response_time": self.hardware.monitor.status.average_response_time,
                    "total_commands": self.hardware.monitor.status.total_commands,
                    "error_count": self.hardware.monitor.status.error_count
                }
        except Exception as e:
            logging.error(f"Status read error: {e}")
        return {}

    def _on_connection_established(self, event: HardwareEvent):
        """Handle connection established event"""
        logging.info("Hardware connection established")

        # Initialize pin configurations
        for pin, config in self.pin_configs.items():
            self.configure_pin(pin, config.mode)

    def _on_connection_lost(self, event: HardwareEvent):
        """Handle connection lost event"""
        logging.warning("Hardware connection lost")

        # Clear smoothing data
        self.analog_smoothing.clear()


class AutomationEngine:
    """Advanced automation engine for hardware control sequences"""

    def __init__(self, hardware_service: HardwareService, event_manager: EventManager):
        self.hardware = hardware_service
        self.events = event_manager
        self.sequences: Dict[str, Dict[str, Any]] = {}
        self.active_sequences: Dict[str, threading.Thread] = {}
        self.sequence_states: Dict[str, Dict[str, Any]] = {}

    def create_sequence(self, name: str, steps: List[Dict[str, Any]],
                       loop: bool = False, interval: float = 1.0) -> bool:
        """Create automation sequence"""
        try:
            sequence = {
                "name": name,
                "steps": steps,
                "loop": loop,
                "interval": interval,
                "enabled": True,
                "current_step": 0,
                "start_time": None
            }

            self.sequences[name] = sequence

            # Emit sequence created event
            event = HardwareEvent(
                EventType.SEQUENCE_STARTED,
                time.time(),
                {"sequence_name": name, "step_count": len(steps)}
            )
            self.events.emit(event)

            return True
        except Exception as e:
            logging.error(f"Sequence creation error: {e}")
            return False

    def start_sequence(self, name: str) -> bool:
        """Start automation sequence"""
        if name not in self.sequences:
            logging.error(f"Sequence '{name}' not found")
            return False

        sequence = self.sequences[name]
        if not sequence["enabled"]:
            logging.error(f"Sequence '{name}' is disabled")
            return False

        # Stop if already running
        if name in self.active_sequences:
            self.stop_sequence(name)

        # Start sequence thread
        sequence["start_time"] = time.time()
        sequence["current_step"] = 0

        thread = threading.Thread(target=self._run_sequence, args=(name,), daemon=True)
        self.active_sequences[name] = thread
        thread.start()

        return True

    def stop_sequence(self, name: str) -> bool:
        """Stop automation sequence"""
        if name in self.active_sequences:
            thread = self.active_sequences[name]
            # Note: In a real implementation, you'd need a way to signal the thread to stop
            del self.active_sequences[name]

            # Emit sequence completed event
            event = HardwareEvent(
                EventType.SEQUENCE_COMPLETED,
                time.time(),
                {"sequence_name": name, "stopped": True}
            )
            self.events.emit(event)

            return True
        return False

    def _run_sequence(self, name: str):
        """Run sequence in background thread"""
        sequence = self.sequences[name]

        while name in self.active_sequences and sequence["enabled"]:
            steps = sequence["steps"]
            current_step = sequence["current_step"]

            if current_step >= len(steps):
                if sequence["loop"]:
                    sequence["current_step"] = 0
                    current_step = 0
                else:
                    break

            # Execute current step
            step = steps[current_step]
            self._execute_step(step)

            # Move to next step
            sequence["current_step"] += 1

            # Wait for next step
            time.sleep(sequence["interval"])

        # Sequence completed
        if name in self.active_sequences:
            del self.active_sequences[name]

        # Emit completion event
        event = HardwareEvent(
            EventType.SEQUENCE_COMPLETED,
            time.time(),
            {"sequence_name": name, "completed": True}
        )
        self.events.emit(event)

    def _execute_step(self, step: Dict[str, Any]):
        """Execute individual automation step"""
        try:
            action = step.get("action", "")
            pin = step.get("pin", "")
            value = step.get("value", 0)

            if action == "DIGITAL_WRITE":
                if pin.isdigit():
                    self.hardware.digital_write(int(pin), int(value))
            elif action == "ANALOG_READ":
                self.hardware.analog_read(pin)
            elif action == "WAIT":
                time.sleep(float(value))

        except Exception as e:
            logging.error(f"Step execution error: {e}")


class BackendManager:
    """Main backend manager coordinating all systems"""

    def __init__(self):
        # Logging setup first
        self._setup_logging()

        # Initialize core systems
        self.monitor = HardwareMonitor()
        self.events = EventManager()
        self.hardware_interface = STM32HardwareInterface(self.monitor)
        self.hardware_service = HardwareService(self.hardware_interface, self.events)
        self.automation_engine = AutomationEngine(self.hardware_service, self.events)

        # Start event system
        self.events.start()

        # Configuration
        self.config_file = "backend_config.json"
        self.load_configuration()

    def _setup_logging(self):
        """Setup logging system"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('backend.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("BackendManager")

    def connect_hardware(self, port: str, baudrate: int = 115200) -> bool:
        """Connect to hardware with full initialization"""
        self.logger.info(f"Connecting to hardware on {port}")

        if self.hardware_interface.connect(port, baudrate):
            # Emit connection event
            event = HardwareEvent(
                EventType.CONNECTION_ESTABLISHED,
                time.time(),
                {"port": port, "baudrate": baudrate}
            )
            self.events.emit(event)

            # Initialize default pin configurations
            self._initialize_default_pins()

            self.logger.info("Hardware connected successfully")
            return True
        else:
            # Emit connection failed event
            event = HardwareEvent(
                EventType.HARDWARE_ERROR,
                time.time(),
                {"error": "Connection failed", "port": port}
            )
            self.events.emit(event)

            self.logger.error("Hardware connection failed")
            return False

    def disconnect_hardware(self):
        """Disconnect from hardware"""
        self.logger.info("Disconnecting from hardware")

        # Stop all sequences
        for sequence_name in list(self.active_sequences.keys()):
            self.automation_engine.stop_sequence(sequence_name)

        self.hardware_interface.disconnect()

        # Emit disconnection event
        event = HardwareEvent(EventType.CONNECTION_LOST, time.time())
        self.events.emit(event)

    def _initialize_default_pins(self):
        """Initialize default pin configurations"""
        # Configure digital pins as outputs
        for pin in range(2, 14):
            self.hardware_service.configure_pin(pin, "OUTPUT")

        # Configure analog pins as inputs
        for pin in ['A0', 'A1', 'A2', 'A3', 'A4', 'A5']:
            # Note: Analog pins are input by default on STM32
            pass

        self.logger.info("Default pin configurations initialized")

    def save_configuration(self):
        """Save current configuration"""
        config = {
            "pin_configs": {
                pin: {
                    "mode": config.mode,
                    "debounce_ms": config.debounce_ms,
                    "smoothing_enabled": config.smoothing_enabled
                }
                for pin, config in self.hardware_service.pin_configs.items()
            },
            "sequences": self.automation_engine.sequences,
            "settings": {
                "smoothing_window": self.hardware_service.smoothing_window
            }
        }

        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            self.logger.info("Configuration saved")
        except Exception as e:
            self.logger.error(f"Configuration save error: {e}")

    def load_configuration(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)

                # Load pin configurations
                for pin_str, pin_config in config.get("pin_configs", {}).items():
                    pin = int(pin_str)
                    self.hardware_service.configure_pin(
                        pin,
                        pin_config["mode"],
                        pin_config["debounce_ms"],
                        pin_config["smoothing_enabled"]
                    )

                # Load sequences
                self.automation_engine.sequences = config.get("sequences", {})

                self.logger.info("Configuration loaded")
        except Exception as e:
            self.logger.error(f"Configuration load error: {e}")

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            "hardware": {
                "state": self.hardware_interface.monitor.status.state.value,
                "connected_at": self.hardware_interface.monitor.status.connected_at,
                "health_score": self.hardware_interface.monitor.get_health_score(),
                "response_time": self.hardware_interface.monitor.status.average_response_time,
                "total_commands": self.hardware_interface.monitor.status.total_commands,
                "error_count": self.hardware_interface.monitor.status.error_count
            },
            "active_sequences": list(self.automation_engine.active_sequences.keys()),
            "pin_states": self.hardware_interface.monitor.status.pin_states,
            "analog_values": self.hardware_interface.monitor.status.analog_values,
            "event_listeners": len(self.events.listeners)
        }

    def cleanup(self):
        """Cleanup all systems"""
        self.logger.info("Cleaning up backend systems")

        # Stop event system
        self.events.stop()

        # Disconnect hardware
        if self.hardware_interface.is_connected():
            self.hardware_interface.disconnect()

        # Save configuration
        self.save_configuration()


# Global backend instance
backend_manager = None


def get_backend() -> BackendManager:
    """Get or create backend instance"""
    global backend_manager
    if backend_manager is None:
        backend_manager = BackendManager()
    return backend_manager


def initialize_backend():
    """Initialize the complete backend system"""
    backend = get_backend()

    # Load configuration
    backend.load_configuration()

    return backend


if __name__ == "__main__":
    # Test backend system
    backend = initialize_backend()
    print("Backend system initialized")
    print(f"Status: {backend.get_system_status()}")

    # Cleanup on exit
    import atexit
    atexit.register(backend.cleanup)