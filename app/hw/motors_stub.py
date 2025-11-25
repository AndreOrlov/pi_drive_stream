from app.config import config
from app.messages import CameraCommand, DriveCommand


async def apply_drive_command(cmd: DriveCommand) -> None:
    # TODO: replace with real PWM/GPIO implementation for motors and steering
    # Temporarily commented out to reduce log noise
    # print(f"[DRIVE] vx={cmd.vx:.2f}, steer={cmd.steer:.2f}, mode={cmd.mode}")
    pass


async def apply_camera_command(cmd: CameraCommand) -> None:
    # TODO: replace with real servo control for camera pan/tilt
    cfg = config.camera

    # Применяем инверсию если нужно
    pan_value = -cmd.pan if cfg.invert_pan else cmd.pan
    tilt_value = -cmd.tilt if cfg.invert_tilt else cmd.tilt

    # Преобразование в углы серво с учетом конфига
    pan_angle = int((pan_value + 1.0) / 2.0 * 180)
    tilt_angle = int((tilt_value + 1.0) / 2.0 * 180)

    if cfg.enable_logging:
        print(f"[CAMERA] pan={cmd.pan:.2f} ({pan_angle}°), tilt={cmd.tilt:.2f} ({tilt_angle}°)")

    # TODO: Реальная реализация с GPIO:
    # import pigpio
    # pi = pigpio.pi()
    # pulse_pan = cfg.servo_min_pulse + (pan_angle / 180) * (cfg.servo_max_pulse - cfg.servo_min_pulse)
    # pulse_tilt = cfg.servo_min_pulse + (tilt_angle / 180) * (cfg.servo_max_pulse - cfg.servo_min_pulse)
    # pi.set_servo_pulsewidth(cfg.pan_gpio_pin, pulse_pan)
    # pi.set_servo_pulsewidth(cfg.tilt_gpio_pin, pulse_tilt)
