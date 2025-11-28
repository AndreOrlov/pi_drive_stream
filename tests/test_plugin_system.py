"""Тесты для системы плагинов оверлеев."""

import numpy as np

from app.overlay.base import Layer
from app.overlay.plugin_loader import discover_plugins
from app.overlay.plugin_registry import get_plugin, list_plugins, register_layer


def test_register_layer_decorator() -> None:
    """Тест регистрации плагина через декоратор."""

    @register_layer("test_plugin")
    class TestLayer(Layer):
        """Тестовый слой."""

        def render(self, frame: np.ndarray) -> None:
            """Заглушка метода render."""
            pass

    # Проверяем, что плагин зарегистрирован
    plugin = get_plugin("test_plugin")
    assert plugin is not None
    assert plugin == TestLayer


def test_get_plugin_returns_none_for_unknown() -> None:
    """Тест что get_plugin возвращает None для неизвестного плагина."""
    plugin = get_plugin("unknown_plugin_xyz")
    assert plugin is None


def test_list_plugins_returns_dict() -> None:
    """Тест что list_plugins возвращает словарь."""
    plugins = list_plugins()
    assert isinstance(plugins, dict)
    assert len(plugins) > 0  # Должны быть зарегистрированы хотя бы существующие плагины


def test_discover_plugins_loads_all_layers() -> None:
    """Тест автоматического обнаружения плагинов."""
    plugins = discover_plugins()

    # Проверяем, что обнаружены стандартные плагины
    assert "crosshair" in plugins
    assert "telemetry" in plugins
    assert "warning" in plugins
    assert "motion_detector" in plugins

    # Проверяем, что все плагины являются подклассами Layer
    for plugin_name, plugin_cls in plugins.items():
        assert issubclass(plugin_cls, Layer), f"{plugin_name} is not a Layer subclass"


def test_plugin_has_priority_attribute() -> None:
    """Тест что плагины имеют атрибут priority после создания."""
    plugins = discover_plugins()

    for _plugin_name, plugin_cls in plugins.items():
        instance = plugin_cls()
        assert hasattr(instance, "priority")
        assert isinstance(instance.priority, int)


def test_discover_plugins_handles_invalid_package() -> None:
    """Тест что discover_plugins корректно обрабатывает несуществующий пакет."""
    plugins = discover_plugins("nonexistent.package.name")
    assert plugins == {}
