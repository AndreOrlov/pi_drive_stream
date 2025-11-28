"""Базовые интерфейсы для OSD системы."""

from abc import ABC, abstractmethod
from typing import Protocol

import numpy as np


class OverlayRenderer(Protocol):
    """
    Интерфейс рендерера OSD.

    Рендерер управляет отрисовкой всех слоёв на кадре.
    """

    def draw(self, frame: np.ndarray) -> None:
        """
        Отрисовать все слои на кадре.

        Args:
            frame: Кадр в формате RGB (numpy array)
        """
        ...


class Layer(ABC):
    """
    Базовый класс для слоя OSD.

    Каждый слой отвечает за отрисовку одного элемента интерфейса
    (прицел, телеметрия, предупреждения и т.д.).

    Атрибуты приоритета определяют порядок отрисовки слоев:
    - PRIORITY_BACKGROUND (0): Фоновые элементы, детекторы
    - PRIORITY_NORMAL (50): Обычные графические элементы
    - PRIORITY_FOREGROUND (100): Передний план, прицелы
    - PRIORITY_HUD (200): UI элементы, текстовая информация

    Слои с меньшим приоритетом рисуются раньше (снизу),
    с большим - позже (сверху).
    """

    # Константы приоритетов
    PRIORITY_BACKGROUND = 0
    PRIORITY_NORMAL = 50
    PRIORITY_FOREGROUND = 100
    PRIORITY_HUD = 200

    def __init__(self, enabled: bool = True, priority: int = PRIORITY_NORMAL) -> None:
        """
        Инициализация слоя.

        Args:
            enabled: Включён ли слой
            priority: Приоритет отрисовки (меньше = раньше)
        """
        self.enabled = enabled
        self.priority = priority

    @abstractmethod
    def render(self, frame: np.ndarray) -> None:
        """
        Отрисовать слой на кадре.

        Args:
            frame: Кадр в формате RGB (numpy array), модифицируется на месте
        """
        ...
