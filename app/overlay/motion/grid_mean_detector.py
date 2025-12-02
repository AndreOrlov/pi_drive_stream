"""Grid-based Mean детектор движения."""

import numpy as np

from app.overlay.motion.base import BaseMotionDetector
from app.overlay.motion.grid_utils import calculate_cell_size, get_cell_bounds, get_cell_pixels


class GridMeanDetector(BaseMotionDetector):
    """
    Детектор движения на основе средней яркости ячейки.

    Алгоритм:
    1. Разбивает кадр на сетку ячеек
    2. Вычисляет среднюю яркость каждой ячейки
    3. Сравнивает с фоновой моделью
    4. Обновляет фон с экспоненциальным сглаживанием
    """

    def __init__(
        self,
        grid_width: int = 24,
        grid_height: int = 18,
        threshold: float = 25.0,
        alpha: float = 0.02,
    ):
        """
        Инициализация детектора.

        Args:
            grid_width: Количество столбцов в сетке
            grid_height: Количество строк в сетке
            threshold: Порог детекции (разница яркости)
            alpha: Скорость обновления фона (0.01-0.1)
        """
        super().__init__(grid_width, grid_height, threshold)
        self.alpha = alpha

    def detect(self, frame: np.ndarray) -> np.ndarray:
        """
        Детектировать движение в кадре.

        Args:
            frame: Кадр (RGB или grayscale)

        Returns:
            Матрица движения (grid_height, grid_width) с значениями 0/1
        """
        # Конвертация в grayscale
        gray = self._to_grayscale(frame)
        height, width = gray.shape

        # Размер ячейки
        cell_w, cell_h = calculate_cell_size(width, height, self.grid_width, self.grid_height)

        # Матрица движения (результат)
        motion = np.zeros((self.grid_height, self.grid_width), dtype=np.uint8)

        # Матрица текущих средних яркостей
        current_avgs = np.zeros((self.grid_height, self.grid_width), dtype=np.float32)

        # Вычисляем среднюю яркость для каждой ячейки
        for j in range(self.grid_height):
            for i in range(self.grid_width):
                x1, y1, x2, y2 = get_cell_bounds(i, j, cell_w, cell_h)
                cell_pixels = get_cell_pixels(gray, x1, y1, x2, y2)

                if cell_pixels.size > 0:
                    current_avgs[j, i] = cell_pixels.mean()

        # Инициализация фона (первый кадр)
        if self.background is None:
            self.background = current_avgs.copy()
            self._initialized = True
            return motion  # Все нули в первом кадре

        # Детекция движения
        diff = np.abs(current_avgs - self.background)
        motion = (diff > self.threshold).astype(np.uint8)

        # Обновление фона (экспоненциальное сглаживание)
        self.background = self.alpha * current_avgs + (1 - self.alpha) * self.background

        return motion

