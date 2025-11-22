from app import event_bus
from app.hw.motors_stub import apply_camera_command
from app.messages import CameraCommand


class CameraNode:
    async def start(self) -> None:
        await event_bus.subscribe("camera/cmd", self._on_camera_cmd)

    async def _on_camera_cmd(self, cmd: CameraCommand) -> None:
        await apply_camera_command(cmd)


