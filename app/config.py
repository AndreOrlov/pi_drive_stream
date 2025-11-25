from pydantic import BaseModel, Field


class ServerConfig(BaseModel):
    """Настройки веб-сервера"""
    host: str = Field("0.0.0.0", description="Адрес для привязки сервера")
    port: int = Field(8000, ge=1, le=65535, description="Порт сервера")
    reload: bool = Field(False, description="Auto-reload при изменении кода (для разработки)")


class DriveConfig(BaseModel):
    """Настройки системы управления движением"""
    timeout_s: float = Field(0.5, gt=0.0, le=5.0, description="Таймаут команд (watchdog)")
    watchdog_interval_s: float = Field(0.1, gt=0.0, le=1.0, description="Частота проверки watchdog")


class VideoConfig(BaseModel):
    """Настройки видеопотока"""
    # Источник видео
    camera_index: int = Field(0, ge=0, description="Индекс камеры для OpenCV")
    use_picamera2: bool = Field(True, description="Использовать Picamera2 если доступна")

    # Разрешение
    width: int = Field(640, ge=320, le=1920, description="Ширина видео")
    height: int = Field(480, ge=240, le=1080, description="Высота видео")

    # FPS
    fps: int = Field(30, ge=1, le=60, description="Частота кадров")

    # WebRTC
    pts_clock_hz: int = Field(90000, description="Частота PTS clock для WebRTC")

    # Трансформации изображения
    flip_horizontal: bool = Field(False, description="Горизонтальное отражение (зеркало)")
    flip_vertical: bool = Field(True, description="Вертикальное отражение (переворот)")


class CameraConfig(BaseModel):
    """Настройки управления камерой (сервоприводы)"""
    # Центровка (нейтральное положение)
    center_pan: float = Field(0.0, ge=-1.0, le=1.0, description="Нейтральное положение pan")
    center_tilt: float = Field(0.0, ge=-1.0, le=1.0, description="Нейтральное положение tilt")

    # Скорость перемещения
    step_size: float = Field(0.1, gt=0.0, le=1.0, description="Шаг для дискретного движения")
    continuous_speed: float = Field(0.05, gt=0.0, le=0.5, description="Скорость плавного движения")
    update_rate: int = Field(10, ge=1, le=60, description="Частота обновления при плавном движении (Hz)")
    hold_delay_ms: int = Field(200, ge=50, le=1000, description="Задержка перед началом плавного движения (мс)")

    # Лимиты
    min_pan: float = Field(-1.0, ge=-1.0, le=1.0, description="Минимальное значение pan")
    max_pan: float = Field(1.0, ge=-1.0, le=1.0, description="Максимальное значение pan")
    min_tilt: float = Field(-1.0, ge=-1.0, le=1.0, description="Минимальное значение tilt")
    max_tilt: float = Field(1.0, ge=-1.0, le=1.0, description="Максимальное значение tilt")

    # Инверсия осей
    invert_pan: bool = Field(False, description="Инвертировать направление pan")
    invert_tilt: bool = Field(False, description="Инвертировать направление tilt")

    # Настройки сервоприводов (для будущей реализации)
    pan_gpio_pin: int = Field(17, ge=0, description="GPIO пин для pan сервопривода")
    tilt_gpio_pin: int = Field(18, ge=0, description="GPIO пин для tilt сервопривода")
    servo_min_pulse: int = Field(1000, ge=500, le=1500, description="Минимальная длительность импульса (мкс)")
    servo_max_pulse: int = Field(2000, ge=1500, le=2500, description="Максимальная длительность импульса (мкс)")

    # Логирование
    enable_logging: bool = Field(True, description="Включить логирование команд управления камерой")


class Config(BaseModel):
    """Главная конфигурация приложения"""
    server: ServerConfig = ServerConfig()
    drive: DriveConfig = DriveConfig()
    video: VideoConfig = VideoConfig()
    camera: CameraConfig = CameraConfig()


# Глобальный экземпляр конфигурации
config = Config()
