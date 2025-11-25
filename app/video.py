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

logger = logging.getLogger(__name__)

try:
    from picamera2 import Picamera2, Transform  # type: ignore[import-not-found]

    PICAMERA2_AVAILABLE = True
    print("[VIDEO MODULE] Picamera2 imported successfully")
except ImportError:  # pragma: no cover - not available on non-RPi dev machines
    Picamera2 = None  # type: ignore[assignment]
    Transform = None  # type: ignore[assignment]
    PICAMERA2_AVAILABLE = False
    print("[VIDEO MODULE] Picamera2 not available, will use OpenCV")


_picam2: Optional["Picamera2"] = None  # type: ignore[name-defined]
_picam2_lock = threading.Lock()
_relay: Optional[MediaRelay] = None


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
            print("[VIDEO] Initializing global Picamera2 instance")
            logger.info("Initializing global Picamera2 instance")
            cam = Picamera2()  # type: ignore[call-arg]

            # Применяем трансформации из конфига
            config_params = {
                "main": {"format": "RGB888", "size": (config.video.width, config.video.height)}
            }

            # Добавляем transform только если он доступен и нужен
            if Transform is not None and (config.video.flip_horizontal or config.video.flip_vertical):
                print(f"[VIDEO] Applying transform: hflip={config.video.flip_horizontal}, vflip={config.video.flip_vertical}")
                logger.info(f"Applying transform: hflip={config.video.flip_horizontal}, vflip={config.video.flip_vertical}")
                transform = Transform(
                    hflip=config.video.flip_horizontal,
                    vflip=config.video.flip_vertical
                )
                config_params["transform"] = transform

            print(f"[VIDEO] Creating camera configuration")
            logger.info(f"Creating camera configuration with params: {config_params}")
            cam_config = cam.create_preview_configuration(**config_params)
            cam.configure(cam_config)
            print("[VIDEO] Starting camera...")
            logger.info("Starting camera...")
            cam.start()
            _picam2 = cam
            print("[VIDEO] Picamera2 started successfully")
            logger.info("Picamera2 started successfully")
        else:
            print("[VIDEO] Reusing existing Picamera2 instance")
            logger.info("Reusing existing Picamera2 instance")

        return _picam2


class CameraVideoTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self) -> None:
        super().__init__()
        print(f"[VIDEO] CameraVideoTrack.__init__() called. PICAMERA2_AVAILABLE={PICAMERA2_AVAILABLE}, use_picamera2={config.video.use_picamera2}")
        self._lock = asyncio.Lock()
        self._counter = 0
        self._start_time = None

        self._use_picamera2 = False
        self._picam2: Optional["Picamera2"] = None  # type: ignore[name-defined]
        self._cap: Optional[cv2.VideoCapture] = None

        if PICAMERA2_AVAILABLE and config.video.use_picamera2:
            try:
                print("[VIDEO] Attempting to initialize Picamera2...")
                logger.info("Attempting to initialize Picamera2...")
                self._picam2 = _ensure_picamera2()
                self._use_picamera2 = True
                print("[VIDEO] Picamera2 initialized successfully")
                logger.info("Picamera2 initialized successfully")
            except Exception as exc:  # pragma: no cover - runtime-only on RPi
                print(f"[VIDEO] Failed to initialize Picamera2: {exc}")
                logger.error("Failed to initialize Picamera2, falling back to OpenCV: %s", exc)
                import traceback
                traceback.print_exc()
                logger.error(traceback.format_exc())

        if not self._use_picamera2:
            print("[VIDEO] Using OpenCV VideoCapture as fallback")
            logger.info("Using OpenCV VideoCapture as fallback")
            self._cap = cv2.VideoCapture(config.video.camera_index)
            if not self._cap.isOpened():
                print(f"[VIDEO] Failed to open camera at index {config.video.camera_index}")
                logger.error("Failed to open camera at index %s", config.video.camera_index)
        self._frame_count = 0

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
                    frame = np.zeros((config.video.height, config.video.width, 3), dtype=np.uint8)
                else:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame = cv2.resize(frame, (config.video.width, config.video.height))

                    # Применяем трансформации для OpenCV
                    if config.video.flip_horizontal and config.video.flip_vertical:
                        frame = cv2.flip(frame, -1)  # оба направления
                    elif config.video.flip_vertical:
                        frame = cv2.flip(frame, 0)   # только вертикально
                    elif config.video.flip_horizontal:
                        frame = cv2.flip(frame, 1)   # только горизонтально

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
    print("[VIDEO] create_peer_connection() called")
    global _relay

    if _relay is None:
        _relay = MediaRelay()
        print("[VIDEO] MediaRelay created")

    pc = RTCPeerConnection()
    print("[VIDEO] RTCPeerConnection created")

    # Create camera track
    print("[VIDEO] Creating CameraVideoTrack...")
    camera_track = CameraVideoTrack()
    print("[VIDEO] CameraVideoTrack created")

    # Use MediaRelay to handle the track
    video_track = _relay.subscribe(camera_track)
    pc.addTrack(video_track)
    print("[VIDEO] Track added to peer connection")

    return pc
