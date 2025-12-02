"""Тесты для PerformanceOptimizedDetector."""

import numpy as np

from app.overlay.motion.grid_mean_detector import GridMeanDetector
from app.overlay.motion.performance import PerformanceOptimizedDetector


def test_performance_detector_initialization() -> None:
    """Тест инициализации оптимизатора производительности."""
    base_detector = GridMeanDetector(grid_width=32, grid_height=24)
    perf_detector = PerformanceOptimizedDetector(
        detector=base_detector,
        max_detection_fps=15,
        skip_frames=0,
        enable_profiling=True,
    )

    assert perf_detector.max_detection_fps == 15
    assert perf_detector.skip_frames == 0
    assert perf_detector.enable_profiling is True
    assert perf_detector.grid_width == 32
    assert perf_detector.grid_height == 24


def test_performance_detector_basic_detection() -> None:
    """Тест базовой детекции через оптимизатор."""
    base_detector = GridMeanDetector(grid_width=32, grid_height=24)
    perf_detector = PerformanceOptimizedDetector(
        detector=base_detector,
        max_detection_fps=0,  # Без ограничений
        skip_frames=0,
        enable_profiling=True,
    )

    frame = np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)
    motion = perf_detector.detect(frame)

    assert motion.shape == (24, 32)
    assert perf_detector.is_initialized()


def test_performance_detector_fps_limit() -> None:
    """Тест ограничения FPS детекции."""
    base_detector = GridMeanDetector(grid_width=32, grid_height=24)
    perf_detector = PerformanceOptimizedDetector(
        detector=base_detector,
        max_detection_fps=10,  # 10 FPS = 100ms между кадрами
        skip_frames=0,
        enable_profiling=True,
    )

    frame = np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)

    # Первая детекция - должна пройти
    motion1 = perf_detector.detect(frame)
    assert motion1 is not None

    # Немедленная вторая детекция - должна использовать кэш
    perf_detector.detect(frame)
    stats = perf_detector.get_stats()

    # Вторая детекция должна быть пропущена
    assert stats["total_skipped"] > 0


def test_performance_detector_skip_frames() -> None:
    """Тест пропуска кадров."""
    base_detector = GridMeanDetector(grid_width=32, grid_height=24)
    perf_detector = PerformanceOptimizedDetector(
        detector=base_detector,
        max_detection_fps=0,  # Без ограничений FPS
        skip_frames=2,  # Пропускать 2 кадра
        enable_profiling=True,
    )

    frame = np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)

    # Кадр 0: обработка
    perf_detector.detect(frame)
    stats0 = perf_detector.get_stats()
    assert stats0["total_detections"] == 1
    assert stats0["total_skipped"] == 0

    # Кадр 1: пропуск (счетчик 1)
    perf_detector.detect(frame)
    stats1 = perf_detector.get_stats()
    assert stats1["total_detections"] == 1
    assert stats1["total_skipped"] == 1

    # Кадр 2: пропуск (счетчик 2)
    perf_detector.detect(frame)
    stats2 = perf_detector.get_stats()
    assert stats2["total_detections"] == 1
    assert stats2["total_skipped"] == 2

    # Кадр 3: обработка (счетчик сброшен)
    perf_detector.detect(frame)
    stats3 = perf_detector.get_stats()
    assert stats3["total_detections"] == 2
    assert stats3["total_skipped"] == 2


def test_performance_detector_profiling() -> None:
    """Тест профилирования производительности."""
    base_detector = GridMeanDetector(grid_width=32, grid_height=24)
    perf_detector = PerformanceOptimizedDetector(
        detector=base_detector,
        max_detection_fps=0,
        skip_frames=0,
        enable_profiling=True,
    )

    frame = np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)

    # Выполняем несколько детекций
    for _ in range(5):
        perf_detector.detect(frame)

    stats = perf_detector.get_stats()

    # Проверяем, что статистика собрана
    assert "total_detections" in stats
    assert stats["total_detections"] == 5
    assert "avg_duration_ms" in stats
    assert stats["avg_duration_ms"] > 0
    assert "min_duration_ms" in stats
    assert "max_duration_ms" in stats
    assert "actual_fps" in stats
    assert stats["actual_fps"] > 0


def test_performance_detector_profiling_disabled() -> None:
    """Тест с отключенным профилированием."""
    base_detector = GridMeanDetector(grid_width=32, grid_height=24)
    perf_detector = PerformanceOptimizedDetector(
        detector=base_detector,
        max_detection_fps=0,
        skip_frames=0,
        enable_profiling=False,
    )

    frame = np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)
    perf_detector.detect(frame)

    stats = perf_detector.get_stats()

    # Статистика должна быть минимальной
    assert "total_detections" in stats
    assert "avg_duration_ms" not in stats


def test_performance_detector_reset() -> None:
    """Тест сброса состояния."""
    base_detector = GridMeanDetector(grid_width=32, grid_height=24)
    perf_detector = PerformanceOptimizedDetector(
        detector=base_detector,
        max_detection_fps=0,
        skip_frames=0,
        enable_profiling=True,
    )

    frame = np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)

    # Выполняем детекцию
    perf_detector.detect(frame)
    assert perf_detector.is_initialized()

    # Сбрасываем
    perf_detector.reset()
    assert not perf_detector.is_initialized()


def test_performance_detector_reset_stats() -> None:
    """Тест сброса статистики."""
    base_detector = GridMeanDetector(grid_width=32, grid_height=24)
    perf_detector = PerformanceOptimizedDetector(
        detector=base_detector,
        max_detection_fps=0,
        skip_frames=0,
        enable_profiling=True,
    )

    frame = np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)

    # Выполняем детекцию
    for _ in range(5):
        perf_detector.detect(frame)

    stats_before = perf_detector.get_stats()
    assert stats_before["total_detections"] == 5

    # Сбрасываем статистику
    perf_detector.reset_stats()

    stats_after = perf_detector.get_stats()
    assert stats_after["total_detections"] == 0


def test_performance_detector_caching() -> None:
    """Тест кэширования результатов."""
    base_detector = GridMeanDetector(grid_width=32, grid_height=24)
    perf_detector = PerformanceOptimizedDetector(
        detector=base_detector,
        max_detection_fps=10,  # Низкий FPS для проверки кэша
        skip_frames=0,
        enable_profiling=True,
    )

    frame = np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)

    # Первая детекция
    motion1 = perf_detector.detect(frame)

    # Немедленная вторая детекция должна вернуть кэшированный результат
    motion2 = perf_detector.detect(frame)

    # Результаты должны быть идентичны (тот же объект из кэша)
    assert np.array_equal(motion1, motion2)


def test_performance_detector_skip_ratio() -> None:
    """Тест расчета skip_ratio."""
    base_detector = GridMeanDetector(grid_width=32, grid_height=24)
    perf_detector = PerformanceOptimizedDetector(
        detector=base_detector,
        max_detection_fps=0,
        skip_frames=1,  # Пропускать каждый второй кадр
        enable_profiling=True,
    )

    frame = np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)

    # Выполняем несколько детекций
    for _ in range(10):
        perf_detector.detect(frame)

    stats = perf_detector.get_stats()

    # Примерно половина кадров должна быть пропущена
    assert "skip_ratio" in stats
    assert 0.4 <= stats["skip_ratio"] <= 0.6  # Примерно 50%
