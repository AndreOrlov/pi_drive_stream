"""Registry для плагинов оверлеев."""

from typing import Type

from app.overlay.base import Layer

_PLUGINS: dict[str, Type[Layer]] = {}


def register_layer(name: str):
    """
    Декоратор для регистрации слоя-плагина.

    Args:
        name: Уникальное имя плагина

    Returns:
        Декоратор класса

    Example:
        @register_layer("my_plugin")
        class MyPluginLayer(Layer):
            def render(self, frame):
                pass
    """

    def decorator(cls: Type[Layer]) -> Type[Layer]:
        """Внутренний декоратор для регистрации класса."""
        _PLUGINS[name] = cls
        return cls

    return decorator


def get_plugin(name: str) -> Type[Layer] | None:
    """
    Получить класс плагина по имени.

    Args:
        name: Имя плагина

    Returns:
        Класс плагина или None, если не найден
    """
    return _PLUGINS.get(name)


def list_plugins() -> dict[str, Type[Layer]]:
    """
    Получить словарь всех зарегистрированных плагинов.

    Returns:
        Словарь {имя: класс} всех плагинов
    """
    return _PLUGINS.copy()
