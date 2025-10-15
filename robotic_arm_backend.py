"""
Professional Robotic Arm Backend System for PyQt5 GUI
Enhanced waypoint management, task sequences, and trajectory optimization
"""

import serial
import serial.tools.list_ports
import threading
import time
import queue
import logging
from typing import Optional, Dict, Any, List, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import os
from datetime import datetime
import math

class TrajectoryType(Enum):
    """Trajectory interpolation types"""
    SMOOTH = "smooth"
    LINEAR = "linear"
    CPG = "cpg"

class MotionProfile(Enum):
    """Motion profile types"""
    FAST = "fast"
    NORMAL = "normal"
    SLOW = "slow"
    PRECISE = "precise"

@dataclass
class Waypoint:
    """Enhanced waypoint with motion parameters"""
    positions: List[float]
    delay_ms: int = 500
    trajectory_type: TrajectoryType = TrajectoryType.SMOOTH
    motion_profile: MotionProfile = MotionProfile.NORMAL
    timestamp: float = field(default_factory=time.time)

@dataclass
class TaskSequence:
    """Enhanced task sequence with metadata"""
    name: str
    description: str = ""
    waypoints: List[Waypoint] = field(default_factory=list)
    loop_count: int = 0
    created_at: float = field(default_factory=time.time)
    modified_at: float = field(default_factory=time.time)

class RoboticArmBackend:
    """Professional backend for robotic arm control with PyQt5 integration"""

    def __init__(self, max_waypoints: int = 250, max_tasks: int = 6):
        # Setup logging
        self._setup_logging()

        # Core configuration
        self.max_waypoints = max_waypoints
        self.max_tasks = max_tasks

        # Serial communication
        self.serial_port: Optional[serial.Serial] = None
        self.is_connected = False
        self.current_port = None
        self.baudrate = 9600

        # Task management
        self.tasks: Dict[str, TaskSequence] = {}
        self.current_positions: List[float] = [0.0] * 7
        self.position_callbacks: List[Callable] = []

        # Motion parameters
        self.speed = 30.0  # deg/s
        self.duration = 1200  # ms
        self.precision = 1.0  # degrees
        self.cpg_alpha = 0.25
        self.cpg_enabled = False

        # Trajectory optimization
        self.interpolation_method = "quintic"
        self.backlash_compensation = 0.5  # degrees
        self.smoothness_factor = 6

        # Real-time updates
        self.realtime_enabled = False
        self.update_thread: Optional[threading.Thread] = None
        self.running = False

        # Performance tracking
        self.performance_metrics = {
            "total_commands": 0,
            "successful_commands": 0,
            "average_response_time": 0.0,
            "error_count": 0
        }

        self.logger.info("RoboticArmBackend initialized")

    def _setup_logging(self):
        """Setup logging system"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('robotic_arm_backend.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("RoboticArmBackend")

    def connect_serial(self, port: str, baudrate: int = 9600) -> bool:
        """Connect to Arduino with enhanced error handling"""
        try:
            self.serial_port = serial.Serial(port, baudrate, timeout=1)
            time.sleep(2)  # Allow Arduino to initialize

            # Test connection
            if self._test_connection():
                self.is_connected = True
                self.current_port = port
                self.baudrate = baudrate

                # Start real-time update thread
                self.running = True
                self.update_thread = threading.Thread(target=self._realtime_update_loop, daemon=True)
                self.update_thread.start()

                self.logger.info(f"Connected to Arduino on {port}")
                return True
            else:
                self.serial_port.close()
                return False

        except serial.SerialException as e:
            self.logger.error(f"Serial connection failed: {e}")
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
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=1.0)

        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()

        self.is_connected = False
        self.current_port = None
        self.logger.info("Disconnected from Arduino")

    def send_command(self, command: str) -> str:
        """Send command to Arduino with performance tracking"""
        if not self.is_connected or not self.serial_port:
            return "Not connected"

        start_time = time.time()
        try:
            self.serial_port.write(f"{command}\n".encode())
            response = self.serial_port.readline().decode().strip()

            # Update performance metrics
            response_time = time.time() - start_time
            self.performance_metrics["total_commands"] += 1
            self.performance_metrics["successful_commands"] += 1
            self.performance_metrics["average_response_time"] = (
                (self.performance_metrics["average_response_time"] * (self.performance_metrics["successful_commands"] - 1) + response_time)
                / self.performance_metrics["successful_commands"]
            )

            return response

        except Exception as e:
            response_time = time.time() - start_time
            self.performance_metrics["total_commands"] += 1
            self.performance_metrics["error_count"] += 1

            self.logger.error(f"Command error: {e}")
            return f"Error: {e}"

    def send_positions(self, positions: List[float]) -> bool:
        """Send multiple servo positions"""
        if not self.is_connected:
            return False

        try:
            for i, pos in enumerate(positions):
                cmd = f"{i+1} {pos}"
                response = self.send_command(cmd)
                if not response or response.startswith("Error"):
                    return False
            return True
        except Exception as e:
            self.logger.error(f"Position send error: {e}")
            return False

    def read_all_positions(self) -> List[float]:
        """Read all positions from Arduino"""
        if not self.is_connected:
            return []

        try:
            response = self.send_command("readall")
            if response and response.isdigit():
                # Parse response (assuming comma-separated values)
                positions = [float(x) for x in response.split(',') if x.strip()]
                if positions:
                    self.current_positions = positions
                    # Notify callbacks
                    for callback in self.position_callbacks:
                        try:
                            callback(positions)
                        except Exception as e:
                            self.logger.error(f"Position callback error: {e}")
                    return positions
        except Exception as e:
            self.logger.error(f"Read positions error: {e}")

        return []

    def add_position_callback(self, callback: Callable):
        """Add callback for position updates"""
        self.position_callbacks.append(callback)

    def remove_position_callback(self, callback: Callable):
        """Remove position callback"""
        if callback in self.position_callbacks:
            self.position_callbacks.remove(callback)

    def _realtime_update_loop(self):
        """Real-time position update loop"""
        while self.running and self.is_connected:
            try:
                if self.realtime_enabled:
                    self.read_all_positions()
                time.sleep(0.05)  # 50ms updates
            except Exception as e:
                self.logger.error(f"Real-time update error: {e}")
                time.sleep(0.1)

    def get_current_positions(self) -> List[float]:
        """Get current cached positions"""
        return self.current_positions.copy()

    def create_task(self, name: str, description: str = "") -> Optional[TaskSequence]:
        """Create new task"""
        if len(self.tasks) >= self.max_tasks:
            self.logger.warning(f"Maximum tasks ({self.max_tasks}) reached")
            return None

        if name in self.tasks:
            self.logger.warning(f"Task '{name}' already exists")
            return None

        task = TaskSequence(name=name, description=description)
        self.tasks[name] = task
        self.logger.info(f"Created task: {name}")
        return task

    def delete_task(self, name: str) -> bool:
        """Delete task"""
        if name in self.tasks:
            del self.tasks[name]
            self.logger.info(f"Deleted task: {name}")
            return True
        return False

    def get_task_list(self) -> List[str]:
        """Get list of task names"""
        return list(self.tasks.keys())

    def get_task_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get task information"""
        if name not in self.tasks:
            return None

        task = self.tasks[name]
        return {
            "name": task.name,
            "description": task.description,
            "waypoint_count": len(task.waypoints),
            "loop_count": task.loop_count,
            "created_at": task.created_at,
            "modified_at": task.modified_at
        }

    def add_waypoint_to_task(self, task_name: str, positions: List[float],
                           delay_ms: int = 500, trajectory_type: TrajectoryType = TrajectoryType.SMOOTH,
                           motion_profile: MotionProfile = MotionProfile.NORMAL) -> bool:
        """Add waypoint to task"""
        if task_name not in self.tasks:
            return False

        task = self.tasks[task_name]

        # Check waypoint limit
        if len(task.waypoints) >= self.max_waypoints:
            self.logger.warning(f"Maximum waypoints ({self.max_waypoints}) reached for task {task_name}")
            return False

        waypoint = Waypoint(
            positions=positions,
            delay_ms=delay_ms,
            trajectory_type=trajectory_type,
            motion_profile=motion_profile
        )

        task.waypoints.append(waypoint)
        task.modified_at = time.time()

        self.logger.info(f"Added waypoint to task {task_name}")
        return True

    def execute_task(self, task_name: str, loop: bool = False) -> bool:
        """Execute task"""
        if task_name not in self.tasks:
            self.logger.error(f"Task '{task_name}' not found")
            return False

        task = self.tasks[task_name]

        if not task.waypoints:
            self.logger.warning(f"Task '{task_name}' has no waypoints")
            return False

        try:
            # Send motion parameters
            self.send_command(f"speed {self.speed}")
            self.send_command(f"dur {self.duration}")
            self.send_command(f"precision {self.precision}")

            if self.cpg_enabled:
                self.send_command(f"cpgalpha {self.cpg_alpha}")
                self.send_command("cpg on")
            else:
                self.send_command("cpg off")

            # Send trajectory parameters
            self.send_command(f"interp {self.interpolation_method}")
            self.send_command(f"backlash {self.backlash_compensation}")
            self.send_command(f"smooth {self.smoothness_factor}")

            # Execute waypoints
            for waypoint in task.waypoints:
                if not self.is_connected:
                    break

                # Send positions
                if not self.send_positions(waypoint.positions):
                    self.logger.error("Failed to send waypoint positions")
                    return False

                # Wait for motion completion
                motion_time = max(self.duration / 1000.0, 0.5)
                time.sleep(motion_time)

                # Handle delay
                if waypoint.delay_ms > 0:
                    time.sleep(waypoint.delay_ms / 1000.0)

            # Loop if requested
            if loop:
                task.loop_count += 1
                return self.execute_task(task_name, loop)

            self.logger.info(f"Task '{task_name}' executed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Task execution error: {e}")
            return False

    def save_task(self, task_name: str, filename: str) -> bool:
        """Save task to file"""
        if task_name not in self.tasks:
            return False

        try:
            task = self.tasks[task_name]
            data = {
                "name": task.name,
                "description": task.description,
                "waypoints": [
                    {
                        "positions": wp.positions,
                        "delay_ms": wp.delay_ms,
                        "trajectory_type": wp.trajectory_type.value,
                        "motion_profile": wp.motion_profile.value
                    }
                    for wp in task.waypoints
                ],
                "created_at": task.created_at,
                "modified_at": task.modified_at
            }

            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)

            self.logger.info(f"Saved task '{task_name}' to {filename}")
            return True

        except Exception as e:
            self.logger.error(f"Save task error: {e}")
            return False

    def load_task(self, filename: str) -> Optional[str]:
        """Load task from file"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)

            task = TaskSequence(
                name=data["name"],
                description=data.get("description", ""),
                created_at=data.get("created_at", time.time()),
                modified_at=data.get("modified_at", time.time())
            )

            # Load waypoints
            for wp_data in data.get("waypoints", []):
                waypoint = Waypoint(
                    positions=wp_data["positions"],
                    delay_ms=wp_data.get("delay_ms", 500),
                    trajectory_type=TrajectoryType(wp_data.get("trajectory_type", "smooth")),
                    motion_profile=MotionProfile(wp_data.get("motion_profile", "normal"))
                )
                task.waypoints.append(waypoint)

            self.tasks[task.name] = task
            self.logger.info(f"Loaded task '{task.name}' from {filename}")
            return task.name

        except Exception as e:
            self.logger.error(f"Load task error: {e}")
            return None

    def save_all_tasks(self, directory: str) -> bool:
        """Save all tasks to directory"""
        try:
            for task_name in self.tasks:
                filename = os.path.join(directory, f"{task_name}.json")
                self.save_task(task_name, filename)
            return True
        except Exception as e:
            self.logger.error(f"Save all tasks error: {e}")
            return False

    def load_all_tasks(self, directory: str) -> int:
        """Load all tasks from directory"""
        count = 0
        try:
            for filename in os.listdir(directory):
                if filename.endswith('.json'):
                    filepath = os.path.join(directory, filename)
                    if self.load_task(filepath):
                        count += 1
        except Exception as e:
            self.logger.error(f"Load all tasks error: {e}")

        return count

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return self.performance_metrics.copy()

    def cleanup(self):
        """Cleanup resources"""
        self.running = False
        self.disconnect()
        self.logger.info("Backend cleanup completed")

    def __del__(self):
        """Destructor"""
        self.cleanup()