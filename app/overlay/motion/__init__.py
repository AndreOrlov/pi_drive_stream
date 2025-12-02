"""Модуль детекторов движения."""

from app.overlay.motion.base import BaseMotionDetector
from app.overlay.motion.frame_diff_detector import FrameDiffDetector
from app.overlay.motion.grid_mean_detector import GridMeanDetector
from app.overlay.motion.grid_rms_detector import GridRMSDetector
from app.overlay.motion.grid_utils import (
    calculate_cell_size,
    get_cell_bounds,
    get_cell_pixels,
)
from app.overlay.motion.performance import PerformanceOptimizedDetector

__all__ = [
    "calculate_cell_size",
    "get_cell_bounds",
    "get_cell_pixels",
    "BaseMotionDetector",
    "GridMeanDetector",
    "GridRMSDetector",
    "FrameDiffDetector",
    "PerformanceOptimizedDetector",
]
