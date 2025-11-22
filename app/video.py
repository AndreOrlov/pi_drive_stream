import asyncio

import cv2
from aiortc import MediaStreamTrack, RTCPeerConnection
from av import VideoFrame


class CameraVideoTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self, camera_index: int = 0) -> None:
        super().__init__()
        self._cap = cv2.VideoCapture(camera_index)
        self._lock = asyncio.Lock()

    async def recv(self) -> VideoFrame:
        pts, time_base = await self.next_timestamp()

        async with self._lock:
            ret, frame = self._cap.read()

        if not ret:
            await asyncio.sleep(0.01)
            raise RuntimeError("Camera read failed")

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
        video_frame.pts = pts
        video_frame.time_base = time_base
        return video_frame

    async def stop(self) -> None:
        await super().stop()
        self._cap.release()


async def create_peer_connection() -> RTCPeerConnection:
    pc = RTCPeerConnection()
    track = CameraVideoTrack()
    pc.addTrack(track)
    return pc


