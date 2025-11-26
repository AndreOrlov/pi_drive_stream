import asyncio
import json
import logging
from typing import Any

from aiortc import RTCPeerConnection, RTCSessionDescription
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app import event_bus
from app.config import config
from app.messages import CameraCommand, DriveCommand, DriveMode
from app.nodes.camera import CameraNode
from app.nodes.drive import DriveNode
from app.video import create_peer_connection

logger = logging.getLogger(__name__)

app = FastAPI()
app.mount("/static", StaticFiles(directory="frontend"), name="static")

drive_node = DriveNode()
camera_node = CameraNode()

# Keep peer connections alive
_peer_connections: set[RTCPeerConnection] = set()


async def _run_peer_connection(pc: RTCPeerConnection) -> None:
    """Keep peer connection alive until it closes."""

    @pc.on("connectionstatechange")
    async def on_connectionstatechange() -> None:
        if pc.connectionState in ["closed", "failed"]:
            logger.info(f"Peer connection {pc.connectionState}, cleaning up")
            _peer_connections.discard(pc)
            await pc.close()

    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange() -> None:
        if pc.iceConnectionState == "failed":
            logger.warning("ICE connection failed")


@app.on_event("startup")
async def on_startup() -> None:
    asyncio.create_task(drive_node.start())
    asyncio.create_task(camera_node.start())


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
async def index() -> FileResponse:
    return FileResponse("frontend/index.html")


@app.get("/api/config")
async def get_config() -> dict[str, Any]:
    """Получить конфигурацию для фронтенда"""
    return {
        "camera": {
            "step": config.camera.step_size,
            "speed": config.camera.continuous_speed,
            "update_interval_ms": 1000 // config.camera.update_rate,
            "hold_delay_ms": config.camera.hold_delay_ms,
            "min_pan": config.camera.min_pan,
            "max_pan": config.camera.max_pan,
            "min_tilt": config.camera.min_tilt,
            "max_tilt": config.camera.max_tilt,
        },
        "video": {
            "width": config.video.width,
            "height": config.video.height,
            "fps": config.video.fps,
        },
    }


class Offer(BaseModel):
    sdp: str
    type: str


@app.post("/webrtc/offer")
async def webrtc_offer(offer: Offer) -> dict[str, Any]:
    pc: RTCPeerConnection = await create_peer_connection()

    # Store PC to keep it alive
    _peer_connections.add(pc)

    # Start background task to monitor connection
    asyncio.create_task(_run_peer_connection(pc))

    remote_desc = RTCSessionDescription(sdp=offer.sdp, type=offer.type)
    await pc.setRemoteDescription(remote_desc)

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}


@app.websocket("/ws/control")
async def ws_control(ws: WebSocket) -> None:
    await ws.accept()
    try:
        while True:
            msg_text = await ws.receive_text()
            msg = json.loads(msg_text)

            msg_type = msg.get("type")
            if msg_type == "drive":
                drive_cmd = DriveCommand(
                    vx=float(msg.get("vx", 0.0)),
                    steer=float(msg.get("steer", 0.0)),
                    mode=DriveMode.MANUAL,
                )
                await event_bus.publish_drive_cmd(drive_cmd)

            elif msg_type == "camera":
                camera_cmd = CameraCommand(
                    pan=float(msg.get("pan", 0.0)),
                    tilt=float(msg.get("tilt", 0.0)),
                )
                await event_bus.publish_camera_cmd(camera_cmd)

            elif msg_type == "emergency_stop":
                stop_cmd = DriveCommand(
                    vx=0.0, steer=0.0, mode=DriveMode.EMERGENCY_STOP
                )
                await event_bus.publish_drive_cmd(stop_cmd)

    except WebSocketDisconnect:
        stop_cmd = DriveCommand(vx=0.0, steer=0.0, mode=DriveMode.EMERGENCY_STOP)
        await event_bus.publish_drive_cmd(stop_cmd)
