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


PAGE = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Python Chat</title>
<style>
body{font-family:sans-serif;max-width:600px;margin:40px auto;padding:0 16px}
#log{border:1px solid #ccc;height:350px;overflow-y:auto;padding:8px;margin-bottom:8px}
.sys{color:#888;font-style:italic}
</style>
</head>
<body>
<h2>Python Chat</h2>
<div id="join"><input id="name" placeholder="Your name"> <button onclick="join()">Join</button></div>
<div id="log"></div>
<input id="msg" placeholder="Type a message" style="width:75%"> <button onclick="send()">Send</button>
<script>
let ws;
function join(){
  const n=document.getElementById('name').value.trim();
  if(!n) return;
  const p=location.protocol==='https:'?'wss':'ws';
  ws=new WebSocket(p+'://'+location.host+'/ws/'+encodeURIComponent(n));
  ws.onmessage=function(e){
    const m=JSON.parse(e.data);
    const d=document.createElement('div');
    if(m.type==='system'){d.className='sys';d.textContent=m.text;}
    else{d.textContent=m.user+': '+m.text;}
    const l=document.getElementById('log');
    l.appendChild(d);
    l.scrollTop=l.scrollHeight;
  };
  document.getElementById('join').style.display='none';
}
function send(){
  const i=document.getElementById('msg');
  if(ws && i.value.trim()){ws.send(i.value);i.value='';}
}
document.getElementById('msg').addEventListener('keydown',function(e){if(e.key==='Enter')send();});
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index():
    return PAGE
