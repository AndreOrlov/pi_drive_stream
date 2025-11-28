"""Тесты для конфигурации OSD."""

from app.config import OverlayConfig


def test_overlay_config_defaults() -> None:
    """Проверка дефолтных значений OverlayConfig."""
    config = OverlayConfig()

    assert config.enabled is True
    assert isinstance(config.plugins, dict)
    assert "crosshair" in config.plugins
    assert "telemetry" in config.plugins
    assert "warning" in config.plugins
    assert "motion_detector" in config.plugins
    assert config.plugins["crosshair"]["enabled"] is True
    assert config.plugins["telemetry"]["enabled"] is True
    assert config.plugins["warning"]["enabled"] is True
    assert config.plugins["motion_detector"]["enabled"] is True


def test_overlay_config_can_be_disabled() -> None:
    """OSD можно отключить."""
    config = OverlayConfig(enabled=False)

    assert config.enabled is False


def test_overlay_config_individual_layers() -> None:
    """Отдельные слои можно отключить через plugins."""
    config = OverlayConfig(
        plugins={
            "crosshair": {"enabled": False},
            "telemetry": {"enabled": True},
            "warning": {"enabled": False},
        }
    )

    assert config.plugins["crosshair"]["enabled"] is False
    assert config.plugins["telemetry"]["enabled"] is True
    assert config.plugins["warning"]["enabled"] is False


def test_overlay_config_plugin_parameters() -> None:
    """Можно настраивать параметры плагинов."""
    config = OverlayConfig(
        plugins={
            "crosshair": {
                "enabled": True,
                "size": 30,
                "thickness": 3,
            },
            "motion_detector": {
                "enabled": True,
                "sensitivity": 50,
                "min_area": 1000,
            },
        }
    )

    assert config.plugins["crosshair"]["size"] == 30
    assert config.plugins["crosshair"]["thickness"] == 3
    assert config.plugins["motion_detector"]["enabled"] is True
    assert config.plugins["motion_detector"]["sensitivity"] == 50


def test_overlay_config_all_disabled() -> None:
    """Все слои можно отключить одновременно."""
    config = OverlayConfig(
        plugins={
            "crosshair": {"enabled": False},
            "telemetry": {"enabled": False},
            "warning": {"enabled": False},
        }
    )

    assert config.plugins["crosshair"]["enabled"] is False
    assert config.plugins["telemetry"]["enabled"] is False
    assert config.plugins["warning"]["enabled"] is False


def test_overlay_config_all_enabled() -> None:
    """Все слои можно явно включить."""
    config = OverlayConfig(
        enabled=True,
        plugins={
            "crosshair": {"enabled": True},
            "telemetry": {"enabled": True},
            "warning": {"enabled": True},
            "motion_detector": {"enabled": True},
        },
    )

    assert config.enabled is True
    assert config.plugins["crosshair"]["enabled"] is True
    assert config.plugins["telemetry"]["enabled"] is True
    assert config.plugins["warning"]["enabled"] is True
    assert config.plugins["motion_detector"]["enabled"] is True
