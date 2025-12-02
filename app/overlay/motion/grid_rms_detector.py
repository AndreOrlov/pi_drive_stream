"""Grid-based RMS детектор движения."""

import numpy as np

from app.overlay.motion.base import BaseMotionDetector
from app.overlay.motion.grid_utils import (
    calculate_cell_size,
    get_cell_bounds,
    get_cell_pixels,
)


class GridRMSDetector(BaseMotionDetector):
    """
    Детектор движения на основе RMS (Root Mean Square) яркости ячейки.

    Алгоритм:
    1. Разбивает кадр на сетку ячеек
    2. Вычисляет RMS разницы пикселей ячейки с фоном
    3. Сравнивает с порогом детекции
    4. Обновляет фон с экспоненциальным сглаживанием

    RMS более чувствителен к локальным изменениям в ячейке по сравнению с простым средним.
    Формула: RMS = sqrt(mean((pixels - background)^2))
    """

    def __init__(
        self,
        grid_width: int = 24,
        grid_height: int = 18,
        threshold: float = 15.0,  # RMS требует меньший порог
        base_alpha: float = 0.02,
        alpha_fast_multiplier: float = 5.0,
        alpha_slow_multiplier: float = 0.5,
        use_adaptive_threshold: bool = True,
        min_brightness: float = 10.0,
        max_change_threshold: float = 200.0,
    ):
        """
        Инициализация детектора.

        Args:
            grid_width: Количество столбцов в сетке
            grid_height: Количество строк в сетке
            threshold: Порог детекции RMS (обычно ниже чем для mean)
            base_alpha: Базовая скорость обновления фона
            alpha_fast_multiplier: Множитель для быстрого обновления фона
            alpha_slow_multiplier: Множитель для медленного обновления фона
            use_adaptive_threshold: Использовать ли адаптивный порог
            min_brightness: Минимальная средняя яркость кадра для детекции
            max_change_threshold: Максимальное резкое изменение яркости для автосброса
        """
        super().__init__(grid_width, grid_height, threshold)
        self.base_alpha = base_alpha
        self.alpha_fast = base_alpha * alpha_fast_multiplier
        self.alpha_slow = base_alpha * alpha_slow_multiplier
        self.use_adaptive_threshold = use_adaptive_threshold
        self.min_brightness = min_brightness
        self.max_change_threshold = max_change_threshold
        self._last_avg_brightness = 0.0

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

        # 1. Проверка brightness (edge case)
        avg_brightness = float(gray.mean())
        if avg_brightness < self.min_brightness:
            # Слишком темный кадр - пропускаем детекцию
            # НО обновляем _last_avg_brightness для корректного отслеживания освещения
            self._last_avg_brightness = avg_brightness
            return np.zeros((self.grid_height, self.grid_width), dtype=np.uint8)

        # 2. Проверка резкого изменения освещения (edge case)
        if self._last_avg_brightness > 0:
            brightness_change = abs(avg_brightness - self._last_avg_brightness)
            if brightness_change > self.max_change_threshold:
                self.reset()  # Сброс фона при резком изменении освещения

        self._last_avg_brightness = avg_brightness

        # Размер ячейки
        cell_w, cell_h = calculate_cell_size(width, height, self.grid_width, self.grid_height)

        # Матрица движения (результат)
        motion = np.zeros((self.grid_height, self.grid_width), dtype=np.uint8)

        # Матрица текущих средних яркостей (для обновления фона)
        current_avgs = np.zeros((self.grid_height, self.grid_width), dtype=np.float32)

        # Матрица RMS значений (для детекции)
        rms_values = np.zeros((self.grid_height, self.grid_width), dtype=np.float32)

        # Вычисляем среднюю яркость и RMS для каждой ячейки
        for j in range(self.grid_height):
            for i in range(self.grid_width):
                x1, y1, x2, y2 = get_cell_bounds(i, j, cell_w, cell_h)
                cell_pixels = get_cell_pixels(gray, x1, y1, x2, y2)

                if cell_pixels.size > 0:
                    # Среднее значение для обновления фона
                    current_avgs[j, i] = cell_pixels.mean()

                    # RMS для детекции (только если фон инициализирован)
                    if self.background is not None:
                        # Разница каждого пикселя с фоном
                        cell_diff = cell_pixels.astype(np.float32) - self.background[j, i]
                        # RMS = sqrt(mean(diff^2))
                        rms_values[j, i] = np.sqrt(np.mean(cell_diff ** 2))

        # Инициализация фона (первый кадр)
        if self.background is None:
            self.background = current_avgs.copy()
            self._initialized = True
            return motion  # Все нули в первом кадре

        # 4. Детекция движения с адаптивным порогом
        if self.use_adaptive_threshold:
            # Адаптивный порог = base_threshold + k * std(rms_values)
            threshold = max(self.threshold, rms_values.std() * 2.0)
        else:
            threshold = self.threshold

        motion = (rms_values > threshold).astype(np.uint8)

        # 5. Двухскоростное обновление фона
        # Там где движения НЕТ - быстрое обновление (alpha_fast)
        # Там где движение ЕСТЬ - медленное обновление (alpha_slow)
        alpha_map = np.where(motion == 0, self.alpha_fast, self.alpha_slow)
        self.background = alpha_map * current_avgs + (1 - alpha_map) * self.background

        return motion

    def reset(self) -> None:
        """Сбросить состояние детектора."""
        super().reset()
        self._last_avg_brightness = 0.0
