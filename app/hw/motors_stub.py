from app.messages import CameraCommand, DriveCommand


async def apply_drive_command(cmd: DriveCommand) -> None:
    # TODO: replace with real PWM/GPIO implementation for motors and steering
    # Temporarily commented out to reduce log noise
    # print(f"[DRIVE] vx={cmd.vx:.2f}, steer={cmd.steer:.2f}, mode={cmd.mode}")
    pass


async def apply_camera_command(cmd: CameraCommand) -> None:
    # TODO: replace with real servo control for camera pan/tilt
    print(f"[CAMERA] pan={cmd.pan:.2f}, tilt={cmd.tilt:.2f}")
