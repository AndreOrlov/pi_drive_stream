"""Автоматическая загрузка плагинов оверлеев."""

import importlib
import logging
import pkgutil
from pathlib import Path
from typing import Type

from app.overlay.base import Layer
from app.overlay.plugin_registry import list_plugins

logger = logging.getLogger(__name__)


def discover_plugins(package_name: str = "app.overlay.layers") -> dict[str, Type[Layer]]:
    """
    Автоматическое обнаружение и загрузка плагинов из пакета.

    Функция импортирует все модули в указанном пакете, что приводит
    к регистрации плагинов через декоратор @register_layer.

    Args:
        package_name: Имя пакета для сканирования (по умолчанию app.overlay.layers)

    Returns:
        Словарь {имя: класс} всех зарегистрированных плагинов

    Raises:
        ImportError: Если пакет не найден
    """
    try:
        package = importlib.import_module(package_name)
    except ImportError as e:
        logger.error("Failed to import package %s: %s", package_name, e)
        return {}

    if not hasattr(package, "__file__") or package.__file__ is None:
        logger.warning("Package %s has no __file__ attribute", package_name)
        return {}

    package_path = Path(package.__file__).parent

    # Импортируем все модули в пакете (кроме base.py)
    loaded_count = 0
    for _, module_name, _ in pkgutil.iter_modules([str(package_path)]):
        if module_name == "base":
            continue

        try:
            importlib.import_module(f"{package_name}.{module_name}")
            loaded_count += 1
            logger.debug("Loaded plugin module: %s.%s", package_name, module_name)
        except Exception as e:
            logger.error(
                "Failed to load plugin module %s.%s: %s", package_name, module_name, e
            )

    plugins = list_plugins()
    logger.info("Discovered %d plugins from %d modules", len(plugins), loaded_count)

    return plugins
