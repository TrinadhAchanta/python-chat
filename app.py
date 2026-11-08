from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI(title="Python Chat")

class ConnectionManager:
    def __init__(self):
        self.active: dict[WebSocket, str] = {}

    async def connect(self, ws: WebSocket, username: str):
        await ws.accept()
        self.active[ws] = username
        await self.broadcast({"type": "system", "text": f"{username} joined"})

    async def disconnect(self, ws: WebSocket):
        username = self.active.pop(ws, None)
        if username:
            await self.broadcast({"type": "system", "text": f"{username} left"})

    async def broadcast(self, message: dict):
        for conn in list(self.active):
            try:
                await conn.send_json(message)
            except Exception:
                self.active.pop(conn, None)

manager = ConnectionManager()

@app.get("/health")
def health():
    return {"status": "ok", "users_online": len(manager.active)}

@app.websocket("/ws/{username}")
async def chat(ws: WebSocket, username: str):
    await manager.connect(ws, username)
    try:
        while True:
            text = (await ws.receive_text()).strip()
            if text:
                await manager.broadcast({"type": "message", "user": username, "text": text[:1000]})
    except WebSocketDisconnect:
        await manager.disconnect(ws)

PAGE = """<!doctype html>"""

@app.get("/", response_class=HTMLResponse)
def index():
    return PAGE
