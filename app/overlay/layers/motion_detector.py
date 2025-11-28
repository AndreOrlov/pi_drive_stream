"""Слой детектора движения."""

import cv2
import numpy as np

from app.overlay.layers.base import Layer
from app.overlay.plugin_registry import register_layer


@register_layer("motion_detector")
class MotionDetectorLayer(Layer):
    """
    Слой детектора движения.

    Детектирует движение в кадре и отображает области с движением
    в виде прямоугольников.

    TODO: Реализовать детекцию движения с использованием:
    - cv2.absdiff() для вычисления разницы между кадрами
    - cv2.threshold() для бинаризации
    - cv2.findContours() для поиска областей движения
    - cv2.boundingRect() для получения координат прямоугольников
    """

    def __init__(
        self,
        enabled: bool = True,
        sensitivity: int = 30,
        min_area: int = 500,
        box_color: tuple[int, int, int] = (0, 255, 0),
        box_thickness: int = 2,
    ) -> None:
        """
        Инициализация слоя детектора движения.

        Args:
            enabled: Включён ли слой
            sensitivity: Чувствительность детекции (порог для threshold)
            min_area: Минимальная площадь области для детекции
            box_color: Цвет рамок вокруг областей движения (RGB)
            box_thickness: Толщина рамок
        """
        super().__init__(enabled, priority=Layer.PRIORITY_BACKGROUND)
        self.sensitivity = sensitivity
        self.min_area = min_area
        self.box_color = box_color
        self.box_thickness = box_thickness
        self.font = cv2.FONT_HERSHEY_SIMPLEX

    def render(self, frame: np.ndarray) -> None:
        """
        Отрисовать детектор движения на кадре (заглушка).

        Args:
            frame: Кадр в формате RGB
        """
        # Заглушка: рисуем текст в правом верхнем углу
        text = "Motion Detector (stub)"
        font_scale = 0.5
        thickness = 1
        color = (0, 255, 0)  # Зелёный

        # Получаем размер текста
        (text_width, text_height), baseline = cv2.getTextSize(
            text, self.font, font_scale, thickness
        )

        height, width = frame.shape[:2]
        x = width - text_width - 10
        y = text_height + 10

        # Рисуем текст
        cv2.putText(
            frame,
            text,
            (x, y),
            self.font,
            font_scale,
            color,
            thickness,
            cv2.LINE_AA,
        )
