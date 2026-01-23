"""
DC motor control via pigpio.
Manages 4 DC motors in tank drive configuration.
"""

import logging
from app.config import config
from app.messages import DriveCommand

logger = logging.getLogger(__name__)

try:
    import pigpio  # type: ignore[import-not-found]

    PIGPIO_AVAILABLE = True
except ImportError:
    pigpio = None  # type: ignore[assignment]
    PIGPIO_AVAILABLE = False

_pi: object | None = None


def _get_pi():
    """Ленивая инициализация pigpio"""
    global _pi
    if not PIGPIO_AVAILABLE or pigpio is None:
        raise RuntimeError("pigpio is not available on this platform")
    if _pi is None:
        _pi = pigpio.pi()
        if not _pi.connected:
            raise RuntimeError(
                "Cannot connect to pigpiod. Is it running? (sudo systemctl start pigpiod)"
            )
        _initialize_motors()
    return _pi


def _initialize_motors() -> None:
    """Инициализация GPIO пинов для моторов"""
    if not PIGPIO_AVAILABLE or _pi is None:
        return

    cfg = config.motor

    # Настройка пинов направления (цифровые выходы)
    for pin in [
        cfg.left_in1,
        cfg.left_in2,
        cfg.left_in3,
        cfg.left_in4,
        cfg.right_in1,
        cfg.right_in2,
        cfg.right_in3,
        cfg.right_in4,
    ]:
        _pi.set_mode(pin, pigpio.OUTPUT)
        _pi.write(pin, 0)

    # Настройка PWM пинов
    for pin in [cfg.left_pwm1, cfg.left_pwm2, cfg.right_pwm1, cfg.right_pwm2]:
        _pi.set_PWM_frequency(pin, cfg.pwm_frequency)
        _pi.set_PWM_range(pin, cfg.pwm_range)
        _pi.set_PWM_dutycycle(pin, 0)

    logger.info("Motors initialized successfully")


def _calculate_motor_powers(vx: float, steer: float) -> tuple[float, float]:
    """
    Преобразование (vx, steer) в мощность левой/правой стороны.

    Args:
        vx: Скорость вперед/назад [-1..1]
        steer: Поворот влево/вправо [-1..1]

    Returns:
        (left_power, right_power) в диапазоне [-1..1]
    """
    left_power = vx - steer
    right_power = vx + steer

    # Нормализация (если вышли за пределы [-1, 1])
    max_abs = max(abs(left_power), abs(right_power))
    if max_abs > 1.0:
        left_power /= max_abs
        right_power /= max_abs

    return left_power, right_power


def _set_motor_side(
    in1: int,
    in2: int,
    pwm1: int,
    in3: int,
    in4: int,
    pwm2: int,
    power: float,
    invert: bool = False,
) -> None:
    """
    Установить скорость и направление для одной стороны (2 мотора).

    Args:
        in1, in2, pwm1: Пины первого мотора
        in3, in4, pwm2: Пины второго мотора
        power: Мощность [0..1] и направление (>0 вперед, <0 назад, =0 стоп)
        invert: Инвертировать направление вращения (меняет полярность IN пинов)
    """
    if not PIGPIO_AVAILABLE or _pi is None:
        return

    cfg = config.motor
    duty_cycle = int(abs(power) * cfg.pwm_range)

    if power > 0:
        # Вперед (ЭТАП 2: только это направление активно)
        if invert:
            # Инвертированное направление (меняем IN пины местами)
            _pi.write(in1, 1)
            _pi.write(in2, 0)
            _pi.write(in3, 0)
            _pi.write(in4, 1)
        else:
            # Нормальное направление
            _pi.write(in1, 0)
            _pi.write(in2, 1)
            _pi.write(in3, 1)
            _pi.write(in4, 0)
    elif power < 0:
        # Назад (ЭТАП 3: пока заблокировано)
        _pi.write(in1, 0)
        _pi.write(in2, 0)
        _pi.write(in3, 0)
        _pi.write(in4, 0)
        duty_cycle = 0
    else:
        # Стоп
        _pi.write(in1, 0)
        _pi.write(in2, 0)
        _pi.write(in3, 0)
        _pi.write(in4, 0)

    _pi.set_PWM_dutycycle(pwm1, duty_cycle)
    _pi.set_PWM_dutycycle(pwm2, duty_cycle)


async def apply_drive_command(cmd: DriveCommand) -> None:
    """
    Применить команду управления движением.

    Args:
        cmd: DriveCommand с vx (скорость) и steer (поворот)
    """
    if not PIGPIO_AVAILABLE:
        return

    try:
        pi = _get_pi()
        cfg = config.motor

        # Преобразование команды в мощность сторон
        left_power, right_power = _calculate_motor_powers(cmd.vx, cmd.steer)

        # ЭТАП 2: Разрешаем только движение вперед (vx > 0, steer == 0)
        if cmd.vx > 0 and cmd.steer == 0:
            # Применение к левой стороне
            _set_motor_side(
                cfg.left_in1,
                cfg.left_in2,
                cfg.left_pwm1,
                cfg.left_in3,
                cfg.left_in4,
                cfg.left_pwm2,
                left_power,
                cfg.invert_left,
            )

            # Применение к правой стороне
            _set_motor_side(
                cfg.right_in1,
                cfg.right_in2,
                cfg.right_pwm1,
                cfg.right_in3,
                cfg.right_in4,
                cfg.right_pwm2,
                right_power,
                cfg.invert_right,
            )

            if cfg.enable_logging:
                print(
                    f"[MOTOR] vx={cmd.vx:.2f}, steer={cmd.steer:.2f} -> L={left_power:.2f}, R={right_power:.2f}"
                )
        else:
            # Стоп (любые другие команды на этапе 2)
            _set_motor_side(
                cfg.left_in1,
                cfg.left_in2,
                cfg.left_pwm1,
                cfg.left_in3,
                cfg.left_in4,
                cfg.left_pwm2,
                0.0,
                cfg.invert_left,
            )
            _set_motor_side(
                cfg.right_in1,
                cfg.right_in2,
                cfg.right_pwm1,
                cfg.right_in3,
                cfg.right_in4,
                cfg.right_pwm2,
                0.0,
                cfg.invert_right,
            )

    except RuntimeError as e:
        logger.error("Failed to control motors: %s", e)
    except Exception as e:
        logger.error("Unexpected error in motor control: %s", e)


def cleanup_motors() -> None:
    """Освобождение ресурсов при выключении"""
    global _pi
    if not PIGPIO_AVAILABLE or _pi is None:
        return

    cfg = config.motor

    # Остановка всех моторов
    for pin in [cfg.left_pwm1, cfg.left_pwm2, cfg.right_pwm1, cfg.right_pwm2]:
        _pi.set_PWM_dutycycle(pin, 0)

    # Сброс направлений
    for pin in [
        cfg.left_in1,
        cfg.left_in2,
        cfg.left_in3,
        cfg.left_in4,
        cfg.right_in1,
        cfg.right_in2,
        cfg.right_in3,
        cfg.right_in4,
    ]:
        _pi.write(pin, 0)

    _pi.stop()
    _pi = None
    logger.info("Motors cleaned up")
