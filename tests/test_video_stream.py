from __future__ import annotations

import asyncio
import importlib
from collections.abc import Awaitable, Callable
from typing import Any

import pytest


class _DummyTrack:
    """Мок видеотрека без доступа к реальной камере."""

    created = 0
    last_instance: "_DummyTrack | None" = None

    def __init__(self) -> None:
        _DummyTrack.created += 1
        _DummyTrack.last_instance = self
        self.readyState = "live"
        self.stop_called = False

    def stop(self) -> None:
        """Помечаем трек как остановленный."""

        self.stop_called = True
        self.readyState = "ended"


class _DummyRelay:
    """Упрощённый MediaRelay, фиксирующий подписчиков."""

    def __init__(self) -> None:
        self.subscribed: list[Any] = []

    def subscribe(self, track: Any) -> tuple[str, Any]:
        """Эмулируем выдачу обёртки поверх базового трека."""

        self.subscribed.append(track)
        return ("relay-track", track)


class _DummyPeerConnection:
    """Заглушка RTCPeerConnection с минимальным API."""

    def __init__(self) -> None:
        self.tracks: list[Any] = []

    def addTrack(self, track: Any) -> None:  # noqa: N802 - FastAPI/Aiortc API
        """Сохраняем добавленный трек."""

        self.tracks.append(track)


class _StatefulPeer:
    """Мок PeerConnection для теста мониторинга состояний."""

    def __init__(self) -> None:
        self.connectionState = "new"
        self._handlers: dict[str, Callable[[], Awaitable[None]]] = {}
        self.closed = False

    def on(self, event: str) -> Callable[[Callable[[], Awaitable[None]]], Callable[[], Awaitable[None]]]:  # noqa: D401
        """Совместимый с aiortc декоратор для регистрации хендлеров."""

        def _register(callback: Callable[[], Awaitable[None]]) -> Callable[[], Awaitable[None]]:
            self._handlers[event] = callback
            return callback

        return _register

    async def close(self) -> None:
        """Помечаем соединение закрытым."""

        self.closed = True

    async def emit(self, event: str) -> None:
        """Выполняем зарегистрированный обработчик."""

        await self._handlers[event]()


def test_create_peer_connection_reuses_single_camera_track(monkeypatch: pytest.MonkeyPatch) -> None:
    """Проверяем, что камера создаётся один раз, а счётчик пользователей ведётся корректно."""

    video = importlib.reload(importlib.import_module("app.video"))
    monkeypatch.setattr(video, "CameraVideoTrack", _DummyTrack)
    monkeypatch.setattr(video, "MediaRelay", _DummyRelay)
    monkeypatch.setattr(video, "RTCPeerConnection", _DummyPeerConnection)

    async def _run_test() -> None:
        pc1, release1 = await video.create_peer_connection()
        pc2, release2 = await video.create_peer_connection()

        assert _DummyTrack.created == 1
        assert len(pc1.tracks) == 1
        assert len(pc2.tracks) == 1
        assert video._camera_track_users == 2  # noqa: SLF001 - доступен только в тесте

        await release1()
        assert video._camera_track_users == 1
        assert not _DummyTrack.last_instance.stop_called

        await release2()
        assert video._camera_track_users == 0
        assert _DummyTrack.last_instance.stop_called
        assert video._camera_track is None  # noqa: SLF001 - только для проверок

    asyncio.run(_run_test())


def test_run_peer_connection_cleans_up_on_disconnect(monkeypatch: pytest.MonkeyPatch) -> None:
    """Убеждаемся, что при disconnect вызывается release и соединение закрывается."""

    server = importlib.reload(importlib.import_module("app.web.server"))
    peer = _StatefulPeer()
    server._peer_connections.add(peer)  # noqa: SLF001 - используется для глобального реестра

    cleanup_events: list[str] = []

    async def release_mock() -> None:
        cleanup_events.append("release")

    async def _run_test() -> None:
        await server._run_peer_connection(peer, release_mock)

        peer.connectionState = "disconnected"
        await peer.emit("connectionstatechange")
        await asyncio.sleep(0)

        assert cleanup_events == ["release"]
        assert peer.closed
        assert peer not in server._peer_connections

        # Повторное событие не даёт двойного релиза
        await peer.emit("connectionstatechange")
        assert cleanup_events == ["release"]

    asyncio.run(_run_test())
