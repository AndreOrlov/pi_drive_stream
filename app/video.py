import asyncio
import logging

import cv2
import numpy as np
from aiortc import MediaStreamTrack, RTCPeerConnection
from av import VideoFrame


logger = logging.getLogger(__name__)


class CameraVideoTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self, camera_index: int = 0) -> None:
        super().__init__()
        self._cap = cv2.VideoCapture(camera_index)
        self._lock = asyncio.Lock()

        if not self._cap.isOpened():
            logger.error("Failed to open camera at index %s", camera_index)

    async def recv(self) -> VideoFrame:
        pts, time_base = await self.next_timestamp()

        async with self._lock:
            ret, frame = self._cap.read()

        if not ret or frame is None:
            logger.error("Camera read failed, sending black frame")
            await asyncio.sleep(0.05)
            frame = np.zeros((480, 640, 3), dtype=np.uint8)

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
        video_frame.pts = pts
        video_frame.time_base = time_base
        return video_frame

    def stop(self) -> None:
        super().stop()
        if self._cap.isOpened():
            self._cap.release()


async def create_peer_connection() -> RTCPeerConnection:
    pc = RTCPeerConnection()
    track = CameraVideoTrack()
    pc.addTrack(track)
    return pc
