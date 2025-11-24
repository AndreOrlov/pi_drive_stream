from pydantic import BaseModel, Field


class CameraConfig(BaseModel):
    # Центровка (нейтральное положение)
    center_pan: float = Field(0.0, ge=-1.0, le=1.0)
    center_tilt: float = Field(0.0, ge=-1.0, le=1.0)

    # Скорость перемещения
    step_size: float = Field(0.1, gt=0.0, le=1.0)  # шаг для дискретного движения
    continuous_speed: float = Field(0.05, gt=0.0, le=0.5)  # скорость для плавного движения

    # Частота обновления при плавном движении (Hz)
    update_rate: int = Field(10, ge=1, le=60)

    # Лимиты
    min_pan: float = Field(-1.0, ge=-1.0, le=1.0)
    max_pan: float = Field(1.0, ge=-1.0, le=1.0)
    min_tilt: float = Field(-1.0, ge=-1.0, le=1.0)
    max_tilt: float = Field(1.0, ge=-1.0, le=1.0)

    # Настройки сервоприводов (для будущей реализации)
    pan_gpio_pin: int = Field(17, ge=0)
    tilt_gpio_pin: int = Field(18, ge=0)
    servo_min_pulse: int = Field(1000, ge=500, le=1500)
    servo_max_pulse: int = Field(2000, ge=1500, le=2500)

    # Логирование
    enable_logging: bool = Field(True, description="Включить логирование команд управления камерой")


class Config(BaseModel):
    camera: CameraConfig = CameraConfig()


# Глобальный экземпляр конфигурации
config = Config()
