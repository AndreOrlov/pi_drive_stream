"""Frame Difference детектор движения (простой референс)."""

import numpy as np

from app.overlay.motion.base import BaseMotionDetector
from app.overlay.motion.grid_utils import (
    calculate_cell_size,
    get_cell_bounds,
    get_cell_pixels,
)


class FrameDiffDetector(BaseMotionDetector):
    """
    Простой детектор движения на основе разницы между кадрами.

    Алгоритм:
    1. Разбивает кадр на сетку ячеек
    2. Вычисляет среднюю яркость каждой ячейки
    3. Сравнивает с предыдущим кадром (не с фоном!)
    4. Если разница больше порога - есть движение

    Это самый простой алгоритм для сравнения. Не использует сглаживание фона,
    просто сравнивает соседние кадры. Чувствителен к любым изменениям,
    но может давать много ложных срабатываний при дрожании камеры.
    """

    def __init__(
        self,
        grid_width: int = 24,
        grid_height: int = 18,
        threshold: float = 20.0,
        min_brightness: float = 10.0,
    ):
        """
        Инициализация детектора.

        Args:
            grid_width: Количество столбцов в сетке
            grid_height: Количество строк в сетке
            threshold: Порог детекции (разница яркости между кадрами)
            min_brightness: Минимальная средняя яркость кадра для детекции
        """
        super().__init__(grid_width, grid_height, threshold)
        self.min_brightness = min_brightness

        # Предыдущий кадр (вместо фона)
        self.prev_frame: np.ndarray | None = None

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

        # Проверка brightness (edge case)
        avg_brightness = gray.mean()
        if avg_brightness < self.min_brightness:
            return np.zeros((self.grid_height, self.grid_width), dtype=np.uint8)

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

        # Инициализация (первый кадр)
        if self.prev_frame is None:
            self.prev_frame = current_avgs.copy()
            self._initialized = True
            return motion  # Все нули в первом кадре

        # Детекция движения - простое сравнение с предыдущим кадром
        diff = np.abs(current_avgs - self.prev_frame)
        motion = (diff > self.threshold).astype(np.uint8)

        # Сохраняем текущий кадр как предыдущий
        self.prev_frame = current_avgs.copy()

        return motion

    def reset(self) -> None:
        """Сбросить состояние детектора."""
        super().reset()
        self.prev_frame = None
