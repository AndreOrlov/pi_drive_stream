import logging
import platform
from typing import Optional

from aiortc import RTCPeerConnection
from aiortc.contrib.media import MediaPlayer, MediaRelay

logger = logging.getLogger(__name__)

_player: Optional[MediaPlayer] = None
_relay: Optional[MediaRelay] = None


def get_camera_player() -> MediaPlayer:
    """Get or create MediaPlayer for camera using official aiortc method"""
    global _player
    
    if _player is None:
        # Check if running on Raspberry Pi
        if platform.system() == "Linux" and "arm" in platform.machine():
            # On Raspberry Pi, use v4l2 (Video4Linux2) to access camera
            logger.info("Creating MediaPlayer for /dev/video0 with v4l2")
            _player = MediaPlayer(
                '/dev/video0',
                format='v4l2',
                options={
                    'video_size': '640x480',
                    'framerate': '30',
                }
            )
        else:
            # On other platforms (Mac, etc.), use default camera
            logger.info("Creating MediaPlayer for default camera")
            _player = MediaPlayer(
                'default:none',  # Use default video device, no audio
                format='avfoundation' if platform.system() == 'Darwin' else 'v4l2',
                options={'video_size': '640x480'}
            )
        
        logger.info("MediaPlayer created successfully")
    
    return _player


async def create_peer_connection() -> RTCPeerConnection:
    """Create RTCPeerConnection with camera video track using official aiortc MediaPlayer"""
    global _relay
    
    if _relay is None:
        _relay = MediaRelay()
    
    pc = RTCPeerConnection()
    
    # Get camera player (official aiortc way)
    player = get_camera_player()
    
    # Use MediaRelay to handle the video track
    if player.video:
        video_track = _relay.subscribe(player.video)
        pc.addTrack(video_track)
        logger.info("Video track from MediaPlayer added to peer connection")
    else:
        logger.error("MediaPlayer has no video track!")
    
    return pc
