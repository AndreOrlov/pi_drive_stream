"""Слой с прицелом (перекрестие)."""

import cv2
import numpy as np

from app.overlay.layers.base import Layer


class CrosshairLayer(Layer):
    """
    Слой с прицелом в центре кадра.

    Рисует простое перекрестие для прицеливания.
    """

    def __init__(
        self,
        enabled: bool = True,
        size: int = 20,
        thickness: int = 2,
        color: tuple[int, int, int] = (255, 255, 255),
        outline_color: tuple[int, int, int] = (0, 0, 0),
        outline_thickness: int = 4,
    ) -> None:
        """
        Инициализация слоя прицела.

        Args:
            enabled: Включён ли слой
            size: Размер прицела (длина линий от центра)
            thickness: Толщина линий
            color: Цвет прицела (RGB)
            outline_color: Цвет обводки (RGB)
            outline_thickness: Толщина обводки
        """
        super().__init__(enabled)
        self.size = size
        self.thickness = thickness
        self.color = color
        self.outline_color = outline_color
        self.outline_thickness = outline_thickness

    def render(self, frame: np.ndarray) -> None:
        """
        Отрисовать прицел в центре кадра.

        Args:
            frame: Кадр в формате RGB
        """
        height, width = frame.shape[:2]
        center_x = width // 2
        center_y = height // 2

        # Горизонтальная линия
        h_start = (center_x - self.size, center_y)
        h_end = (center_x + self.size, center_y)

        # Вертикальная линия
        v_start = (center_x, center_y - self.size)
        v_end = (center_x, center_y + self.size)

        # Рисуем обводку (чёрную, толще)
        cv2.line(
            frame,
            h_start,
            h_end,
            self.outline_color,
            self.outline_thickness,
            cv2.LINE_AA,
        )
        cv2.line(
            frame,
            v_start,
            v_end,
            self.outline_color,
            self.outline_thickness,
            cv2.LINE_AA,
        )

        # Рисуем основные линии (белые, тоньше)
        cv2.line(frame, h_start, h_end, self.color, self.thickness, cv2.LINE_AA)
        cv2.line(frame, v_start, v_end, self.color, self.thickness, cv2.LINE_AA)

        # Центральная точка
        cv2.circle(frame, (center_x, center_y), 3, self.outline_color, -1, cv2.LINE_AA)
        cv2.circle(frame, (center_x, center_y), 2, self.color, -1, cv2.LINE_AA)
