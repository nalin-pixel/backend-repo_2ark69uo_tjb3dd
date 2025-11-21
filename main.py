import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import Dict, List, Set
from pydantic import BaseModel
from database import create_document

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CreateRoomRequest(BaseModel):
    player_id: str
    room_code: str

class JoinRoomRequest(BaseModel):
    player_id: str
    room_code: str

# In-memory connection manager for websockets (not for persistence)
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.voice_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, room: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(room, set()).add(websocket)

    def disconnect(self, room: str, websocket: WebSocket):
        if room in self.active_connections and websocket in self.active_connections[room]:
            self.active_connections[room].remove(websocket)
        if room in self.voice_connections and websocket in self.voice_connections[room]:
            self.voice_connections[room].remove(websocket)

    async def broadcast(self, room: str, message: dict):
        for connection in list(self.active_connections.get(room, set())):
            try:
                await connection.send_json(message)
            except Exception:
                pass

    async def broadcast_voice(self, room: str, data: bytes):
        for connection in list(self.voice_connections.get(room, set())):
            try:
                await connection.send_bytes(data)
            except Exception:
                pass

manager = ConnectionManager()

@app.get("/")
async def root():
    return {"message": "Ludo backend running"}

@app.get("/test")
async def test_database():
    from database import db
    status = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "❌ Not Set",
        "database_name": "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        import os
        status["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
        status["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
        if db is not None:
            status["database"] = "✅ Available"
            cols = db.list_collection_names()
            status["collections"] = cols
            status["connection_status"] = "Connected"
    except Exception as e:
        status["database"] = f"⚠️ {str(e)[:60]}"
    return status

@app.post("/api/room/create")
async def create_room(req: CreateRoomRequest):
    from schemas import Room
    doc = Room(room_code=req.room_code, created_by=req.player_id, players=[req.player_id])
    room_id = create_document("room", doc)
    return {"ok": True, "room_id": room_id}

@app.post("/api/room/join")
async def join_room(req: JoinRoomRequest):
    # Persistence of room membership is in DB via moves/rooms; realtime via websockets
    await manager.broadcast(req.room_code, {"type": "player_joined", "player_id": req.player_id})
    return {"ok": True}

# WebSocket for game state (JSON messages)
@app.websocket("/ws/game/{room_code}")
async def websocket_endpoint(websocket: WebSocket, room_code: str):
    await manager.connect(room_code, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Echo/broadcast game events to room
            await manager.broadcast(room_code, data)
    except WebSocketDisconnect:
        manager.disconnect(room_code, websocket)

# WebSocket for raw voice data (binary)
@app.websocket("/ws/voice/{room_code}")
async def voice_endpoint(websocket: WebSocket, room_code: str):
    await websocket.accept()
    manager.voice_connections.setdefault(room_code, set()).add(websocket)
    try:
        while True:
            msg = await websocket.receive()
            if "bytes" in msg and msg["bytes"] is not None:
                await manager.broadcast_voice(room_code, msg["bytes"])  # relay audio frames
    except WebSocketDisconnect:
        manager.disconnect(room_code, websocket)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
