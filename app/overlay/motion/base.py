"""Базовый класс для детекторов движения."""

from abc import ABC, abstractmethod
import numpy as np
import cv2


class BaseMotionDetector(ABC):
    """Базовый класс для всех детекторов движения."""

    def __init__(
        self,
        grid_width: int,
        grid_height: int,
        threshold: float = 25.0,
    ):
        """
        Инициализация базового детектора.

        Args:
            grid_width: Количество столбцов в сетке
            grid_height: Количество строк в сетке
            threshold: Порог детекции движения
        """
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.threshold = threshold

        # Фон: матрица средних яркостей ячеек
        self.background: np.ndarray | None = None
        self._initialized = False

    @abstractmethod
    def detect(self, frame: np.ndarray) -> np.ndarray:
        """
        Детектировать движение в кадре.

        Args:
            frame: Кадр (RGB или grayscale)

        Returns:
            Матрица движения (grid_height, grid_width) с значениями 0/1
        """
        ...

    def reset(self) -> None:
        """Сбросить состояние детектора."""
        self.background = None
        self._initialized = False

    def is_initialized(self) -> bool:
        """Проверить, инициализирован ли детектор."""
        return self._initialized

    def _to_grayscale(self, frame: np.ndarray) -> np.ndarray:
        """
        Конвертировать кадр в grayscale.

        Args:
            frame: Кадр (RGB или grayscale)

        Returns:
            Grayscale кадр
        """
        if len(frame.shape) == 3:
            return cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        return frame

