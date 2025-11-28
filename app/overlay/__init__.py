"""OSD (On-Screen Display) система для наложения графики на видеопоток."""

from app.overlay.base import Layer, OverlayRenderer
from app.overlay.cv_renderer import CvOverlayRenderer
from app.overlay.plugin_loader import discover_plugins
from app.overlay.plugin_registry import get_plugin, list_plugins, register_layer

__all__ = [
    "Layer",
    "OverlayRenderer",
    "CvOverlayRenderer",
    "discover_plugins",
    "get_plugin",
    "list_plugins",
    "register_layer",
]
