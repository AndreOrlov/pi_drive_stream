"""OpenCV рендерер для OSD."""

import numpy as np

from app.overlay.base import Layer


class CvOverlayRenderer:
    """
    Рендерер OSD на основе OpenCV.

    Управляет отрисовкой всех слоёв на кадре с использованием OpenCV.
    """

    def __init__(self, layers: list[Layer]) -> None:
        """
        Инициализация рендерера.

        Args:
            layers: Список слоёв для отрисовки
        """
        self.layers = layers

    def draw(self, frame: np.ndarray) -> None:
        """
        Отрисовать все активные слои на кадре.

        Args:
            frame: Кадр в формате RGB (numpy array), модифицируется на месте
        """
        for layer in self.layers:
            if layer.enabled:
                layer.render(frame)



