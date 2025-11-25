import asyncio
import fractions
import logging
import threading
import time
from typing import Optional

import cv2
import numpy as np
from aiortc import MediaStreamTrack, RTCPeerConnection
from aiortc.contrib.media import MediaRelay
from av import VideoFrame

from app.config import config
from app.overlay import CvOverlayRenderer
from app.overlay.base import Layer
from app.overlay.layers import CrosshairLayer, TelemetryLayer, WarningLayer

logger = logging.getLogger(__name__)

try:
    import libcamera  # type: ignore[import-not-found]
    from picamera2 import Picamera2  # type: ignore[import-not-found]

    PICAMERA2_AVAILABLE = True
except ImportError:  # pragma: no cover - not available on non-RPi dev machines
    Picamera2 = None  # type: ignore[assignment]
    PICAMERA2_AVAILABLE = False


_picam2: Optional["Picamera2"] = None  # type: ignore[name-defined]
_picam2_lock = threading.Lock()
_relay: MediaRelay | None = None


def _ensure_picamera2() -> "Picamera2":  # type: ignore[override]
    """
    Create and start a single global Picamera2 instance.
    Subsequent callers reuse the same instance to avoid 'Device or resource busy'.
    """
    global _picam2

    if not PICAMERA2_AVAILABLE or Picamera2 is None:  # type: ignore[comparison-overlap]
        raise RuntimeError("Picamera2 is not available in this environment")

    with _picam2_lock:
        if _picam2 is None:
            logger.info("Initializing global Picamera2 instance")
            cam = Picamera2()  # type: ignore[call-arg]

            # Применяем трансформации из конфига
            cam_config = cam.create_preview_configuration(
                main={
                    "format": "RGB888",
                    "size": (config.video.width, config.video.height),
                },
                transform=libcamera.Transform(
                    hflip=int(config.video.flip_horizontal),
                    vflip=int(config.video.flip_vertical),
                ),
            )
            cam.configure(cam_config)
            cam.start()
            _picam2 = cam

        return _picam2


class CameraVideoTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self) -> None:
        super().__init__()
        self._lock = asyncio.Lock()
        self._counter = 0
        self._start_time: float | None = None

        self._use_picamera2 = False
        self._picam2: Picamera2 | None = None  # type: ignore[name-defined]
        self._cap: cv2.VideoCapture | None = None

        if PICAMERA2_AVAILABLE and config.video.use_picamera2:
            try:
                self._picam2 = _ensure_picamera2()
                self._use_picamera2 = True
            except Exception as exc:  # pragma: no cover - runtime-only on RPi
                logger.error(
                    "Failed to initialize Picamera2, falling back to OpenCV: %s", exc
                )

        if not self._use_picamera2:
            self._cap = cv2.VideoCapture(config.video.camera_index)
            if not self._cap.isOpened():
                logger.error(
                    "Failed to open camera at index %s", config.video.camera_index
                )
        self._frame_count = 0

        # Инициализация OSD рендерера
        self._overlay_renderer: CvOverlayRenderer | None = None
        if config.overlay.enabled:
            layers: list[Layer] = []
            if config.overlay.crosshair:
                layers.append(CrosshairLayer())
            if config.overlay.telemetry:
                layers.append(TelemetryLayer())
            if config.overlay.warnings:
                layers.append(WarningLayer())

            if layers:
                self._overlay_renderer = CvOverlayRenderer(layers)
                logger.info("OSD renderer initialized with %d layers", len(layers))

    async def recv(self) -> VideoFrame:
        try:
            # Засекаем время начала обработки кадра
            loop_start = time.time()

            # Initialize start time on first frame
            if self._start_time is None:
                self._start_time = loop_start

            # Calculate timestamp based on elapsed time
            elapsed = loop_start - self._start_time
            pts = int(elapsed * config.video.pts_clock_hz)
            time_base = fractions.Fraction(1, config.video.pts_clock_hz)

            self._frame_count += 1

            # Capture frame
            if self._use_picamera2 and self._picam2 is not None:
                frame = self._picam2.capture_array()
            else:
                ret, frame = (False, None)
                if self._cap is not None:
                    ret, frame = self._cap.read()
                if not ret or frame is None:
                    frame = np.zeros(
                        (config.video.height, config.video.width, 3), dtype=np.uint8
                    )
                else:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame = cv2.resize(frame, (config.video.width, config.video.height))

                    # Применяем трансформации для OpenCV
                    if config.video.flip_horizontal and config.video.flip_vertical:
                        frame = cv2.flip(frame, -1)  # оба направления
                    elif config.video.flip_vertical:
                        frame = cv2.flip(frame, 0)  # только вертикально
                    elif config.video.flip_horizontal:
                        frame = cv2.flip(frame, 1)  # только горизонтально

            # Отрисовка OSD
            if self._overlay_renderer is not None:
                self._overlay_renderer.draw(frame)

            # Create VideoFrame
            video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
            video_frame.pts = pts
            video_frame.time_base = time_base

            # Динамическое ограничение FPS: спим только оставшееся время
            frame_duration = time.time() - loop_start
            target_period = 1.0 / config.video.fps
            sleep_time = max(0, target_period - frame_duration)

            # Логируем если обработка превысила целевой период (каждые 100 кадров)
            if self._frame_count % 100 == 0 and frame_duration > target_period:
                logger.warning(
                    "Frame processing too slow: %.1f ms (target: %.1f ms, FPS: %.1f)",
                    frame_duration * 1000,
                    target_period * 1000,
                    1.0 / frame_duration if frame_duration > 0 else 0,
                )

            await asyncio.sleep(sleep_time)

            return video_frame
        except Exception as e:
            logger.error(f"Error in CameraVideoTrack.recv: {e}")
            raise

    def stop(self) -> None:
        super().stop()
        if self._use_picamera2 and self._picam2 is not None:
            logger.info("Stopping Picamera2")
            try:
                self._picam2.stop()
                self._picam2.close()
            except Exception as exc:  # pragma: no cover - best effort
                logger.error("Error stopping Picamera2: %s", exc)
        elif self._cap is not None and self._cap.isOpened():
            logger.info("Releasing OpenCV VideoCapture")
            self._cap.release()


async def create_peer_connection() -> RTCPeerConnection:
    """Create RTCPeerConnection with camera video track"""
    global _relay

    if _relay is None:
        _relay = MediaRelay()

    pc = RTCPeerConnection()

    # Create camera track
    camera_track = CameraVideoTrack()

    # Use MediaRelay to handle the track
    video_track = _relay.subscribe(camera_track)
    pc.addTrack(video_track)

    return pc
