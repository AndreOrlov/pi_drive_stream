import asyncio
import fractions
import logging
import threading
import time
from typing import Optional

import cv2
import numpy as np
from aiortc import MediaStreamTrack, RTCPeerConnection
from av import VideoFrame

from app.config import config
from app.overlay import CvOverlayRenderer
from app.overlay.base import Layer
from app.overlay.plugin_loader import discover_plugins

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
_global_camera_track: Optional["CameraVideoTrack"] = None
_track_lock = threading.Lock()


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


def _ensure_camera_track() -> "CameraVideoTrack":
    """
    Create single global camera track for all connections.
    Ensures one VideoCapture/Picamera2 instance.
    """
    global _global_camera_track

    with _track_lock:
        if _global_camera_track is None:
            logger.info("Creating global camera track (single producer)")
            _global_camera_track = CameraVideoTrack()
        return _global_camera_track


class CameraVideoTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self) -> None:
        super().__init__()
        self._start_time: float | None = None
        self._frame_count = 0

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

        # Инициализация OSD рендерера с плагинами
        self._overlay_renderer: CvOverlayRenderer | None = None
        if config.overlay.enabled:
            # Обнаруживаем все доступные плагины
            available_plugins = discover_plugins()
            logger.info("Discovered %d overlay plugins", len(available_plugins))

            layers: list[Layer] = []

            # Создаём слои на основе конфигурации
            for plugin_name, plugin_config in config.overlay.plugins.items():
                if not plugin_config.get("enabled", False):
                    continue

                plugin_cls = available_plugins.get(plugin_name)
                if plugin_cls is None:
                    logger.warning("Plugin '%s' not found, skipping", plugin_name)
                    continue

                # Извлекаем параметры для создания плагина
                params = {
                    k: v
                    for k, v in plugin_config.items()
                    if k not in ("enabled", "priority")
                }

                try:
                    # Создаём экземпляр плагина
                    layer = plugin_cls(**params)

                    # Переопределяем priority если указан в конфиге
                    if "priority" in plugin_config:
                        layer.priority = plugin_config["priority"]

                    layers.append(layer)
                    logger.info(
                        "Loaded plugin '%s' with priority %d",
                        plugin_name,
                        layer.priority,
                    )
                except Exception as e:
                    logger.error("Failed to initialize plugin '%s': %s", plugin_name, e)

            if layers:
                self._overlay_renderer = CvOverlayRenderer(layers)
                logger.info("OSD renderer initialized with %d layers", len(layers))

    async def recv(self) -> VideoFrame:
        try:
            # Initialize start time on first frame
            if self._start_time is None:
                self._start_time = time.time()

            # Calculate timestamp based on elapsed time
            elapsed = time.time() - self._start_time
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

            # Control frame rate
            await asyncio.sleep(1 / config.video.fps)

            return video_frame
        except Exception as e:
            logger.error(f"Error in CameraVideoTrack.recv: {e}")
            raise

    def stop(self) -> None:
        """
        Stop track but don't release camera - it's global and reused.
        Camera will be released on application shutdown.
        """
        super().stop()
        logger.info("Track stopped (camera remains active)")


class VideoRelayTrack(MediaStreamTrack):
    """
    Relay track that forwards frames from camera_track to peer connection.
    Each peer connection gets its own VideoRelayTrack instance.
    """

    kind = "video"

    def __init__(self, camera_track: CameraVideoTrack) -> None:
        super().__init__()
        self._camera_track = camera_track

    async def recv(self) -> VideoFrame:
        """Forward frame from camera track."""
        return await self._camera_track.recv()


async def create_peer_connection() -> RTCPeerConnection:
    """
    Create RTCPeerConnection with video relay track.
    Each peer gets its own VideoRelayTrack that reads from global CameraVideoTrack.
    """
    pc = RTCPeerConnection()

    # Get global camera track (creates if doesn't exist)
    camera_track = _ensure_camera_track()

    # Create relay track for this peer
    relay_track = VideoRelayTrack(camera_track)
    pc.addTrack(relay_track)

    logger.info("Created peer connection with video relay track")
    return pc


def cleanup_camera() -> None:
    """Cleanup camera resources on shutdown."""
    global _global_camera_track

    if _global_camera_track is not None:
        logger.info("Stopping global camera track")
        if _global_camera_track._cap is not None:
            _global_camera_track._cap.release()
        if _global_camera_track._picam2 is not None:
            try:
                _global_camera_track._picam2.stop()
                _global_camera_track._picam2.close()
            except Exception as exc:
                logger.error("Error stopping Picamera2: %s", exc)
