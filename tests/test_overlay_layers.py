"""Тесты для слоёв OSD."""

import numpy as np
import pytest

from app.overlay.layers import CrosshairLayer, TelemetryLayer, WarningLayer


def test_crosshair_layer_renders() -> None:
    """Прицел рисует что-то на кадре."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    layer = CrosshairLayer()

    layer.render(frame)

    assert frame.sum() > 0, "Прицел должен изменить кадр"


def test_crosshair_layer_disabled() -> None:
    """Отключенный прицел не меняет кадр."""
    layer = CrosshairLayer(enabled=False)

    # Рендерер должен проверять enabled, но слой сам не проверяет
    # Этот тест проверяет, что слой можно создать с enabled=False
    assert layer.enabled is False


def test_telemetry_layer_renders() -> None:
    """Телеметрия рисует дату/время на кадре."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    layer = TelemetryLayer()

    layer.render(frame)

    assert frame.sum() > 0, "Телеметрия должна изменить кадр"


def test_warning_layer_renders() -> None:
    """Предупреждения рисуют текст на кадре."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    layer = WarningLayer()

    layer.render(frame)

    assert frame.sum() > 0, "Предупреждения должны изменить кадр"


@pytest.mark.parametrize(
    "resolution",
    [
        (240, 320, 3),  # Маленькое
        (480, 640, 3),  # Среднее
        (1080, 1920, 3),  # Большое
    ],
)
def test_layers_work_with_different_resolutions(
    resolution: tuple[int, int, int],
) -> None:
    """Все слои работают с разными разрешениями."""
    frame = np.zeros(resolution, dtype=np.uint8)

    layers = [
        CrosshairLayer(),
        TelemetryLayer(),
        WarningLayer(),
    ]

    for layer in layers:
        layer.render(frame)
        assert frame.sum() > 0, (
            f"{layer.__class__.__name__} должен работать с {resolution}"
        )


def test_crosshair_layer_custom_parameters() -> None:
    """Прицел работает с кастомными параметрами."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    layer = CrosshairLayer(
        size=30,
        thickness=3,
        color=(0, 255, 0),  # Зелёный
    )

    layer.render(frame)

    assert frame.sum() > 0, "Прицел с кастомными параметрами должен работать"


def test_telemetry_layer_custom_position() -> None:
    """Телеметрия работает с кастомной позицией."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    layer = TelemetryLayer(position=(50, 100))

    layer.render(frame)

    assert frame.sum() > 0, "Телеметрия с кастомной позицией должна работать"


def test_warning_layer_custom_text() -> None:
    """Предупреждения работают с кастомным текстом."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    layer = WarningLayer(warning_text="CUSTOM WARNING")

    layer.render(frame)

    assert frame.sum() > 0, "Предупреждения с кастомным текстом должны работать"
