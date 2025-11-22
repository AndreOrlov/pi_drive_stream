import asyncio
import logging
import threading
from typing import Optional

import cv2
import numpy as np
from aiortc import MediaStreamTrack, RTCPeerConnection
from av import VideoFrame

logger = logging.getLogger(__name__)

try:
    from picamera2 import Picamera2  # type: ignore[import-not-found]

    PICAMERA2_AVAILABLE = True
except ImportError:  # pragma: no cover - not available on non-RPi dev machines
    Picamera2 = None  # type: ignore[assignment]
    PICAMERA2_AVAILABLE = False


_picam2: Optional["Picamera2"] = None  # type: ignore[name-defined]
_picam2_lock = threading.Lock()


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
            config = cam.create_preview_configuration(
                main={"format": "RGB888", "size": (640, 480)}
            )
            cam.configure(config)
            cam.start()
            _picam2 = cam

        return _picam2


class CameraVideoTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self, camera_index: int = 0) -> None:
        super().__init__()
        self._lock = asyncio.Lock()

        self._use_picamera2 = False
        self._picam2: Optional["Picamera2"] = None  # type: ignore[name-defined]
        self._cap: Optional[cv2.VideoCapture] = None

        if PICAMERA2_AVAILABLE:
            try:
                self._picam2 = _ensure_picamera2()
                self._use_picamera2 = True
                logger.info("Using global Picamera2 instance for CSI camera")
            except Exception as exc:  # pragma: no cover - runtime-only on RPi
                logger.error("Failed to initialize Picamera2, falling back to OpenCV: %s", exc)

        if not self._use_picamera2:
            logger.info("Using OpenCV VideoCapture for camera index %s", camera_index)
            self._cap = cv2.VideoCapture(camera_index)
            if not self._cap.isOpened():
                logger.error("Failed to open camera at index %s", camera_index)
        self._frame_count = 0

    async def recv(self) -> VideoFrame:
        pts, time_base = await self.next_timestamp()

        async with self._lock:
            if self._use_picamera2 and self._picam2 is not None:
                frame = self._picam2.capture_array()
                # Picamera2 returns RGB, convert to BGR for aiortc
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                print("[CameraVideoTrack] picamera2 frame mean:", float(frame.mean()))
            else:
                ret, frame = (False, None)
                if self._cap is not None:
                    ret, frame = self._cap.read()
                if not ret or frame is None:
                    logger.error("Camera read failed, sending black frame")
                    await asyncio.sleep(0.05)
                    frame = np.zeros((480, 640, 3), dtype=np.uint8)
                else:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    print("[CameraVideoTrack] opencv frame mean:", float(frame.mean()))

        self._frame_count += 1
        if self._frame_count % 30 == 0:
            # Use print so it always appears in uvicorn stdout without extra logger config
            print(f"[CameraVideoTrack] produced {self._frame_count} frames")

        video_frame = VideoFrame.from_ndarray(frame, format="bgr24")
        video_frame.pts = pts
        video_frame.time_base = time_base
        return video_frame

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
    pc = RTCPeerConnection()
    track = CameraVideoTrack()
    pc.addTrack(track)
    print("[CameraVideoTrack] track added to peer connection")
    return pc
