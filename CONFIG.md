# Конфигурация проекта

Все настройки проекта находятся в файле `app/config.py` и структурированы с помощью Pydantic.

## Структура конфигурации

### ServerConfig - Настройки веб-сервера

```python
host: str = "0.0.0.0"        # Адрес для привязки сервера
port: int = 8000              # Порт сервера
reload: bool = True           # Auto-reload при разработке
```

**Примеры использования:**
- Для production: установите `reload=False`
- Для другого порта: измените `port=8080`
- Для локального доступа: `host="127.0.0.1"`

---

### DriveConfig - Настройки системы управления движением

```python
timeout_s: float = 0.5              # Таймаут команд (watchdog)
watchdog_interval_s: float = 0.1    # Частота проверки watchdog
```

**Безопасность:**
- `timeout_s` - через сколько секунд без команд робот остановится
- `watchdog_interval_s` - как часто проверяется таймаут

---

### VideoConfig - Настройки видеопотока

```python
camera_index: int = 0           # Индекс камеры для OpenCV
use_picamera2: bool = True      # Использовать Picamera2 на Raspberry Pi

width: int = 640                # Ширина видео
height: int = 480               # Высота видео
fps: int = 30                   # Частота кадров

pts_clock_hz: int = 90000       # Частота PTS clock для WebRTC
```

**Оптимизация производительности:**

Для **Raspberry Pi Zero/1/2**:
```python
width: int = 320
height: int = 240
fps: int = 15
```

Для **Raspberry Pi 3/4**:
```python
width: int = 640
height: int = 480
fps: int = 30
```

Для **высокого качества** (Pi 4):
```python
width: int = 1280
height: int = 720
fps: int = 30
```

---

### CameraConfig - Настройки управления камерой

#### Центровка (нейтральное положение)
```python
center_pan: float = 0.0     # -1.0 до 1.0
center_tilt: float = 0.0    # -1.0 до 1.0
```

#### Скорость перемещения
```python
step_size: float = 0.1               # Шаг для дискретного движения
continuous_speed: float = 0.05       # Скорость плавного движения
update_rate: int = 10                # Частота обновления (Hz)
hold_delay_ms: int = 200             # Задержка перед плавным движением
```

**Настройка чувствительности:**
- Увеличьте `step_size` для больших шагов при клике
- Увеличьте `continuous_speed` для более быстрого плавного движения
- Уменьшите `hold_delay_ms` для более быстрой реакции на удержание

#### Лимиты
```python
min_pan: float = -1.0       # Минимум по горизонтали
max_pan: float = 1.0        # Максимум по горизонтали
min_tilt: float = -1.0      # Минимум по вертикали
max_tilt: float = 1.0       # Максимум по вертикали
```

**Ограничение диапазона:**
Если сервоприводы имеют механические ограничения:
```python
min_pan: float = -0.8
max_pan: float = 0.8
min_tilt: float = -0.5
max_tilt: float = 0.5
```

#### Инверсия осей
```python
invert_pan: bool = False    # Инвертировать pan
invert_tilt: bool = False   # Инвертировать tilt
```

**Когда использовать:**
Если сервоприводы установлены в обратном направлении, установите `True`

#### Настройки GPIO (для Raspberry Pi)
```python
pan_gpio_pin: int = 17              # GPIO пин для pan
tilt_gpio_pin: int = 18             # GPIO пин для tilt
servo_min_pulse: int = 1000         # Минимальная длительность импульса (мкс)
servo_max_pulse: int = 2000         # Максимальная длительность импульса (мкс)
```

**Калибровка сервоприводов:**
- Стандартные SG90: 500-2500 мкс
- Большинство серво: 1000-2000 мкс
- Проверьте datasheet вашего сервопривода

#### Логирование
```python
enable_logging: bool = True     # Включить логирование команд
```

Установите `False` для отключения логов в production

---

## Примеры конфигураций

### Конфигурация для разработки на macOS
```python
config = Config(
    server=ServerConfig(
        host="127.0.0.1",
        port=8000,
        reload=True
    ),
    video=VideoConfig(
        camera_index=0,
        use_picamera2=False,
        width=640,
        height=480,
        fps=30
    )
)
```

### Конфигурация для Raspberry Pi Zero
```python
config = Config(
    server=ServerConfig(
        host="0.0.0.0",
        port=8000,
        reload=False
    ),
    video=VideoConfig(
        use_picamera2=True,
        width=320,
        height=240,
        fps=15
    ),
    camera=CameraConfig(
        pan_gpio_pin=17,
        tilt_gpio_pin=18,
        enable_logging=False
    )
)
```

### Конфигурация для Raspberry Pi 4
```python
config = Config(
    video=VideoConfig(
        width=1280,
        height=720,
        fps=30
    ),
    camera=CameraConfig(
        step_size=0.05,
        continuous_speed=0.02,
        update_rate=20
    )
)
```

---

## API для фронтенда

Фронтенд автоматически загружает настройки с сервера через endpoint:

```
GET /api/config
```

Возвращает:
```json
{
  "camera": {
    "step": 0.1,
    "speed": 0.05,
    "update_interval_ms": 100,
    "hold_delay_ms": 200,
    "min_pan": -1.0,
    "max_pan": 1.0,
    "min_tilt": -1.0,
    "max_tilt": 1.0
  },
  "video": {
    "width": 640,
    "height": 480,
    "fps": 30
  }
}
```

Эти настройки автоматически применяются при загрузке страницы.
