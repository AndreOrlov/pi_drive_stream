"""
Drive motor control stub.
TODO: Replace with real PWM/GPIO implementation for DC motors and steering.
"""

from app.messages import DriveCommand


async def apply_drive_command(cmd: DriveCommand) -> None:
    """
    Apply drive motor command (STUB).

    Args:
        cmd: DriveCommand with vx (velocity) and steer values
    """
    # TODO: replace with real PWM/GPIO implementation for motors and steering
    # Temporarily commented out to reduce log noise
    # print(f"[DRIVE] vx={cmd.vx:.2f}, steer={cmd.steer:.2f}, mode={cmd.mode}")
    pass
