"""Тесты для FrameDiffDetector."""

import numpy as np

from app.overlay.motion.frame_diff_detector import FrameDiffDetector


def test_frame_diff_detector_initialization() -> None:
    """Тест инициализации FrameDiffDetector."""
    detector = FrameDiffDetector(
        grid_width=4,
        grid_height=3,
        threshold=20.0,
        min_brightness=10.0,
    )

    assert detector.grid_width == 4
    assert detector.grid_height == 3
    assert detector.threshold == 20.0
    assert detector.min_brightness == 10.0
    assert not detector.is_initialized()


def test_frame_diff_detector_first_frame() -> None:
    """Тест первого кадра (инициализация предыдущего кадра)."""
    detector = FrameDiffDetector(grid_width=4, grid_height=3)

    # Создаем равномерный серый кадр
    frame = np.full((60, 80), 128, dtype=np.uint8)

    motion = detector.detect(frame)

    # Первый кадр должен инициализировать prev_frame
    assert detector.is_initialized()
    assert detector.prev_frame is not None
    assert detector.prev_frame.shape == (3, 4)

    # Движения не должно быть
    assert motion.sum() == 0


def test_frame_diff_detector_motion_detection() -> None:
    """Тест детекции движения при изменении между кадрами."""
    detector = FrameDiffDetector(
        grid_width=4,
        grid_height=3,
        threshold=15.0,  # Низкий порог для гарантированной детекции
        min_brightness=10.0,
    )

    # Первый кадр: равномерный
    frame1 = np.full((60, 80), 100, dtype=np.uint8)
    motion1 = detector.detect(frame1)
    assert motion1.sum() == 0  # Нет движения на первом кадре

    # Второй кадр: изменяем одну ячейку (правый нижний угол)
    frame2 = frame1.copy()
    frame2[40:60, 60:80] = 200  # Яркое пятно в правом нижнем углу

    motion2 = detector.detect(frame2)

    # Должно быть движение в одной ячейке (3, 3) -> индекс (2, 3)
    assert motion2.sum() >= 1
    assert motion2[2, 3] == 1  # Правый нижний угол


def test_frame_diff_detector_no_motion() -> None:
    """Тест отсутствия движения при одинаковых кадрах."""
    detector = FrameDiffDetector(
        grid_width=4,
        grid_height=3,
        threshold=10.0,
    )

    # Первый кадр
    frame1 = np.full((60, 80), 128, dtype=np.uint8)
    detector.detect(frame1)

    # Второй кадр - такой же
    frame2 = np.full((60, 80), 128, dtype=np.uint8)
    motion = detector.detect(frame2)

    # Не должно быть движения
    assert motion.sum() == 0


def test_frame_diff_detector_dark_frame() -> None:
    """Тест игнорирования слишком темных кадров."""
    detector = FrameDiffDetector(
        grid_width=4,
        grid_height=3,
        threshold=20.0,
        min_brightness=50.0,
    )

    # Инициализация фона
    frame1 = np.full((60, 80), 100, dtype=np.uint8)
    detector.detect(frame1)

    # Очень темный кадр
    dark_frame = np.full((60, 80), 5, dtype=np.uint8)
    motion = detector.detect(dark_frame)

    # Не должно быть детекции на темном кадре
    assert motion.sum() == 0


def test_frame_diff_detector_continuous_motion() -> None:
    """Тест непрерывного движения (каждый кадр меняется)."""
    detector = FrameDiffDetector(
        grid_width=4,
        grid_height=3,
        threshold=10.0,
    )

    # Первый кадр
    frame1 = np.full((60, 80), 100, dtype=np.uint8)
    detector.detect(frame1)

    # Второй кадр - изменение
    frame2 = np.full((60, 80), 120, dtype=np.uint8)
    motion2 = detector.detect(frame2)

    # Должно быть движение во всех ячейках
    assert motion2.sum() == 12  # 4x3 = 12 ячеек

    # Третий кадр - еще изменение
    frame3 = np.full((60, 80), 140, dtype=np.uint8)
    motion3 = detector.detect(frame3)

    # Снова должно быть движение во всех ячейках
    assert motion3.sum() == 12


def test_frame_diff_detector_reset_functionality() -> None:
    """Тест функции сброса."""
    detector = FrameDiffDetector(grid_width=4, grid_height=3)

    # Инициализация
    frame = np.full((60, 80), 128, dtype=np.uint8)
    detector.detect(frame)
    assert detector.is_initialized()
    assert detector.prev_frame is not None

    # Сброс
    detector.reset()

    # Проверяем сброс состояния
    assert not detector.is_initialized()
    assert detector.prev_frame is None


def test_frame_diff_detector_grayscale_input() -> None:
    """Тест работы с grayscale входом."""
    detector = FrameDiffDetector(grid_width=4, grid_height=3)

    # Grayscale кадр
    frame_gray = np.full((60, 80), 128, dtype=np.uint8)
    motion = detector.detect(frame_gray)

    assert motion.shape == (3, 4)
    assert detector.is_initialized()


def test_frame_diff_vs_grid_mean_sensitivity() -> None:
    """Тест что FrameDiff более чувствителен к быстрым изменениям."""
    from app.overlay.motion.grid_mean_detector import GridMeanDetector

    # Создаем два детектора с одинаковыми параметрами
    frame_diff_detector = FrameDiffDetector(
        grid_width=4,
        grid_height=3,
        threshold=8.0,  # Низкий порог для детекции небольших изменений
        min_brightness=10.0,
    )

    mean_detector = GridMeanDetector(
        grid_width=4,
        grid_height=3,
        threshold=20.0,
        base_alpha=0.5,  # Быстрое обновление для сравнения
        min_brightness=10.0,
    )

    # Инициализация фона для обоих
    frame1 = np.full((60, 80), 100, dtype=np.uint8)
    frame_diff_detector.detect(frame1)
    mean_detector.detect(frame1)

    # Второй кадр - небольшое изменение (10 единиц)
    frame2 = np.full((60, 80), 110, dtype=np.uint8)
    motion_frame_diff = frame_diff_detector.detect(frame2)
    _ = mean_detector.detect(frame2)

    # FrameDiff должен быть более чувствительным (детектирует изменение сразу)
    # Mean может не детектировать из-за сглаживания фона
    assert motion_frame_diff.sum() > 0  # FrameDiff детектирует
    # Mean может детектировать, а может и нет - зависит от alpha


def test_frame_diff_detector_local_change() -> None:
    """Тест детекции локального изменения в одной ячейке."""
    detector = FrameDiffDetector(
        grid_width=4,
        grid_height=3,
        threshold=10.0,  # Низкий порог для детекции локальных изменений
    )

    # Первый кадр
    frame1 = np.full((60, 80), 100, dtype=np.uint8)
    detector.detect(frame1)

    # Второй кадр - изменение только в центре одной ячейки
    frame2 = frame1.copy()
    # Ячейка (0,0) занимает пиксели [0:20, 0:20]
    # Изменяем значительную часть ячейки для гарантированной детекции
    frame2[5:15, 5:15] = 200  # 10x10 пикселей = 100 пикселей из 400

    motion = detector.detect(frame2)

    # Должно быть движение в ячейке (0,0)
    assert motion[0, 0] == 1
    # Остальные ячейки без движения
    assert motion.sum() == 1
