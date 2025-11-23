import asyncio
import fractions
import logging
import threading
from typing import Optional

import cv2
import numpy as np
from aiortc import MediaStreamTrack, RTCPeerConnection
from aiortc.contrib.media import MediaRelay
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
            logger.info("Initializing global Picamera2 instance")
            cam = Picamera2()  # type: ignore[call-arg]
            # Use lower resolution for better encoding performance
            config = cam.create_preview_configuration(
                main={"format": "RGB888", "size": (320, 240)}
            )
            cam.configure(config)
            cam.start()
            _picam2 = cam

        return _picam2


class CameraVideoTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self, camera_index: int = 0) -> None:
        super().__init__()
        print("[CameraVideoTrack] __init__ called")
        self._lock = asyncio.Lock()
        self._counter = 0
        self._timestamp = 0
        self._time_base = fractions.Fraction(1, 90000)  # Standard RTP timestamp rate for video
        self._frame_interval = 6000  # 15fps at 90kHz = 6000 ticks per frame (was 3000 for 30fps)

        self._use_picamera2 = False
        self._picam2: Optional["Picamera2"] = None  # type: ignore[name-defined]
        self._cap: Optional[cv2.VideoCapture] = None

        if PICAMERA2_AVAILABLE:
            try:
                self._picam2 = _ensure_picamera2()
                self._use_picamera2 = True
                print("[CameraVideoTrack] Using Picamera2")
            except Exception as exc:  # pragma: no cover - runtime-only on RPi
                logger.error("Failed to initialize Picamera2, falling back to OpenCV: %s", exc)

        if not self._use_picamera2:
            print(f"[CameraVideoTrack] Using OpenCV for camera {camera_index}")
            self._cap = cv2.VideoCapture(camera_index)
            if not self._cap.isOpened():
                logger.error("Failed to open camera at index %s", camera_index)
        self._frame_count = 0
        print(f"[CameraVideoTrack] __init__ done, use_picamera2={self._use_picamera2}")

    async def recv(self) -> VideoFrame:
        try:
            self._counter += 1

            # Generate our own timestamp since we're wrapped by MediaRelay
            pts = self._timestamp
            time_base = self._time_base
            self._timestamp += self._frame_interval  # Use configured frame interval

            self._frame_count += 1
            if self._frame_count == 1:
                print("[CameraVideoTrack] First frame!")
            if self._frame_count % 30 == 0:
                print(f"[CameraVideoTrack] {self._frame_count} frames sent")

            async with self._lock:
                # For first 15 frames (~1 second at 15fps), send a bright test pattern
                if self._frame_count <= 15:
                    # Create a bright test pattern at 320x240
                    frame = np.zeros((240, 320, 3), dtype=np.uint8)
                    frame[:, :] = [255, 0, 0]  # Red in RGB
                    frame[60:180, 60:260] = [0, 255, 0]  # Green center
                    if self._frame_count == 1:
                        print(f"[CameraVideoTrack] Sending TEST PATTERN 320x240 @ 15fps (mean={np.mean(frame):.1f})")
                elif self._use_picamera2 and self._picam2 is not None:
                    frame = self._picam2.capture_array()
                else:
                    ret, frame = (False, None)
                    if self._cap is not None:
                        ret, frame = self._cap.read()
                    if not ret or frame is None:
                        await asyncio.sleep(0.05)
                        frame = np.zeros((240, 320, 3), dtype=np.uint8)
                    else:
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        # Resize to 320x240 for better performance
                        frame = cv2.resize(frame, (320, 240))

            # Always create VideoFrame with RGB format
            video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
            video_frame.pts = pts
            video_frame.time_base = time_base
            return video_frame
        except Exception as e:
            print(f"[CameraVideoTrack] ERROR: {e}")
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
    global _relay

    if _relay is None:
        _relay = MediaRelay()

    pc = RTCPeerConnection()

    # Create the camera track
    camera_track = CameraVideoTrack()
    print(f"[CameraVideoTrack] track created, readyState: {camera_track.readyState}")

    # Use MediaRelay to properly handle the track
    relayed_track = _relay.subscribe(camera_track)
    print(f"[MediaRelay] track relayed")

    # Add the relayed track to peer connection
    sender = pc.addTrack(relayed_track)
    print(f"[WebRTC] relayed track added, sender: {sender}")

    return pc
