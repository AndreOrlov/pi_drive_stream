import asyncio
import logging

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


class CameraVideoTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self, camera_index: int = 0) -> None:
        super().__init__()
        self._lock = asyncio.Lock()

        self._use_picamera2 = PICAMERA2_AVAILABLE
        self._picam2 = None
        self._cap = None

        if self._use_picamera2:
            logger.info("Using Picamera2 for CSI camera")
            self._picam2 = Picamera2()  # type: ignore[call-arg]
            config = self._picam2.create_preview_configuration(
                main={"format": "RGB888", "size": (640, 480)}
            )
            self._picam2.configure(config)
            self._picam2.start()
        else:
            logger.info("Picamera2 not available, falling back to OpenCV VideoCapture")
            self._cap = cv2.VideoCapture(camera_index)
            if not self._cap.isOpened():
                logger.error("Failed to open camera at index %s", camera_index)

    async def recv(self) -> VideoFrame:
        pts, time_base = await self.next_timestamp()

        async with self._lock:
            if self._use_picamera2 and self._picam2 is not None:
                frame = self._picam2.capture_array()
                # Picamera2 returns RGB already
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

        video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
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
    return pc
