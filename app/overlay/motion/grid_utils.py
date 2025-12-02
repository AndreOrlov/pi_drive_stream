"""Утилиты для работы с сеткой детекции движения."""

import numpy as np


def calculate_cell_size(
    frame_width: int,
    frame_height: int,
    grid_width: int,
    grid_height: int,
) -> tuple[float, float]:
    """
    Вычислить размер одной ячейки сетки в пикселях.

    Args:
        frame_width: Ширина кадра в пикселях
        frame_height: Высота кадра в пикселях
        grid_width: Количество столбцов сетки
        grid_height: Количество строк сетки

    Returns:
        Кортеж (cell_width, cell_height) - размеры ячейки в пикселях

    Example:
        >>> calculate_cell_size(640, 480, 24, 18)
        (26.666666666666668, 26.666666666666668)
    """
    cell_width = frame_width / grid_width
    cell_height = frame_height / grid_height
    return cell_width, cell_height


def get_cell_bounds(
    i: int,
    j: int,
    cell_width: float,
    cell_height: float,
) -> tuple[int, int, int, int]:
    """
    Получить границы ячейки в пикселях.

    Args:
        i: Индекс столбца (0-based, слева направо)
        j: Индекс строки (0-based, сверху вниз)
        cell_width: Ширина ячейки в пикселях
        cell_height: Высота ячейки в пикселях

    Returns:
        Кортеж (x1, y1, x2, y2) - координаты левого верхнего и правого нижнего углов

    Example:
        >>> get_cell_bounds(0, 0, 26.67, 26.67)
        (0, 0, 26, 26)
        >>> get_cell_bounds(1, 0, 26.67, 26.67)
        (26, 0, 53, 26)
    """
    x1 = int(i * cell_width)
    y1 = int(j * cell_height)
    x2 = int((i + 1) * cell_width)
    y2 = int((j + 1) * cell_height)
    return x1, y1, x2, y2


def get_cell_pixels(
    frame: np.ndarray,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
) -> np.ndarray:
    """
    Извлечь пиксели ячейки из кадра.

    Args:
        frame: Кадр (grayscale или RGB)
        x1: Левая граница ячейки
        y1: Верхняя граница ячейки
        x2: Правая граница ячейки
        y2: Нижняя граница ячейки

    Returns:
        Массив пикселей ячейки

    Example:
        >>> frame = np.zeros((480, 640), dtype=np.uint8)
        >>> pixels = get_cell_pixels(frame, 0, 0, 26, 26)
        >>> pixels.shape
        (26, 26)
    """
    return frame[y1:y2, x1:x2]
