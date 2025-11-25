import asyncio
from collections import defaultdict
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

T = TypeVar("T")
Handler = Callable[[T], Coroutine[Any, Any, None]]


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[Handler[Any]]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def subscribe(self, topic: str, handler: Handler[T]) -> None:
        async with self._lock:
            self._subscribers[topic].append(handler)  # type: ignore[arg-type]

    async def publish(self, topic: str, message: T) -> None:
        async with self._lock:
            handlers = list(self._subscribers.get(topic, []))
        if not handlers:
            return
        await asyncio.gather(*(h(message) for h in handlers))

    async def publish_drive_cmd(self, cmd: Any) -> None:
        await self.publish("drive/cmd", cmd)

    async def publish_camera_cmd(self, cmd: Any) -> None:
        await self.publish("camera/cmd", cmd)

    async def publish_state(self, state: Any) -> None:
        await self.publish("robot/state", state)
