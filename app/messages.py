from dataclasses import dataclass
from enum import Enum


class DriveMode(str, Enum):
    MANUAL = "manual"
    EMERGENCY_STOP = "emergency_stop"


@dataclass
class DriveCommand:
    vx: float  # linear velocity, normalized -1..1 or m/s
    steer: float  # steering, -1..1 (left/right)
    mode: DriveMode = DriveMode.MANUAL


@dataclass
class CameraCommand:
    pan: float  # -1..1
    tilt: float  # -1..1


@dataclass
class RobotState:
    vx: float
    steer: float
    battery_voltage: float | None = None


