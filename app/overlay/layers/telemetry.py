"""Слой с телеметрией (дата/время)."""

from datetime import datetime

import cv2
import numpy as np

from app.overlay.layers.base import Layer
from app.overlay.plugin_registry import register_layer


@register_layer("telemetry")
class TelemetryLayer(Layer):
    """
    Слой с телеметрией.

    Отображает текущую дату и время.
    """

    def __init__(
        self,
        enabled: bool = True,
        position: tuple[int, int] = (10, 30),
        font_scale: float = 0.7,
        color: tuple[int, int, int] = (255, 255, 255),
        outline_color: tuple[int, int, int] = (0, 0, 0),
        thickness: int = 2,
        outline_thickness: int = 4,
    ) -> None:
        """
        Инициализация слоя телеметрии.

        Args:
            enabled: Включён ли слой
            position: Позиция текста (x, y) от левого верхнего угла
            font_scale: Размер шрифта
            color: Цвет текста (RGB)
            outline_color: Цвет обводки (RGB)
            thickness: Толщина текста
            outline_thickness: Толщина обводки
        """
        super().__init__(enabled, priority=Layer.PRIORITY_HUD)
        self.position = position
        self.font_scale = font_scale
        self.color = color
        self.outline_color = outline_color
        self.thickness = thickness
        self.outline_thickness = outline_thickness
        self.font = cv2.FONT_HERSHEY_SIMPLEX

    def render(self, frame: np.ndarray) -> None:
        """
        Отрисовать телеметрию на кадре.

        Args:
            frame: Кадр в формате RGB
        """
        # Получаем текущую дату и время
        now = datetime.now()
        text = now.strftime("%d.%m.%Y %H:%M:%S")

        # Рисуем обводку (чёрную, толще)
        cv2.putText(
            frame,
            text,
            self.position,
            self.font,
            self.font_scale,
            self.outline_color,
            self.outline_thickness,
            cv2.LINE_AA,
        )

        # Рисуем основной текст (белый, тоньше)
        cv2.putText(
            frame,
            text,
            self.position,
            self.font,
            self.font_scale,
            self.color,
            self.thickness,
            cv2.LINE_AA,
        )
