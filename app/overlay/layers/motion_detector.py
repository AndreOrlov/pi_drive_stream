"""Слой детектора движения."""

import cv2
import numpy as np

from app.overlay.layers.base import Layer
from app.overlay.motion.grid_utils import calculate_cell_size, get_cell_bounds
from app.overlay.plugin_registry import register_layer


@register_layer("motion_detector")
class MotionDetectorLayer(Layer):
    """
    Слой детектора движения с визуализацией сетки.

    ЭТАП 1: Отрисовка сетки для проверки разбиения кадра на ячейки.
    """

    def __init__(
        self,
        enabled: bool = True,
        # Параметры сетки
        grid_width: int = 24,
        grid_height: int = 18,
        # Визуализация сетки
        show_grid_lines: bool = True,
        grid_line_color: tuple[int, int, int] = (0, 255, 0),
        grid_line_thickness: int = 1,
        show_cell_info: bool = True,
        # Информация на экране
        show_stats: bool = True,
    ) -> None:
        """
        Инициализация слоя детектора движения.

        Args:
            enabled: Включён ли слой
            grid_width: Количество столбцов сетки
            grid_height: Количество строк сетки
            show_grid_lines: Показывать линии сетки
            grid_line_color: Цвет линий сетки (RGB)
            grid_line_thickness: Толщина линий сетки
            show_cell_info: Показывать номера ячеек (для отладки)
            show_stats: Показывать информацию о сетке
        """
        super().__init__(enabled, priority=Layer.PRIORITY_BACKGROUND)

        # Параметры сетки
        self.grid_width = grid_width
        self.grid_height = grid_height

        # Визуализация
        self.show_grid_lines = show_grid_lines
        self.grid_line_color = grid_line_color
        self.grid_line_thickness = grid_line_thickness
        self.show_cell_info = show_cell_info
        self.show_stats = show_stats

        self.font = cv2.FONT_HERSHEY_SIMPLEX

    def render(self, frame: np.ndarray) -> None:
        """
        Отрисовать сетку на кадре.

        Args:
            frame: Кадр в формате RGB
        """
        if not self.show_grid_lines:
            return

        height, width = frame.shape[:2]
        cell_w, cell_h = calculate_cell_size(width, height, self.grid_width, self.grid_height)

        # Рисуем рамку сетки (границы кадра)
        cv2.rectangle(
            frame,
            (0, 0),
            (width - 1, height - 1),
            self.grid_line_color,
            self.grid_line_thickness,
            cv2.LINE_AA,
        )

        # Рисуем вертикальные линии с антиалиасингом
        for i in range(1, self.grid_width):
            x = i * cell_w
            cv2.line(
                frame,
                (x, 0),
                (x, height),
                self.grid_line_color,
                self.grid_line_thickness,
                cv2.LINE_AA,  # Антиалиасинг для гладких линий
            )

        # Рисуем горизонтальные линии с антиалиасингом
        for j in range(1, self.grid_height):
            y = j * cell_h
            cv2.line(
                frame,
                (0, y),
                (width, y),
                self.grid_line_color,
                self.grid_line_thickness,
                cv2.LINE_AA,  # Антиалиасинг для гладких линий
            )

        # Опционально: показать номера ячеек (для отладки)
        if self.show_cell_info:
            self._draw_cell_numbers(frame, cell_w, cell_h)

        # Статистика
        if self.show_stats:
            self._draw_stats(frame, cell_w, cell_h)

    def _draw_cell_numbers(
        self,
        frame: np.ndarray,
        cell_w: int,
        cell_h: int,
    ) -> None:
        """
        Нарисовать номера ячеек (для отладки).

        Args:
            frame: Кадр для отрисовки
            cell_w: Ширина ячейки в пикселях
            cell_h: Высота ячейки в пикселях
        """
        font_scale = 0.3
        thickness = 1
        color = (255, 255, 255)  # Белый

        # Рисуем номера только в первых нескольких ячейках
        for j in range(min(3, self.grid_height)):
            for i in range(min(4, self.grid_width)):
                x = int(i * cell_w + 5)
                y = int(j * cell_h + 15)
                cv2.putText(
                    frame,
                    f"{i},{j}",
                    (x, y),
                    self.font,
                    font_scale,
                    color,
                    thickness,
                    cv2.LINE_AA,
                )

    def _draw_stats(
        self,
        frame: np.ndarray,
        cell_w: int,
        cell_h: int,
    ) -> None:
        """
        Отрисовать информацию о сетке.

        Args:
            frame: Кадр для отрисовки
            cell_w: Ширина ячейки в пикселях
            cell_h: Высота ячейки в пикселях
        """
        height, width = frame.shape[:2]
        total_cells = self.grid_width * self.grid_height

        lines = [
            "Motion Detection - STAGE 1",
            f"Grid: {self.grid_width}x{self.grid_height} ({total_cells} cells)",
            f"Cell size: {cell_w}x{cell_h}px",
            f"Frame: {width}x{height}px",
        ]

        # Параметры текста
        font_scale = 0.45
        thickness = 1
        line_height = 18
        padding = 10

        # Вычисляем размер фона
        max_width = max(
            cv2.getTextSize(line, self.font, font_scale, thickness)[0][0]
            for line in lines
        )

        box_height = len(lines) * line_height + padding * 2

        # Полупрозрачный фон
        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (8, 8),
            (max_width + padding * 2, box_height),
            (0, 0, 0),
            -1,
        )
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        # Рамка
        cv2.rectangle(
            frame,
            (8, 8),
            (max_width + padding * 2, box_height),
            self.grid_line_color,
            1,
        )

        # Текст
        for idx, line in enumerate(lines):
            y = 8 + padding + (idx + 1) * line_height - 5
            color = self.grid_line_color if idx == 0 else (255, 255, 255)
            cv2.putText(
                frame,
                line,
                (8 + padding, y),
                self.font,
                font_scale,
                color,
                thickness,
                cv2.LINE_AA,
            )
