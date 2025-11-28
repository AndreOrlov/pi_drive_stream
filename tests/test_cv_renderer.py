"""Тесты для OpenCV рендерера."""

import numpy as np

from app.overlay import CvOverlayRenderer
from app.overlay.layers import CrosshairLayer, TelemetryLayer


def test_renderer_calls_all_enabled_layers() -> None:
    """Рендерер вызывает все включенные слои."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    layers = [
        CrosshairLayer(enabled=True),
        TelemetryLayer(enabled=True),
    ]

    renderer = CvOverlayRenderer(layers)
    renderer.draw(frame)

    assert frame.sum() > 0, "Рендерер должен вызвать слои"


def test_renderer_skips_disabled_layers() -> None:
    """Рендерер пропускает отключенные слои."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Только отключенные слои
    layers = [
        CrosshairLayer(enabled=False),
        TelemetryLayer(enabled=False),
    ]

    renderer = CvOverlayRenderer(layers)
    renderer.draw(frame)

    assert frame.sum() == 0, "Отключенные слои не должны менять кадр"


def test_renderer_respects_layer_order() -> None:
    """Рендерер вызывает слои в правильном порядке."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    call_order: list[str] = []

    class TrackedLayer(CrosshairLayer):
        """Слой, который отслеживает порядок вызовов."""

        def __init__(self, name: str) -> None:
            super().__init__()
            self.name = name

        def render(self, frame: np.ndarray) -> None:
            call_order.append(self.name)
            super().render(frame)

    layers = [
        TrackedLayer("first"),
        TrackedLayer("second"),
        TrackedLayer("third"),
    ]

    renderer = CvOverlayRenderer(layers)
    renderer.draw(frame)

    assert call_order == ["first", "second", "third"], "Порядок вызова должен совпадать"


def test_renderer_with_empty_layers() -> None:
    """Рендерер работает с пустым списком слоёв."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    renderer = CvOverlayRenderer([])
    renderer.draw(frame)

    assert frame.sum() == 0, "Пустой рендерер не должен менять кадр"


def test_renderer_with_mixed_enabled_disabled() -> None:
    """Рендерер корректно обрабатывает смесь включенных и отключенных слоёв."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    layers = [
        CrosshairLayer(enabled=True),
        TelemetryLayer(enabled=False),
        CrosshairLayer(enabled=True),
    ]

    renderer = CvOverlayRenderer(layers)
    renderer.draw(frame)

    # Должны отработать только два прицела
    assert frame.sum() > 0, "Включенные слои должны отработать"


def test_renderer_does_not_modify_layers_list() -> None:
    """Рендерер не модифицирует список слоёв."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    layers = [
        CrosshairLayer(),
        TelemetryLayer(),
    ]
    original_length = len(layers)

    renderer = CvOverlayRenderer(layers)
    renderer.draw(frame)

    assert len(layers) == original_length, "Список слоёв не должен изменяться"


def test_renderer_sorts_layers_by_priority() -> None:
    """Рендерер сортирует слои по приоритету."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    call_order: list[int] = []

    class PriorityTrackedLayer(CrosshairLayer):
        """Слой, который отслеживает порядок вызовов по приоритету."""

        def __init__(self, priority: int) -> None:
            super().__init__(enabled=True)
            self.priority = priority

        def render(self, frame: np.ndarray) -> None:
            call_order.append(self.priority)

    # Создаём слои в случайном порядке приоритетов
    layers = [
        PriorityTrackedLayer(100),  # Должен быть вторым
        PriorityTrackedLayer(0),    # Должен быть первым
        PriorityTrackedLayer(200),  # Должен быть третьим
    ]

    renderer = CvOverlayRenderer(layers)
    renderer.draw(frame)

    # Проверяем, что слои вызваны в порядке возрастания приоритета
    assert call_order == [0, 100, 200], "Слои должны вызываться в порядке приоритета"
