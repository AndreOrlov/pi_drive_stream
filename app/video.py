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
        print("[CameraVideoTrack] __init__ called")
        self._lock = asyncio.Lock()
        self._counter = 0
        self._timestamp = 0
        self._time_base = fractions.Fraction(1, 90000)  # Standard RTP timestamp rate for video

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
            print(f"[CameraVideoTrack] recv() START, counter={self._counter}")
            self._counter += 1

            # Generate our own timestamp since we're wrapped by MediaRelay
            pts = self._timestamp
            time_base = self._time_base
            self._timestamp += 3000  # 30fps at 90kHz = 3000 ticks per frame

            print(f"[CameraVideoTrack] timestamp: pts={pts}, time_base={time_base}")

            self._frame_count += 1
            if self._frame_count == 1:
                print("[CameraVideoTrack] recv() called for the FIRST time!")
            if self._frame_count % 30 == 0:
                print(f"[CameraVideoTrack] recv() called {self._frame_count} times")

            print("[CameraVideoTrack] About to capture frame...")
            async with self._lock:
                # For first 30 frames (1 second), send a bright test pattern
                if self._frame_count <= 30:
                    # Create a bright test pattern: red square
                    frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    frame[:, :] = [255, 0, 0]  # Red in RGB
                    frame[100:380, 100:540] = [0, 255, 0]  # Green center
                    print(f"[CameraVideoTrack] TEST PATTERN: shape={frame.shape}, mean={np.mean(frame):.1f}")
                elif self._use_picamera2 and self._picam2 is not None:
                    # Picamera2 gives us RGB888
                    frame = self._picam2.capture_array()
                    print(f"[CameraVideoTrack] Picamera2 frame: shape={frame.shape}, dtype={frame.dtype}, mean={np.mean(frame):.1f}")
                else:
                    ret, frame = (False, None)
                    if self._cap is not None:
                        ret, frame = self._cap.read()
                    if not ret or frame is None:
                        logger.error("Camera read failed, sending black frame")
                        await asyncio.sleep(0.05)
                        frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    else:
                        # OpenCV gives us BGR, convert to RGB
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        print(f"[CameraVideoTrack] OpenCV frame: shape={frame.shape}, dtype={frame.dtype}, mean={np.mean(frame):.1f}")

            print(f"[CameraVideoTrack] Creating VideoFrame from array...")
            # Always create VideoFrame with RGB format
            video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
            video_frame.pts = pts
            video_frame.time_base = time_base
            print(f"[CameraVideoTrack] VideoFrame created: {video_frame.width}x{video_frame.height}, pts={pts}, time_base={time_base}")
            print(f"[CameraVideoTrack] recv() COMPLETE, returning frame")
            return video_frame
        except Exception as e:
            print(f"[CameraVideoTrack] ERROR in recv(): {e}")
            import traceback
            traceback.print_exc()
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
