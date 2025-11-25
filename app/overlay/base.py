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
    """

    def __init__(self, enabled: bool = True) -> None:
        """
        Инициализация слоя.

        Args:
            enabled: Включён ли слой
        """
        self.enabled = enabled

    @abstractmethod
    def render(self, frame: np.ndarray) -> None:
        """
        Отрисовать слой на кадре.

        Args:
            frame: Кадр в формате RGB (numpy array), модифицируется на месте
        """
        ...
