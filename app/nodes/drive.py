import asyncio
import time

from app import event_bus
from app.hw.motors_stub import apply_drive_command
from app.messages import DriveCommand, DriveMode


class DriveNode:
    def __init__(self, timeout_s: float = 0.5) -> None:
        self.timeout_s = timeout_s
        self._last_cmd_time = time.monotonic()

    async def start(self) -> None:
        await event_bus.subscribe("drive/cmd", self._on_drive_cmd)
        asyncio.create_task(self._watchdog())

    async def _on_drive_cmd(self, cmd: DriveCommand) -> None:
        self._last_cmd_time = time.monotonic()

        if cmd.mode == DriveMode.EMERGENCY_STOP:
            safe_cmd = DriveCommand(vx=0.0, steer=0.0, mode=cmd.mode)
            await apply_drive_command(safe_cmd)
        else:
            await apply_drive_command(cmd)

    async def _watchdog(self) -> None:
        while True:
            await asyncio.sleep(0.1)
            if time.monotonic() - self._last_cmd_time > self.timeout_s:
                safe_cmd = DriveCommand(vx=0.0, steer=0.0, mode=DriveMode.EMERGENCY_STOP)
                await apply_drive_command(safe_cmd)


