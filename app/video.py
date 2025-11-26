from __future__ import annotations

import asyncio
import contextlib
import fractions
import logging
import threading
import time
from collections.abc import Awaitable, Callable

import cv2
import numpy as np
from aiortc import MediaStreamTrack, RTCPeerConnection
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


_picam2: Picamera2 | None = None  # type: ignore[name-defined]
_picam2_lock = threading.Lock()
_camera_track: CameraVideoTrack | None = None
_camera_track_users = 0
_camera_track_lock: asyncio.Lock | None = None

CameraReleaseCallback = Callable[[], Awaitable[None]]


def _ensure_picamera2() -> Picamera2:  # type: ignore[override]
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

        # Broadcast mechanism: producer writes to all subscriber queues
        self._subscribers: list[asyncio.Queue[VideoFrame | None]] = []
        self._subscribers_lock = asyncio.Lock()
        self._producer_task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()
        self._latest_frame: VideoFrame | None = None

    async def _produce_frames(self) -> None:
        """Background task that captures frames and broadcasts to all subscribers."""
        try:
            logger.info("Frame producer started")
            while not self._stop_event.is_set():
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
                        # Run blocking read in thread pool to avoid blocking event loop
                        if self._frame_count % 30 == 0:
                            logger.debug(f"Frame {self._frame_count}: calling cv2.VideoCapture.read()")
                        loop = asyncio.get_event_loop()
                        ret, frame = await loop.run_in_executor(None, self._cap.read)
                        if self._frame_count % 30 == 0:
                            logger.debug(f"Frame {self._frame_count}: cv2.VideoCapture.read() returned ret={ret}")
                    if not ret or frame is None:
                        frame = np.zeros(
                            (config.video.height, config.video.width, 3), dtype=np.uint8
                        )
                    else:
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        frame = cv2.resize(
                            frame, (config.video.width, config.video.height)
                        )

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

                # Create VideoFrame (FFmpeg call - must be single-threaded)
                if self._frame_count % 30 == 0:
                    logger.debug(f"Frame {self._frame_count}: creating VideoFrame")
                video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
                video_frame.pts = pts
                video_frame.time_base = time_base
                if self._frame_count % 30 == 0:
                    logger.debug(f"Frame {self._frame_count}: VideoFrame created")

                # Store latest frame for new subscribers
                self._latest_frame = video_frame

                # Broadcast to all subscribers
                async with self._subscribers_lock:
                    subscriber_count = len(self._subscribers)
                    for queue in self._subscribers[:]:  # Copy list to avoid modification during iteration
                        with contextlib.suppress(asyncio.QueueFull):
                            # Skip frame if subscriber queue is full (slow consumer)
                            queue.put_nowait(video_frame)

                if self._frame_count % 30 == 0:  # Log every 30 frames
                    logger.info(
                        f"Produced frame {self._frame_count}, {subscriber_count} subscribers"
                    )

                # Control frame rate
                await asyncio.sleep(1 / config.video.fps)

        except asyncio.CancelledError:
            logger.info("Frame producer task cancelled")
        except Exception as e:
            logger.error(f"Error in frame producer: {e}")
            # Signal all consumers that production has stopped
            async with self._subscribers_lock:
                for queue in self._subscribers:
                    with contextlib.suppress(asyncio.QueueFull):
                        queue.put_nowait(None)

    async def subscribe(self) -> asyncio.Queue[VideoFrame | None]:
        """Create a new subscriber queue for broadcasting frames."""
        queue: asyncio.Queue[VideoFrame | None] = asyncio.Queue(maxsize=2)

        async with self._subscribers_lock:
            self._subscribers.append(queue)
            subscriber_count = len(self._subscribers)

        logger.info(f"New subscriber added, total subscribers: {subscriber_count}")

        # Start producer on first subscriber
        if self._producer_task is None:
            logger.info("Starting frame producer task")
            self._producer_task = asyncio.create_task(self._produce_frames())

        return queue

    async def unsubscribe(self, queue: asyncio.Queue[VideoFrame | None]) -> None:
        """Remove a subscriber queue."""
        async with self._subscribers_lock:
            if queue in self._subscribers:
                self._subscribers.remove(queue)
            subscriber_count = len(self._subscribers)

        logger.info(f"Subscriber removed, remaining subscribers: {subscriber_count}")

    async def recv(self) -> VideoFrame:
        """This method should not be called directly - use BroadcastVideoTrack instead."""
        raise NotImplementedError("Use subscribe() to create broadcast tracks")

    def stop(self) -> None:
        super().stop()

        # Signal producer to stop
        self._stop_event.set()

        # Cancel producer task
        if self._producer_task is not None and not self._producer_task.done():
            self._producer_task.cancel()

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


class BroadcastVideoTrack(MediaStreamTrack):
    """Wrapper track that receives frames from CameraVideoTrack broadcast."""

    kind = "video"

    def __init__(self, source: CameraVideoTrack) -> None:
        super().__init__()
        self._source = source
        self._queue: asyncio.Queue[VideoFrame | None] | None = None
        logger.info(f"BroadcastVideoTrack created: {id(self)}")

    async def recv(self) -> VideoFrame:
        """Receive frame from broadcast queue."""
        if self._queue is None:
            logger.info(f"BroadcastVideoTrack {id(self)}: subscribing to camera")
            self._queue = await self._source.subscribe()

        video_frame = await self._queue.get()

        if video_frame is None:
            logger.error(f"BroadcastVideoTrack {id(self)}: producer stopped")
            raise Exception("Frame producer stopped")

        return video_frame

    def stop(self) -> None:
        super().stop()
        logger.info(f"BroadcastVideoTrack {id(self)}: stopping")
        if self._queue is not None:
            # Unsubscribe from source (async, but we can't await in stop)
            asyncio.create_task(self._source.unsubscribe(self._queue))


async def _get_camera_track_lock() -> asyncio.Lock:
    """Return a global lock instance for camera track lifecycle operations."""

    global _camera_track_lock
    if _camera_track_lock is None:
        _camera_track_lock = asyncio.Lock()
    return _camera_track_lock


async def _acquire_camera_track() -> CameraVideoTrack:
    """Return a shared camera track, creating it if necessary."""

    global _camera_track, _camera_track_users
    lock = await _get_camera_track_lock()
    async with lock:
        if (
            _camera_track is None
            or getattr(_camera_track, "readyState", "ended") == "ended"
        ):
            logger.info("Creating shared CameraVideoTrack")
            _camera_track = CameraVideoTrack()
            logger.info(f"CameraVideoTrack created: {id(_camera_track)}")

        _camera_track_users += 1
        logger.info(f"Camera track acquired, users: {_camera_track_users}")
        return _camera_track


async def _release_camera_track() -> None:
    """Decrease the number of consumers and stop the track when unused."""

    global _camera_track, _camera_track_users
    lock = await _get_camera_track_lock()
    async with lock:
        if _camera_track_users > 0:
            _camera_track_users -= 1
            logger.info(f"Camera track released, remaining users: {_camera_track_users}")

        if _camera_track_users == 0 and _camera_track is not None:
            logger.info("Stopping shared CameraVideoTrack (no users left)")
            _camera_track.stop()
            _camera_track = None


async def create_peer_connection() -> tuple[RTCPeerConnection, CameraReleaseCallback]:
    """Create RTCPeerConnection with a broadcast video track."""

    logger.info("Creating new peer connection")
    pc = RTCPeerConnection()

    camera_track = await _acquire_camera_track()

    # Create a broadcast wrapper track for this client
    broadcast_track = BroadcastVideoTrack(camera_track)
    pc.addTrack(broadcast_track)
    logger.info(f"Broadcast track added to peer connection: {id(pc)}")

    release_lock = asyncio.Lock()
    released = False

    async def release_camera() -> None:
        """Ensure the shared track is released exactly once per peer."""

        nonlocal released
        async with release_lock:
            if released:
                logger.warning(f"Peer {id(pc)}: release_camera called twice (ignored)")
                return
            released = True

        logger.info(f"Peer {id(pc)}: releasing camera resources")
        # Stop the broadcast track
        broadcast_track.stop()

        # Release the shared camera track
        await _release_camera_track()

    return pc, release_camera
