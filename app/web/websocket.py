from __future__ import annotations

import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect


def register_websocket_routes(app: FastAPI) -> None:
    @app.websocket("/ws/live")
    async def live_websocket(websocket: WebSocket) -> None:
        await websocket.accept()
        try:
            while True:
                await websocket.send_json(app.state.service.snapshot())
                await asyncio.sleep(1)
        except WebSocketDisconnect:
            return

