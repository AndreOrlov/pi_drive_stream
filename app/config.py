from pydantic import BaseModel, Field


class ServerConfig(BaseModel):
    """Настройки веб-сервера"""

    host: str = Field("0.0.0.0", description="Адрес для привязки сервера")
    port: int = Field(8000, ge=1, le=65535, description="Порт сервера")
    reload: bool = Field(
        True, description="Auto-reload при изменении кода (для разработки)"
    )


class DriveConfig(BaseModel):
    """Настройки системы управления движением"""

    timeout_s: float = Field(
        0.5, gt=0.0, le=5.0, description="Таймаут команд (watchdog)"
    )
    watchdog_interval_s: float = Field(
        0.1, gt=0.0, le=1.0, description="Частота проверки watchdog"
    )


class VideoConfig(BaseModel):
    """Настройки видеопотока"""

    # Источник видео
    camera_index: int = Field(0, ge=0, description="Индекс камеры для OpenCV")
    use_picamera2: bool = Field(
        True, description="Использовать Picamera2 если доступна"
    )

    # Разрешение
    width: int = Field(640, ge=320, le=1920, description="Ширина видео")
    height: int = Field(480, ge=240, le=1080, description="Высота видео")

    # FPS
    fps: int = Field(30, ge=1, le=60, description="Частота кадров")

    # WebRTC
    pts_clock_hz: int = Field(90000, description="Частота PTS clock для WebRTC")

    # Трансформации изображения
    flip_horizontal: bool = Field(
        False, description="Горизонтальное отражение (зеркало)"
    )
    flip_vertical: bool = Field(False, description="Вертикальное отражение (переворот)")


class CameraConfig(BaseModel):
    """Настройки управления камерой (сервоприводы)"""

    # Центровка (нейтральное положение)
    center_pan: float = Field(
        0.0, ge=-1.0, le=1.0, description="Нейтральное положение pan"
    )
    center_tilt: float = Field(
        0.0, ge=-1.0, le=1.0, description="Нейтральное положение tilt"
    )

    # Скорость перемещения
    step_size: float = Field(
        0.1, gt=0.0, le=1.0, description="Шаг для дискретного движения"
    )
    continuous_speed: float = Field(
        0.05, gt=0.0, le=0.5, description="Скорость плавного движения"
    )
    update_rate: int = Field(
        10, ge=1, le=60, description="Частота обновления при плавном движении (Hz)"
    )
    hold_delay_ms: int = Field(
        200, ge=50, le=1000, description="Задержка перед началом плавного движения (мс)"
    )

    # Лимиты
    min_pan: float = Field(
        -1.0, ge=-1.0, le=1.0, description="Минимальное значение pan"
    )
    max_pan: float = Field(
        1.0, ge=-1.0, le=1.0, description="Максимальное значение pan"
    )
    min_tilt: float = Field(
        -1.0, ge=-1.0, le=1.0, description="Минимальное значение tilt"
    )
    max_tilt: float = Field(
        1.0, ge=-1.0, le=1.0, description="Максимальное значение tilt"
    )

    # Инверсия осей
    invert_pan: bool = Field(True, description="Инвертировать направление pan")
    invert_tilt: bool = Field(True, description="Инвертировать направление tilt")

    # Настройки сервоприводов (для будущей реализации)
    pan_gpio_pin: int = Field(7, ge=0, description="GPIO пин для pan сервопривода")
    tilt_gpio_pin: int = Field(6, ge=0, description="GPIO пин для tilt сервопривода")
    servo_min_pulse: int = Field(
        1000, ge=500, le=1500, description="Минимальная длительность импульса (мкс)"
    )
    servo_max_pulse: int = Field(
        2000, ge=1500, le=2500, description="Максимальная длительность импульса (мкс)"
    )

    # Логирование
    enable_logging: bool = Field(
        True, description="Включить логирование команд управления камерой"
    )


class MotorConfig(BaseModel):
    """Настройки управления DC моторами"""

    # Левая сторона (2 мотора)
    left_in1: int = Field(20, description="Левый мотор 1 - направление IN1")
    left_in2: int = Field(21, description="Левый мотор 1 - направление IN2")
    left_pwm1: int = Field(0, description="Левый мотор 1 - скорость PWM")
    left_in3: int = Field(22, description="Левый мотор 2 - направление IN3")
    left_in4: int = Field(23, description="Левый мотор 2 - направление IN4")
    left_pwm2: int = Field(1, description="Левый мотор 2 - скорость PWM")

    # Правая сторона (2 мотора)
    right_in1: int = Field(24, description="Правый мотор 1 - направление IN1")
    right_in2: int = Field(25, description="Правый мотор 1 - направление IN2")
    right_pwm1: int = Field(12, description="Правый мотор 1 - скорость PWM (аппаратный)")
    right_in3: int = Field(26, description="Правый мотор 2 - направление IN3")
    right_in4: int = Field(27, description="Правый мотор 2 - направление IN4")
    right_pwm2: int = Field(13, description="Правый мотор 2 - скорость PWM (аппаратный)")

    # Параметры PWM
    pwm_frequency: int = Field(100, description="Частота PWM (Hz)")
    pwm_range: int = Field(100, description="Диапазон duty cycle (0-100)")

    # Логирование
    enable_logging: bool = Field(True, description="Логировать команды моторов")


class OverlayConfig(BaseModel):
    """Настройки OSD (On-Screen Display)"""

    enabled: bool = Field(True, description="Включить OSD")
    plugins: dict[str, dict] = Field(
        default_factory=lambda: {
            "crosshair": {
                "enabled": True,
                "size": 20,
                "thickness": 2,
            },
            "telemetry": {
                "enabled": True,
                "position": [236, 30],
                "font_scale": 0.7,
            },
            "warning": {
                "enabled": True,
                "warning_text": "LOW BATTERY",
            },
            "motion_detector": {
                "enabled": True,
                "stage": 2,  # 1 = только сетка, 2 = детекция движения
                # Сетка
                "grid_width": 32,
                "grid_height": 24,
                # Детекция (stage 2)
                "algorithm": "grid_rms",  # "grid_mean" | "grid_rms" | "frame_diff"
                "threshold": 95.0,  # Базовый порог (grid_mean: 25.0, RMS: 15.0, frame_diff: 20.0)
                "alpha": 0.02,  # Базовая скорость обновления фона
                "alpha_fast_multiplier": 5.0,  # Множитель для быстрого обновления (нет движения)
                "alpha_slow_multiplier": 0.5,  # Множитель для медленного обновления (есть движение)
                "use_adaptive_threshold": True,  # Адаптивный порог на основе std
                "min_brightness": 10.0,  # Минимальная яркость для детекции
                "max_change_threshold": 200.0,  # Порог резкого изменения освещения
                # Производительность
                "max_detection_fps": 15,  # Максимальный FPS детекции (0 = без ограничений)
                "skip_frames": 0,  # Пропускать N кадров между детекциями
                "enable_profiling": True,  # Включить профилирование производительности
                "show_performance": True,  # Показывать статистику производительности на экране
                # Визуализация движения (stage 2)
                "box_color": [0, 255, 0],  # Зеленый
                "box_thickness": 1,
                "box_fill_alpha": 0,  # Без заливки, только рамки
                # Визуализация сетки (stage 1)
                "show_grid_lines": False,  # Отключить на stage 2
                "grid_line_color": [128, 128, 128],  # Серый
                "grid_line_thickness": 1,
                "grid_line_alpha": 0.3,
                # UI
                "show_cell_info": False,
                "show_stats": True,
            },
        },
        description="Конфигурация плагинов оверлеев",
    )


class Config(BaseModel):
    """Главная конфигурация приложения"""

    server: ServerConfig = Field(default_factory=ServerConfig)
    drive: DriveConfig = Field(default_factory=DriveConfig)
    video: VideoConfig = Field(default_factory=VideoConfig)
    camera: CameraConfig = Field(default_factory=CameraConfig)
    motor: MotorConfig = Field(default_factory=MotorConfig)
    overlay: OverlayConfig = Field(default_factory=OverlayConfig)


# Глобальный экземпляр конфигурации
config = Config()
