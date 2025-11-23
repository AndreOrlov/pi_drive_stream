"""Simple MJPEG video streaming from Picamera2"""
import asyncio
import io
import logging
from typing import Optional

import cv2
from fastapi import Response
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
except ImportError:
    Picamera2 = None
    PICAMERA2_AVAILABLE = False


_picam2: Optional["Picamera2"] = None


def get_camera():
    """Get or create global camera instance"""
    global _picam2
    
    if _picam2 is None:
        if PICAMERA2_AVAILABLE and Picamera2 is not None:
            logger.info("Initializing Picamera2 for MJPEG streaming")
            _picam2 = Picamera2()
            config = _picam2.create_preview_configuration(
                main={"format": "RGB888", "size": (640, 480)}
            )
            _picam2.configure(config)
            _picam2.start()
            logger.info("Picamera2 started successfully")
        else:
            logger.warning("Picamera2 not available, using OpenCV")
            _picam2 = cv2.VideoCapture(0)
    
    return _picam2


def generate_frames():
    """Generate MJPEG frames"""
    camera = get_camera()
    
    while True:
        if PICAMERA2_AVAILABLE and isinstance(camera, Picamera2):
            # Picamera2
            frame = camera.capture_array()
            # Convert RGB to BGR for JPEG encoding
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        else:
            # OpenCV
            ret, frame = camera.read()
            if not ret:
                logger.error("Failed to read frame from camera")
                break
        
        # Encode frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not ret:
            logger.error("Failed to encode frame as JPEG")
            continue
        
        frame_bytes = buffer.tobytes()
        
        # Yield frame in MJPEG format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


async def video_feed():
    """Async video feed endpoint"""
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

