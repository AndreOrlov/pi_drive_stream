"""Тесты для конфигурации OSD."""

from app.config import OverlayConfig


def test_overlay_config_defaults() -> None:
    """Проверка дефолтных значений OverlayConfig."""
    config = OverlayConfig()

    assert config.enabled is True
    assert config.backend == "cv"
    assert config.crosshair is True
    assert config.telemetry is True
    assert config.warnings is True


def test_overlay_config_can_be_disabled() -> None:
    """OSD можно отключить."""
    config = OverlayConfig(enabled=False)

    assert config.enabled is False


def test_overlay_config_individual_layers() -> None:
    """Отдельные слои можно отключить."""
    config = OverlayConfig(
        crosshair=False,
        telemetry=True,
        warnings=False,
    )

    assert config.crosshair is False
    assert config.telemetry is True
    assert config.warnings is False


def test_overlay_config_backend() -> None:
    """Backend можно изменить."""
    config = OverlayConfig(backend="picamera")

    assert config.backend == "picamera"


def test_overlay_config_all_disabled() -> None:
    """Все слои можно отключить одновременно."""
    config = OverlayConfig(
        crosshair=False,
        telemetry=False,
        warnings=False,
    )

    assert config.crosshair is False
    assert config.telemetry is False
    assert config.warnings is False


def test_overlay_config_all_enabled() -> None:
    """Все слои можно явно включить."""
    config = OverlayConfig(
        enabled=True,
        crosshair=True,
        telemetry=True,
        warnings=True,
    )

    assert config.enabled is True
    assert config.crosshair is True
    assert config.telemetry is True
    assert config.warnings is True



