"""Тесты для улучшенного GridMeanDetector."""

import numpy as np

from app.overlay.motion.grid_mean_detector import GridMeanDetector


def test_detector_initialization() -> None:
    """Тест инициализации детектора с новыми параметрами."""
    detector = GridMeanDetector(
        grid_width=32,
        grid_height=24,
        threshold=25.0,
        alpha=0.02,
        alpha_fast_multiplier=5.0,
        alpha_slow_multiplier=0.5,
        use_adaptive_threshold=True,
        min_brightness=10.0,
        max_change_threshold=200.0,
    )

    assert detector.grid_width == 32
    assert detector.grid_height == 24
    assert detector.threshold == 25.0
    assert detector.alpha == 0.02
    assert detector.alpha_fast == 0.1  # 0.02 * 5.0
    assert detector.alpha_slow == 0.01  # 0.02 * 0.5
    assert detector.use_adaptive_threshold is True
    assert detector.min_brightness == 10.0
    assert detector.max_change_threshold == 200.0
    assert not detector.is_initialized()


def test_detector_first_frame_initialization() -> None:
    """Тест инициализации фона на первом кадре."""
    detector = GridMeanDetector(grid_width=32, grid_height=24)
    frame = np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)

    motion = detector.detect(frame)

    assert detector.is_initialized()
    assert detector.background is not None
    assert detector.background.shape == (24, 32)
    assert np.all(motion == 0)  # Первый кадр: движения нет


def test_edge_case_dark_frame() -> None:
    """Тест edge case: слишком темный кадр (яркость < min_brightness)."""
    detector = GridMeanDetector(
        grid_width=32,
        grid_height=24,
        min_brightness=10.0,
    )

    # Первый кадр для инициализации
    normal_frame = np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)
    detector.detect(normal_frame)

    # Очень темный кадр (средняя яркость < 10)
    dark_frame = np.random.randint(0, 5, (480, 640, 3), dtype=np.uint8)
    motion = detector.detect(dark_frame)

    # Должны вернуть нулевую матрицу движения
    assert np.all(motion == 0)
    assert motion.shape == (24, 32)


def test_edge_case_sudden_brightness_change() -> None:
    """Тест edge case: резкое изменение освещения (reset фона)."""
    detector = GridMeanDetector(
        grid_width=32,
        grid_height=24,
        max_change_threshold=50.0,  # Низкий порог для теста
    )

    # Первый кадр: темный
    frame1 = np.ones((480, 640, 3), dtype=np.uint8) * 50
    detector.detect(frame1)
    assert detector.is_initialized()

    # Второй кадр: резко яркий (разница > 50)
    frame2 = np.ones((480, 640, 3), dtype=np.uint8) * 200
    motion = detector.detect(frame2)

    # Детектор должен сбросить фон (но остаться инициализированным после обработки)
    # Проверяем, что не упал
    assert motion.shape == (24, 32)


def test_two_speed_background_update() -> None:
    """Тест двухскоростного обновления фона."""
    detector = GridMeanDetector(
        grid_width=4,  # Маленькая сетка для простоты
        grid_height=3,
        alpha=0.1,
        alpha_fast_multiplier=2.0,  # alpha_fast = 0.2
        alpha_slow_multiplier=0.5,  # alpha_slow = 0.05
        threshold=10.0,
    )

    # Инициализация: все ячейки с яркостью 100
    frame1 = np.ones((300, 400, 3), dtype=np.uint8) * 100
    detector.detect(frame1)

    # Второй кадр: все ячейки с яркостью 120 (без движения)
    frame2 = np.ones((300, 400, 3), dtype=np.uint8) * 120
    motion2 = detector.detect(frame2)

    # Разница = 20 > threshold=10, должно быть движение
    assert np.any(motion2 == 1)

    # Фон обновится медленно в ячейках с движением (alpha_slow)
    # и быстро в ячейках без движения (alpha_fast)


def test_adaptive_threshold() -> None:
    """Тест адаптивного порога на основе стандартного отклонения."""
    detector = GridMeanDetector(
        grid_width=32,
        grid_height=24,
        threshold=10.0,
        use_adaptive_threshold=True,
    )

    # Кадр с высокой вариацией яркости
    frame = np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)
    detector.detect(frame)

    # Проверяем, что детектор инициализирован
    assert detector.is_initialized()
    assert detector.background is not None

    # Второй кадр для проверки детекции
    frame2 = np.random.randint(55, 205, (480, 640, 3), dtype=np.uint8)
    motion = detector.detect(frame2)

    # Адаптивный порог должен учитывать std фона
    # Проверяем, что motion матрица имеет правильный размер
    assert motion.shape == (24, 32)
    assert motion.dtype == np.uint8


def test_disable_adaptive_threshold() -> None:
    """Тест с отключенным адаптивным порогом."""
    detector = GridMeanDetector(
        grid_width=32,
        grid_height=24,
        threshold=25.0,
        use_adaptive_threshold=False,
    )

    frame = np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)
    detector.detect(frame)

    # С фиксированным порогом
    frame2 = np.random.randint(60, 210, (480, 640, 3), dtype=np.uint8)
    motion = detector.detect(frame2)

    assert motion.shape == (24, 32)


def test_reset_functionality() -> None:
    """Тест функции reset()."""
    detector = GridMeanDetector(grid_width=32, grid_height=24)

    # Инициализируем детектор
    frame = np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)
    detector.detect(frame)
    assert detector.is_initialized()
    assert detector.background is not None

    # Сбрасываем
    detector.reset()
    assert not detector.is_initialized()
    assert detector.background is None
    assert detector._last_avg_brightness == 0.0


def test_grayscale_input() -> None:
    """Тест с уже grayscale входным кадром."""
    detector = GridMeanDetector(grid_width=32, grid_height=24)

    # Grayscale кадр (2D массив)
    gray_frame = np.random.randint(50, 200, (480, 640), dtype=np.uint8)
    motion = detector.detect(gray_frame)

    assert detector.is_initialized()
    assert motion.shape == (24, 32)


def test_motion_detection_with_change() -> None:
    """Тест детекции реального движения."""
    detector = GridMeanDetector(
        grid_width=8,
        grid_height=6,
        threshold=20.0,
        use_adaptive_threshold=False,
    )

    # Первый кадр: однородный фон
    frame1 = np.ones((480, 640, 3), dtype=np.uint8) * 100
    motion1 = detector.detect(frame1)
    assert np.all(motion1 == 0)  # Инициализация, нет движения

    # Второй кадр: изменение в правом нижнем углу
    frame2 = np.ones((480, 640, 3), dtype=np.uint8) * 100
    frame2[300:480, 400:640] = 150  # Яркая область

    motion2 = detector.detect(frame2)

    # Должно быть движение в некоторых ячейках
    assert np.any(motion2 == 1)
    # И должны быть ячейки без движения
    assert np.any(motion2 == 0)
