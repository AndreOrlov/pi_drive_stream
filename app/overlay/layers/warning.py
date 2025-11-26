"""Слой с предупреждениями."""

import cv2
import numpy as np

from app.overlay.layers.base import Layer


class WarningLayer(Layer):
    """
    Слой с предупреждениями.

    Отображает предупреждающие сообщения в верхней части экрана.
    """

    def __init__(
        self,
        enabled: bool = True,
        warning_text: str = "LOW BATTERY",
        font_scale: float = 0.8,
        color: tuple[int, int, int] = (0, 0, 255),  # Красный в RGB
        outline_color: tuple[int, int, int] = (0, 0, 0),
        thickness: int = 2,
        outline_thickness: int = 4,
    ) -> None:
        """
        Инициализация слоя предупреждений.

        Args:
            enabled: Включён ли слой
            warning_text: Текст предупреждения (замокированный)
            font_scale: Размер шрифта
            color: Цвет текста (RGB)
            outline_color: Цвет обводки (RGB)
            thickness: Толщина текста
            outline_thickness: Толщина обводки
        """
        super().__init__(enabled)
        self.warning_text = warning_text
        self.font_scale = font_scale
        self.color = color
        self.outline_color = outline_color
        self.thickness = thickness
        self.outline_thickness = outline_thickness
        self.font = cv2.FONT_HERSHEY_SIMPLEX

    def render(self, frame: np.ndarray) -> None:
        """
        Отрисовать предупреждение на кадре.

        Args:
            frame: Кадр в формате RGB
        """
        height, width = frame.shape[:2]

        # Получаем размер текста для центрирования
        (text_width, text_height), baseline = cv2.getTextSize(
            self.warning_text,
            self.font,
            self.font_scale,
            self.thickness,
        )

        # Позиция: центр по горизонтали, верхняя часть экрана
        x = (width - text_width) // 2
        y = 60

        # Рисуем обводку (чёрную, толще)
        cv2.putText(
            frame,
            self.warning_text,
            (x, y),
            self.font,
            self.font_scale,
            self.outline_color,
            self.outline_thickness,
            cv2.LINE_AA,
        )

        # Рисуем основной текст (красный, тоньше)
        cv2.putText(
            frame,
            self.warning_text,
            (x, y),
            self.font,
            self.font_scale,
            self.color,
            self.thickness,
            cv2.LINE_AA,
        )



