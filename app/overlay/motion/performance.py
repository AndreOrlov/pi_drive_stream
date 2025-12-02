"""Оптимизатор производительности для детекторов движения."""

import time
from collections import deque

import numpy as np

from app.overlay.motion.base import BaseMotionDetector


class PerformanceOptimizedDetector:
    """
    Обертка для оптимизации производительности детекторов движения.

    Функции:
    - Ограничение максимального FPS детекции
    - Пропуск кадров (skip_frames)
    - Профилирование производительности (время обработки, FPS)
    - Кэширование последнего результата
    """

    def __init__(
        self,
        detector: BaseMotionDetector,
        max_detection_fps: int = 15,
        skip_frames: int = 0,
        enable_profiling: bool = True,
    ):
        """
        Инициализация оптимизатора.

        Args:
            detector: Базовый детектор движения
            max_detection_fps: Максимальный FPS детекции (0 = без ограничений)
            skip_frames: Количество кадров для пропуска между детекциями
            enable_profiling: Включить профилирование производительности
        """
        self.detector = detector
        self.max_detection_fps = max_detection_fps
        self.skip_frames = skip_frames
        self.enable_profiling = enable_profiling

        # Ограничение FPS
        self._min_frame_interval = (
            1.0 / max_detection_fps if max_detection_fps > 0 else 0
        )
        self._last_detection_time = 0.0

        # Пропуск кадров
        self._frame_counter = 0

        # Кэширование результата
        self._cached_result: np.ndarray | None = None

        # Профилирование
        self._detection_times: deque[float] = deque(maxlen=30)  # Последние 30 измерений
        self._last_detection_duration = 0.0
        self._total_detections = 0
        self._total_skipped = 0

    @property
    def grid_width(self) -> int:
        """Ширина сетки из базового детектора."""
        return self.detector.grid_width

    @property
    def grid_height(self) -> int:
        """Высота сетки из базового детектора."""
        return self.detector.grid_height

    def detect(self, frame: np.ndarray) -> np.ndarray:
        """
        Детектировать движение с оптимизацией производительности.

        Args:
            frame: Кадр для анализа

        Returns:
            Матрица движения (grid_height, grid_width) с значениями 0/1
        """
        current_time = time.monotonic()

        # ============================================================
        # 1. Проверка пропуска кадров (skip_frames)
        # ============================================================
        if self.skip_frames > 0 and self._frame_counter > 0:
            # Пропускаем кадр
            self._total_skipped += 1
            self._frame_counter += 1

            # Проверяем, достигли ли лимита пропуска
            if self._frame_counter > self.skip_frames:
                # Сбрасываем счетчик - следующий кадр будет обработан
                self._frame_counter = 0

            # Возвращаем кэшированный результат
            if self._cached_result is not None:
                return self._cached_result
            # Если кэша нет - возвращаем пустую матрицу
            return np.zeros((self.grid_height, self.grid_width), dtype=np.uint8)

        # ============================================================
        # 2. Проверка ограничения FPS
        # ============================================================
        if self.max_detection_fps > 0:
            time_since_last = current_time - self._last_detection_time
            if time_since_last < self._min_frame_interval:
                self._total_skipped += 1
                # Возвращаем кэшированный результат
                if self._cached_result is not None:
                    return self._cached_result
                # Если кэша нет - возвращаем пустую матрицу
                return np.zeros((self.grid_height, self.grid_width), dtype=np.uint8)

        # ============================================================
        # 3. Выполнить детекцию
        # ============================================================
        start_time = time.perf_counter() if self.enable_profiling else 0

        motion = self.detector.detect(frame)

        if self.enable_profiling:
            detection_duration = time.perf_counter() - start_time
            self._detection_times.append(detection_duration)
            self._last_detection_duration = detection_duration

        # Обновляем метрики
        self._last_detection_time = current_time
        self._total_detections += 1

        # Кэшируем результат
        self._cached_result = motion

        # Запускаем счетчик пропуска кадров после обработки
        if self.skip_frames > 0:
            self._frame_counter = 1

        return motion

    def reset(self) -> None:
        """Сбросить состояние детектора и кэш."""
        self.detector.reset()
        self._cached_result = None
        self._frame_counter = 0
        self._last_detection_time = 0.0

    def is_initialized(self) -> bool:
        """Проверить инициализацию базового детектора."""
        return self.detector.is_initialized()

    def get_stats(self) -> dict:
        """
        Получить статистику производительности.

        Returns:
            Словарь с метриками производительности
        """
        if not self.enable_profiling or not self._detection_times:
            return {
                "total_detections": self._total_detections,
                "total_skipped": self._total_skipped,
            }

        detection_times_list = list(self._detection_times)

        avg_time = sum(detection_times_list) / len(detection_times_list)
        min_time = min(detection_times_list)
        max_time = max(detection_times_list)

        # FPS = 1 / avg_time
        actual_fps = 1.0 / avg_time if avg_time > 0 else 0

        return {
            "total_detections": self._total_detections,
            "total_skipped": self._total_skipped,
            "skip_ratio": (
                self._total_skipped / (self._total_detections + self._total_skipped)
                if (self._total_detections + self._total_skipped) > 0
                else 0
            ),
            "last_duration_ms": self._last_detection_duration * 1000,
            "avg_duration_ms": avg_time * 1000,
            "min_duration_ms": min_time * 1000,
            "max_duration_ms": max_time * 1000,
            "actual_fps": actual_fps,
            "target_fps": self.max_detection_fps
            if self.max_detection_fps > 0
            else None,
        }

    def reset_stats(self) -> None:
        """Сбросить статистику производительности."""
        self._detection_times.clear()
        self._last_detection_duration = 0.0
        self._total_detections = 0
        self._total_skipped = 0
