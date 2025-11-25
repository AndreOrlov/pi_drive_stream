"""OSD (On-Screen Display) система для наложения графики на видеопоток."""

from app.overlay.base import Layer, OverlayRenderer
from app.overlay.cv_renderer import CvOverlayRenderer

__all__ = ["Layer", "OverlayRenderer", "CvOverlayRenderer"]
