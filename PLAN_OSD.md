# План реализации OSD системы

## Цель
Добавить систему наложения графики (OSD) на видеопоток с модульной архитектурой, позволяющей легко добавлять новые элементы и менять backend отрисовки.

## Архитектура

### Структура модулей
```
app/overlay/
├── __init__.py
├── base.py              # Protocol OverlayRenderer + ABC Layer
├── cv_renderer.py       # CvOverlayRenderer (OpenCV backend)
└── layers/
    ├── __init__.py
    ├── base.py          # ABC Layer
    ├── crosshair.py     # CrosshairLayer (прицел)
    ├── telemetry.py     # TelemetryLayer (дата/время)
    └── warning.py       # WarningLayer (предупреждения, mock)
```

### Слои для первой версии
1. **CrosshairLayer** — простой прицел (перекрестие в центре)
2. **TelemetryLayer** — дата и время в формате "01.09.2025 08:57:45"
3. **WarningLayer** — предупреждения (замокированные, например "LOW BATTERY")

## Реализация

### 1. Базовые интерфейсы (`app/overlay/base.py`)

**Protocol для рендерера:**
```python
class OverlayRenderer(Protocol):
    """Интерфейс рендерера OSD."""
    def draw(self, frame: np.ndarray) -> None:
        """Отрисовать все слои на кадре."""
        ...
```

**ABC для слоя:**
```python
class Layer(ABC):
    """Базовый класс для слоя OSD."""
    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    @abstractmethod
    def render(self, frame: np.ndarray) -> None:
        """Отрисовать слой на кадре."""
        ...
```

### 2. Реализация слоёв

**`app/overlay/layers/crosshair.py`:**
- Рисует перекрестие в центре кадра
- Использует `cv2.line()` для линий
- Цвет: белый с чёрной обводкой для контраста
- Центральная точка для точного прицеливания

**`app/overlay/layers/telemetry.py`:**
- Выводит текущую дату и время в формате "01.09.2025 08:57:45"
- Использует `datetime.now().strftime("%d.%m.%Y %H:%M:%S")`
- Позиция: левый верхний угол (10, 30)
- Использует `cv2.putText()` с `FONT_HERSHEY_SIMPLEX`

**`app/overlay/layers/warning.py`:**
- Выводит замокированное предупреждение "LOW BATTERY"
- Позиция: центр верхней части экрана (x=center, y=40)
- Цвет: красный с чёрной обводкой
- В будущем можно передавать список предупреждений через параметры

### 3. OpenCV рендерер (`app/overlay/cv_renderer.py`)

```python
class CvOverlayRenderer:
    """Рендерер OSD на основе OpenCV."""
    def __init__(self, layers: list[Layer]):
        self.layers = layers

    def draw(self, frame: np.ndarray) -> None:
        """Отрисовать все активные слои."""
        for layer in self.layers:
            if layer.enabled:
                layer.render(frame)
```

### 4. Конфигурация (`app/config.py`)

```python
class OverlayConfig(BaseModel):
    """Настройки OSD."""
    enabled: bool = Field(True, description="Включить OSD")
    backend: str = Field("cv", description="Backend отрисовки (cv, picamera, gst)")
    crosshair: bool = Field(True, description="Показывать прицел")
    telemetry: bool = Field(True, description="Показывать телеметрию")
    warnings: bool = Field(True, description="Показывать предупреждения")
```

Добавлено в `Config`:
```python
overlay: OverlayConfig = OverlayConfig()
```

### 5. Интеграция в видеопоток (`app/video.py`)

**В `CameraVideoTrack.__init__()`:**
```python
# Инициализация OSD рендерера
self._overlay_renderer: Optional[CvOverlayRenderer] = None
if config.overlay.enabled:
    layers = []
    if config.overlay.crosshair:
        layers.append(CrosshairLayer())
    if config.overlay.telemetry:
        layers.append(TelemetryLayer())
    if config.overlay.warnings:
        layers.append(WarningLayer())

    if layers:
        self._overlay_renderer = CvOverlayRenderer(layers)
        logger.info("OSD renderer initialized with %d layers", len(layers))
```

**В `CameraVideoTrack.recv()` после блока трансформаций:**
```python
# Отрисовка OSD
if self._overlay_renderer is not None:
    self._overlay_renderer.draw(frame)
```

## Особенности реализации

- Все слои работают на RGB-кадрах (формат уже готов в `video.py`)
- Координаты и размеры фиксированные для первой версии
- Цвета в формате RGB (не BGR, так как кадр уже конвертирован)
- Для контрастности текст рисуется дважды: сначала чёрная обводка (толще), потом основной цвет
- Рендерер создаётся один раз в `__init__`, не пересоздаётся каждый кадр
- Работает одинаково для Picamera2 и OpenCV

## Варианты backend'ов (будущее расширение)

### 1. CPU/OpenCV (текущая реализация)
```
CameraVideoTrack.recv()
    ├─ numpy frame (Picamera2 или cv2.VideoCapture)
    ├─ CvOverlayRenderer.draw(frame)
    └─ VideoFrame.from_ndarray(frame)
```

### 2. Picamera2 аппаратный overlay (Raspberry Pi)
```
Picamera2 pipeline → GPU plane
    ├─ OverlayRenderer = Picamera2DRMOverlay
    │     • создаёт ARGB слой
    │     • обновляет буфер (через Pillow/NumPy)
    └─ CameraVideoTrack выдаёт чистый кадр,
        а overlay рендерится аппаратно поверх
```

### 3. GStreamer backend
```
libcamera-vid/v4l2src → ... → [textoverlay/cairooverlay] → webrtcbin
                                 ↑
                                 └─ GstOverlayRenderer (Python)
                                     • через GObject Introspection
                                     • обновляет свойства overlay-элемента
```

### 4. FFmpeg backend
```
ffmpeg -i camera -vf "drawtext=..., drawbox=..., overlay=..." → webrtc/http stream
          ↑
          └─ FfmpegOverlayRenderer
                • перезапускает процесс с нужными фильтрами
                • либо подкидывает surface через zmq/shmem
```

## Будущие улучшения

### Базовые
- [x] Включение/отключение слоёв через конфиг
- [ ] Обработка ошибок в слоях (try/except в рендерере)
- [ ] Порядок отрисовки (z-index)
- [ ] Типизированная структура данных вместо dict

### Производительность
- [ ] Метрики производительности (время отрисовки каждого слоя)
- [ ] Кэширование статических элементов (прицел)
- [ ] Поддержка альфа-канала (прозрачность)
- [ ] Адаптация под разные разрешения (scale_factor)

### Функциональность
- [ ] Динамические данные телеметрии (скорость, углы серв, батарея)
- [ ] Реальные предупреждения вместо mock
- [ ] Горячая перезагрузка конфигурации
- [ ] Композитные слои (несколько элементов в одном слое)
- [ ] Декларативный UI (YAML/JSON конфиг для элементов)

### Backend'ы
- [ ] PicameraOverlayRenderer (DRM planes)
- [ ] GstOverlayRenderer (GStreamer фильтры)
- [ ] FfmpegOverlayRenderer (FFmpeg фильтры)
- [ ] Клиентский overlay (WebGL/Canvas в браузере)

## Использование

### По умолчанию
OSD включён со всеми слоями. Для настройки измените `app/config.py`:

```python
overlay=OverlayConfig(
    enabled=True,      # Включить OSD
    crosshair=True,    # Показывать прицел
    telemetry=True,    # Показывать дату/время
    warnings=False,    # Скрыть предупреждения
)
```

### Добавление нового слоя

1. Создать класс в `app/overlay/layers/new_layer.py`:
```python
from app.overlay.layers.base import Layer

class NewLayer(Layer):
    def render(self, frame: np.ndarray) -> None:
        # Ваша логика отрисовки
        pass
```

2. Добавить в `app/overlay/layers/__init__.py`:
```python
from app.overlay.layers.new_layer import NewLayer
__all__ = [..., "NewLayer"]
```

3. Добавить параметр в `OverlayConfig` (`app/config.py`):
```python
new_layer: bool = Field(True, description="Показывать новый слой")
```

4. Добавить в инициализацию рендерера (`app/video.py`):
```python
if config.overlay.new_layer:
    layers.append(NewLayer())
```

## Тестирование

### Локально (десктоп)
```bash
cd /Users/andreyorlov/projects/pi_drive_stream
source .venv/bin/activate
python main.py
```

Откройте `http://localhost:8000` — OSD должен быть виден на видеопотоке.

### На Raspberry Pi
```bash
cd ~/projects/pi_drive_stream
./start.sh
```

Откройте `http://<raspberry-pi-ip>:8000` — OSD должен работать с Picamera2.

## Статус реализации

- [x] Базовые интерфейсы (Protocol, ABC)
- [x] Три слоя (Crosshair, Telemetry, Warning)
- [x] OpenCV рендерер
- [x] Конфигурация
- [x] Интеграция в видеопоток
- [x] Тестирование на десктопе ✅
- [x] Тестирование на Raspberry Pi ✅
- [ ] Аппаратные backend'ы
- [ ] Динамические данные
