"""Grid-based Mean детектор движения."""

import numpy as np

from app.overlay.motion.base import BaseMotionDetector
from app.overlay.motion.grid_utils import (
    calculate_cell_size,
    get_cell_bounds,
    get_cell_pixels,
)


class GridMeanDetector(BaseMotionDetector):
    """
    Улучшенный детектор движения на основе средней яркости ячейки.

    Алгоритм:
    1. Разбивает кадр на сетку ячеек
    2. Вычисляет среднюю яркость каждой ячейки
    3. Сравнивает с фоновой моделью (с адаптивным порогом)
    4. Обновляет фон с двухскоростным экспоненциальным сглаживанием
    5. Обрабатывает edge cases (темные кадры, резкие изменения освещения)
    """

    def __init__(
        self,
        grid_width: int = 24,
        grid_height: int = 18,
        threshold: float = 25.0,
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
            threshold: Базовый порог детекции (разница яркости)
            base_alpha: Базовая скорость обновления фона (0.01-0.1)
            alpha_fast_multiplier: Множитель для быстрого обновления (нет движения)
            alpha_slow_multiplier: Множитель для медленного обновления (есть движение)
            use_adaptive_threshold: Использовать адаптивный порог на основе std
            min_brightness: Минимальная средняя яркость кадра для детекции
            max_change_threshold: Порог для определения резкого изменения освещения
        """
        super().__init__(grid_width, grid_height, threshold)
        self.base_alpha = base_alpha
        self.alpha_fast = base_alpha * alpha_fast_multiplier
        self.alpha_slow = base_alpha * alpha_slow_multiplier
        self.use_adaptive_threshold = use_adaptive_threshold
        self.min_brightness = min_brightness
        self.max_change_threshold = max_change_threshold

        # Статистика для edge cases
        self._last_avg_brightness = 0.0

    def reset(self) -> None:
        """Сбросить состояние детектора."""
        super().reset()
        self._last_avg_brightness = 0.0

    def detect(self, frame: np.ndarray) -> np.ndarray:
        """
        Детектировать движение в кадре с улучшенными алгоритмами.

        Args:
            frame: Кадр (RGB или grayscale)

        Returns:
            Матрица движения (grid_height, grid_width) с значениями 0/1
        """
        # Конвертация в grayscale
        gray = self._to_grayscale(frame)
        height, width = gray.shape

        # ============================================================
        # EDGE CASE 1: Проверка минимальной яркости
        # ============================================================
        avg_brightness = float(gray.mean())

        if avg_brightness < self.min_brightness:
            # Слишком темный кадр - пропускаем детекцию
            # НО обновляем _last_avg_brightness для корректного отслеживания освещения
            self._last_avg_brightness = avg_brightness
            return np.zeros((self.grid_height, self.grid_width), dtype=np.uint8)

        # ============================================================
        # EDGE CASE 2: Проверка резкого изменения освещения
        # ============================================================
        if self._last_avg_brightness > 0:
            brightness_change = abs(avg_brightness - self._last_avg_brightness)
            if brightness_change > self.max_change_threshold:
                # Резкое изменение освещения (включили/выключили свет)
                # Сбрасываем фон для переинициализации
                self.reset()

        self._last_avg_brightness = avg_brightness

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

        # ============================================================
        # ДЕТЕКЦИЯ ДВИЖЕНИЯ с адаптивным порогом
        # ============================================================
        diff = np.abs(current_avgs - self.background)

        if self.use_adaptive_threshold:
            # Адаптивный порог: base_threshold + k * std(background)
            # Коэффициент 2.5 подобран эмпирически
            adaptive_threshold = max(self.threshold, float(self.background.std()) * 2.5)
        else:
            adaptive_threshold = self.threshold

        motion = (diff > adaptive_threshold).astype(np.uint8)

        # ============================================================
        # ДВУХСКОРОСТНОЕ ОБНОВЛЕНИЕ ФОНА
        # ============================================================
        # Где движения НЕТ (motion == 0): быстрое обновление (alpha_fast)
        # Где движение ЕСТЬ (motion == 1): медленное обновление (alpha_slow)
        #
        # Логика: статичные области быстро адаптируются к новому фону,
        # а области с движением обновляются медленно, чтобы не "съесть"
        # движущийся объект в фон
        alpha_map = np.where(motion == 0, self.alpha_fast, self.alpha_slow)
        self.background = alpha_map * current_avgs + (1 - alpha_map) * self.background

        return motion
