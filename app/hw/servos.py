"""
Camera servo control via pigpio.
Manages pan/tilt servos for camera positioning.
"""

from app.config import config
from app.messages import CameraCommand
from typing import Optional, TYPE_CHECKING

try:
    import pigpio  # type: ignore[import-not-found]
    PIGPIO_AVAILABLE = True
except ImportError:
    pigpio = None  # type: ignore[assignment]
    PIGPIO_AVAILABLE = False

if TYPE_CHECKING:
    _pi: Optional[pigpio.pi] = None
else:
    _pi: Optional[object] = None


def _get_pi():
    """Ленивая инициализация pigpio"""
    global _pi
    if not PIGPIO_AVAILABLE or pigpio is None:
        raise RuntimeError("pigpio is not available on this platform")
    if _pi is None:
        _pi = pigpio.pi()
        if not _pi.connected:
            raise RuntimeError("Cannot connect to pigpiod. Is it running? (sudo systemctl start pigpiod)")
    return _pi


async def apply_camera_command(cmd: CameraCommand) -> None:
    """
    Apply camera servo command.

    Args:
        cmd: CameraCommand with pan/tilt values (-1.0 to 1.0)
    """
    if not PIGPIO_AVAILABLE:
        # На macOS просто игнорируем команды сервоприводов
        return

    cfg = config.camera
    pi = _get_pi()  # Получаем экземпляр pigpio

    # Применяем инверсию если нужно
    pan_value = -cmd.pan if cfg.invert_pan else cmd.pan
    tilt_value = -cmd.tilt if cfg.invert_tilt else cmd.tilt

    # Преобразование в углы серво с учетом конфига
    pan_angle = int((pan_value + 1.0) / 2.0 * 180)
    tilt_angle = int((tilt_value + 1.0) / 2.0 * 180)

    # Преобразование в PWM импульсы (мкс)
    pan_pulse = cfg.servo_min_pulse + (pan_angle / 180.0) * (cfg.servo_max_pulse - cfg.servo_min_pulse)
    tilt_pulse = cfg.servo_min_pulse + (tilt_angle / 180.0) * (cfg.servo_max_pulse - cfg.servo_min_pulse)

    # Отправка команд на сервоприводы
    pi.set_servo_pulsewidth(cfg.pan_gpio_pin, pan_pulse)
    pi.set_servo_pulsewidth(cfg.tilt_gpio_pin, tilt_pulse)

    if cfg.enable_logging:
        print(f"[CAMERA] pan={cmd.pan:.2f} ({pan_angle}°, {pan_pulse:.0f}μs), tilt={cmd.tilt:.2f} ({tilt_angle}°, {tilt_pulse:.0f}μs)")


def cleanup_servo():
    """Освобождение ресурсов при выключении"""
    global _pi
    if not PIGPIO_AVAILABLE:
        return
    if _pi is not None:
        cfg = config.camera
        # Отключаем PWM (серво перестанут держать позицию)
        _pi.set_servo_pulsewidth(cfg.pan_gpio_pin, 0)
        _pi.set_servo_pulsewidth(cfg.tilt_gpio_pin, 0)
        _pi.stop()
        _pi = None
