import asyncio
import json
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

app = FastAPI()
app.mount("/static", StaticFiles(directory="frontend"), name="static")

drive_node = DriveNode()
camera_node = CameraNode()

# Keep peer connections alive
_peer_connections: set[RTCPeerConnection] = set()


async def _run_peer_connection(pc: RTCPeerConnection) -> None:
    """Keep peer connection alive until it closes."""

    disconnected_time = None

    @pc.on("connectionstatechange")
    async def on_connectionstatechange() -> None:
        print(f"[WEBRTC] Peer connection state changed: {pc.connectionState}")
        if pc.connectionState in ("closed", "failed"):
            print(f"[WEBRTC] Cleaning up peer connection (state={pc.connectionState})")
            _peer_connections.discard(pc)
            await pc.close()
            print(f"[WEBRTC] Active peer connections: {len(_peer_connections)}")

    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange() -> None:
        nonlocal disconnected_time
        print(f"[WEBRTC] ICE connection state changed: {pc.iceConnectionState}")

        if pc.iceConnectionState in ("disconnected", "failed"):
            if disconnected_time is None:
                disconnected_time = asyncio.get_event_loop().time()
                print(f"[WEBRTC] Connection lost, will cleanup in 5 seconds if not recovered")
        elif pc.iceConnectionState == "connected":
            disconnected_time = None  # Восстановилось

    # Мониторинг неактивных соединений
    try:
        while pc.connectionState not in ("closed", "failed"):
            await asyncio.sleep(1)

            # Если соединение disconnected больше 5 секунд, принудительно закрываем
            if disconnected_time is not None:
                elapsed = asyncio.get_event_loop().time() - disconnected_time
                if elapsed > 5.0:
                    print(f"[WEBRTC] Force closing stale connection (disconnected for {elapsed:.1f}s)")
                    _peer_connections.discard(pc)
                    await pc.close()
                    print(f"[WEBRTC] Active peer connections: {len(_peer_connections)}")
                    break
    except Exception as e:
        print(f"[WEBRTC] Error in peer connection monitor: {e}")


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
    print(f"[WEBRTC] New peer connection created. Active connections: {len(_peer_connections)}")

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
