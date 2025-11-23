import asyncio
import json
from typing import Any, Dict, Set

from aiortc import RTCPeerConnection, RTCSessionDescription
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app import event_bus
from app.messages import CameraCommand, DriveCommand, DriveMode
from app.nodes.camera import CameraNode
from app.nodes.drive import DriveNode
from app.video import create_peer_connection

app = FastAPI()
app.mount("/static", StaticFiles(directory="frontend"), name="static")

drive_node = DriveNode(timeout_s=0.5)
camera_node = CameraNode()

# Keep peer connections alive
_peer_connections: Set[RTCPeerConnection] = set()


async def _run_peer_connection(pc: RTCPeerConnection) -> None:
    """Keep peer connection alive until it closes."""
    print("[WebRTC] peer connection started")
    
    @pc.on("connectionstatechange")
    async def on_connectionstatechange() -> None:
        print(f"[WebRTC] connectionState: {pc.connectionState}")
        if pc.connectionState == "connected":
            print("[WebRTC] Connection established!")
            for idx, transceiver in enumerate(pc.getTransceivers()):
                print(f"[WebRTC]   Transceiver {idx}: currentDirection={transceiver.currentDirection}")
                # Check if sender is actually sending
                if transceiver.sender and transceiver.sender.transport:
                    transport = transceiver.sender.transport
                    print(f"[WebRTC]   Transport state: {transport.state}")
        elif pc.connectionState == "failed":
            print("[WebRTC] CONNECTION FAILED!")
            # Try to get error details
            for idx, transceiver in enumerate(pc.getTransceivers()):
                if transceiver.sender:
                    print(f"[WebRTC]   Transceiver {idx} sender state: {transceiver.sender}")
        elif pc.connectionState == "closed":
            print("[WebRTC] connection closed, cleaning up")
            _peer_connections.discard(pc)
            await pc.close()
    
    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange() -> None:
        print(f"[WebRTC] iceConnectionState: {pc.iceConnectionState}")
        if pc.iceConnectionState == "failed":
            print("[WebRTC] ICE CONNECTION FAILED!")


@app.on_event("startup")
async def on_startup() -> None:
    asyncio.create_task(drive_node.start())
    asyncio.create_task(camera_node.start())


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/")
async def index() -> FileResponse:
    return FileResponse("frontend/index.html")


class Offer(BaseModel):
    sdp: str
    type: str


@app.post("/webrtc/offer")
async def webrtc_offer(offer: Offer) -> Dict[str, Any]:
    pc: RTCPeerConnection = await create_peer_connection()

    # Store PC to keep it alive
    _peer_connections.add(pc)

    # Start background task to monitor connection
    asyncio.create_task(_run_peer_connection(pc))

    remote_desc = RTCSessionDescription(sdp=offer.sdp, type=offer.type)
    await pc.setRemoteDescription(remote_desc)

    print(f"[WebRTC] Remote description set, senders: {len(pc.getSenders())}")
    for idx, sender in enumerate(pc.getSenders()):
        print(f"[WebRTC]   Sender {idx}: track={sender.track}, transport={sender.transport}")

    # Check transceivers
    print(f"[WebRTC] Transceivers: {len(pc.getTransceivers())}")
    for idx, transceiver in enumerate(pc.getTransceivers()):
        print(f"[WebRTC]   Transceiver {idx}: kind={transceiver.kind}, direction={transceiver.direction}, currentDirection={transceiver.currentDirection}")

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    # Give the sender a moment to initialize
    await asyncio.sleep(0.1)

    print(f"[WebRTC] Answer created, {len(_peer_connections)} active connections")
    print(f"[WebRTC] Local description type: {pc.localDescription.type}")

    # Log SDP to see which codec is being used
    if pc.localDescription and pc.localDescription.sdp:
        sdp_lines = pc.localDescription.sdp.split('\n')
        for line in sdp_lines:
            if 'a=rtpmap' in line or 'a=fmtp' in line:
                print(f"[WebRTC] SDP: {line.strip()}")

    # Check again after answer
    print("[WebRTC] After answer:")
    for idx, transceiver in enumerate(pc.getTransceivers()):
        print(f"[WebRTC]   Transceiver {idx}: currentDirection={transceiver.currentDirection}")

    # Check if sender has started
    for idx, sender in enumerate(pc.getSenders()):
        if sender.track:
            print(f"[WebRTC]   Sender {idx} track: kind={sender.track.kind}, readyState={sender.track.readyState}")

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
                cmd = DriveCommand(
                    vx=float(msg.get("vx", 0.0)),
                    steer=float(msg.get("steer", 0.0)),
                    mode=DriveMode.MANUAL,
                )
                await event_bus.publish_drive_cmd(cmd)

            elif msg_type == "camera":
                cmd = CameraCommand(
                    pan=float(msg.get("pan", 0.0)),
                    tilt=float(msg.get("tilt", 0.0)),
                )
                await event_bus.publish_camera_cmd(cmd)

            elif msg_type == "emergency_stop":
                cmd = DriveCommand(vx=0.0, steer=0.0, mode=DriveMode.EMERGENCY_STOP)
                await event_bus.publish_drive_cmd(cmd)

    except WebSocketDisconnect:
        stop_cmd = DriveCommand(vx=0.0, steer=0.0, mode=DriveMode.EMERGENCY_STOP)
        await event_bus.publish_drive_cmd(stop_cmd)
