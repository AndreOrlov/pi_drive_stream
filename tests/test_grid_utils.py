"""Тесты для утилит работы с сеткой детекции движения."""

import numpy as np
import pytest

from app.overlay.motion.grid_utils import (
    calculate_cell_size,
    get_cell_bounds,
    get_cell_pixels,
)


class TestCalculateCellSize:
    """Тесты для функции calculate_cell_size."""

    def test_standard_resolution_640x480(self) -> None:
        """Тест стандартного разрешения 640×480."""
        cell_w, cell_h = calculate_cell_size(640, 480, 24, 18)

        assert cell_w == 26
        assert cell_h == 26
        assert isinstance(cell_w, int)
        assert isinstance(cell_h, int)

    def test_perfect_division_640x480_32x24(self) -> None:
        """Тест идеального деления без остатка."""
        cell_w, cell_h = calculate_cell_size(640, 480, 32, 24)

        assert cell_w == 20
        assert cell_h == 20
        # Проверяем полное покрытие
        assert 32 * 20 == 640
        assert 24 * 20 == 480

    def test_high_resolution_1280x720(self) -> None:
        """Тест HD разрешения 1280×720."""
        cell_w, cell_h = calculate_cell_size(1280, 720, 32, 24)

        assert cell_w == 40
        assert cell_h == 30

    def test_low_resolution_320x240(self) -> None:
        """Тест низкого разрешения 320×240."""
        cell_w, cell_h = calculate_cell_size(320, 240, 16, 12)

        assert cell_w == 20
        assert cell_h == 20

    def test_single_cell(self) -> None:
        """Тест с одной ячейкой."""
        cell_w, cell_h = calculate_cell_size(640, 480, 1, 1)

        assert cell_w == 640
        assert cell_h == 480

    def test_many_cells(self) -> None:
        """Тест с большим количеством ячеек."""
        cell_w, cell_h = calculate_cell_size(640, 480, 64, 48)

        assert cell_w == 10
        assert cell_h == 10


class TestGetCellBounds:
    """Тесты для функции get_cell_bounds."""

    def test_first_cell_top_left(self) -> None:
        """Тест первой ячейки (0, 0)."""
        x1, y1, x2, y2 = get_cell_bounds(0, 0, 26, 26)

        assert x1 == 0
        assert y1 == 0
        assert x2 == 26
        assert y2 == 26

    def test_second_cell_horizontal(self) -> None:
        """Тест второй ячейки по горизонтали (1, 0)."""
        x1, y1, x2, y2 = get_cell_bounds(1, 0, 26, 26)

        assert x1 == 26
        assert y1 == 0
        assert x2 == 52
        assert y2 == 26

    def test_second_cell_vertical(self) -> None:
        """Тест второй ячейки по вертикали (0, 1)."""
        x1, y1, x2, y2 = get_cell_bounds(0, 1, 26, 26)

        assert x1 == 0
        assert y1 == 26
        assert x2 == 26
        assert y2 == 52

    def test_middle_cell(self) -> None:
        """Тест ячейки в середине сетки."""
        x1, y1, x2, y2 = get_cell_bounds(5, 3, 20, 20)

        assert x1 == 100
        assert y1 == 60
        assert x2 == 120
        assert y2 == 80

    def test_last_cell_640x480_24x18(self) -> None:
        """Тест последней ячейки для 640×480 с сеткой 24×18."""
        x1, y1, x2, y2 = get_cell_bounds(23, 17, 26, 26)

        assert x1 == 598  # 23 * 26
        assert y1 == 442  # 17 * 26
        assert x2 == 624  # 24 * 26
        assert y2 == 468  # 18 * 26

    def test_cell_size_consistency(self) -> None:
        """Тест консистентности размеров ячейки."""
        x1, y1, x2, y2 = get_cell_bounds(3, 2, 30, 25)

        width = x2 - x1
        height = y2 - y1

        assert width == 30
        assert height == 25

    def test_non_square_cells(self) -> None:
        """Тест прямоугольных (не квадратных) ячеек."""
        x1, y1, x2, y2 = get_cell_bounds(2, 1, 40, 30)

        assert x1 == 80
        assert y1 == 30
        assert x2 == 120
        assert y2 == 60


class TestGetCellPixels:
    """Тесты для функции get_cell_pixels."""

    def test_extract_pixels_grayscale(self) -> None:
        """Тест извлечения пикселей из grayscale кадра."""
        frame = np.zeros((100, 100), dtype=np.uint8)
        frame[10:20, 10:20] = 255

        pixels = get_cell_pixels(frame, 10, 10, 20, 20)

        assert pixels.shape == (10, 10)
        assert np.all(pixels == 255)

    def test_extract_pixels_rgb(self) -> None:
        """Тест извлечения пикселей из RGB кадра."""
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        frame[20:30, 20:30] = [255, 0, 0]  # Красный квадрат

        pixels = get_cell_pixels(frame, 20, 20, 30, 30)

        assert pixels.shape == (10, 10, 3)
        assert np.all(pixels[:, :, 0] == 255)  # R
        assert np.all(pixels[:, :, 1] == 0)    # G
        assert np.all(pixels[:, :, 2] == 0)    # B

    def test_extract_full_frame(self) -> None:
        """Тест извлечения всего кадра."""
        frame = np.ones((50, 50), dtype=np.uint8) * 128

        pixels = get_cell_pixels(frame, 0, 0, 50, 50)

        assert pixels.shape == (50, 50)
        assert np.all(pixels == 128)

    def test_extract_single_pixel(self) -> None:
        """Тест извлечения одного пикселя."""
        frame = np.arange(100).reshape(10, 10).astype(np.uint8)

        pixels = get_cell_pixels(frame, 5, 5, 6, 6)

        assert pixels.shape == (1, 1)
        assert pixels[0, 0] == frame[5, 5]

    def test_extract_different_sizes(self) -> None:
        """Тест извлечения областей разных размеров."""
        frame = np.random.randint(0, 256, (100, 100), dtype=np.uint8)

        # Маленькая область
        small = get_cell_pixels(frame, 0, 0, 10, 10)
        assert small.shape == (10, 10)

        # Средняя область
        medium = get_cell_pixels(frame, 20, 20, 50, 50)
        assert medium.shape == (30, 30)

        # Большая область
        large = get_cell_pixels(frame, 10, 10, 90, 90)
        assert large.shape == (80, 80)

    def test_pixel_values_preserved(self) -> None:
        """Тест сохранения значений пикселей."""
        frame = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]], dtype=np.uint8)

        pixels = get_cell_pixels(frame, 1, 1, 3, 3)

        expected = np.array([[5, 6], [8, 9]], dtype=np.uint8)
        assert np.array_equal(pixels, expected)


class TestIntegration:
    """Интеграционные тесты для работы всех функций вместе."""

    def test_full_grid_coverage_640x480(self) -> None:
        """Тест полного покрытия кадра 640×480 сеткой 32×24."""
        frame_w, frame_h = 640, 480
        grid_w, grid_h = 32, 24

        cell_w, cell_h = calculate_cell_size(frame_w, frame_h, grid_w, grid_h)

        # Проверяем, что все ячейки помещаются в кадр
        for j in range(grid_h):
            for i in range(grid_w):
                x1, y1, x2, y2 = get_cell_bounds(i, j, cell_w, cell_h)

                assert x1 >= 0
                assert y1 >= 0
                assert x2 <= frame_w
                assert y2 <= frame_h

    def test_no_gaps_between_cells(self) -> None:
        """Тест отсутствия пропусков между ячейками."""
        cell_w, cell_h = 20, 20

        # Проверяем стыковку по горизонтали
        _, _, x2_prev, _ = get_cell_bounds(0, 0, cell_w, cell_h)
        x1_next, _, _, _ = get_cell_bounds(1, 0, cell_w, cell_h)
        assert x2_prev == x1_next

        # Проверяем стыковку по вертикали
        _, _, _, y2_prev = get_cell_bounds(0, 0, cell_w, cell_h)
        _, y1_next, _, _ = get_cell_bounds(0, 1, cell_w, cell_h)
        assert y2_prev == y1_next

    def test_extract_pixels_from_grid_cells(self) -> None:
        """Тест извлечения пикселей из всех ячеек сетки."""
        frame = np.random.randint(0, 256, (480, 640), dtype=np.uint8)
        grid_w, grid_h = 24, 18

        cell_w, cell_h = calculate_cell_size(640, 480, grid_w, grid_h)

        # Проверяем, что можем извлечь пиксели из каждой ячейки
        for j in range(grid_h):
            for i in range(grid_w):
                x1, y1, x2, y2 = get_cell_bounds(i, j, cell_w, cell_h)
                pixels = get_cell_pixels(frame, x1, y1, x2, y2)

                assert pixels.size > 0
                assert pixels.shape[0] == cell_h or (i == grid_w - 1 or j == grid_h - 1)
                assert pixels.shape[1] == cell_w or (i == grid_w - 1 or j == grid_h - 1)
