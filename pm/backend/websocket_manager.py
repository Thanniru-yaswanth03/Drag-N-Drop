from typing import Dict, List
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # Maps project_id -> List[WebSocket]
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, project_id: str):
        await websocket.accept()
        if project_id not in self.active_connections:
            self.active_connections[project_id] = []
        self.active_connections[project_id].append(websocket)

    def disconnect(self, websocket: WebSocket, project_id: str):
        if project_id in self.active_connections:
            if websocket in self.active_connections[project_id]:
                self.active_connections[project_id].remove(websocket)
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]

    async def broadcast_to_project(
        self, project_id: str, message: dict, sender: WebSocket = None
    ):
        if project_id not in self.active_connections:
            return

        dead_connections = []
        for connection in self.active_connections[project_id]:
            if connection != sender:
                try:
                    await connection.send_json(message)
                except Exception:
                    dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead, project_id)


ws_manager = ConnectionManager()
