from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"

def test_index_page():
    r = client.get("/")
    assert r.status_code == 200 and "Python Chat" in r.text

def test_join_and_message():
    with client.websocket_connect("/ws/alice") as ws:
        assert ws.receive_json() == {"type": "system", "text": "alice joined"}
        ws.send_text("hello")
        assert ws.receive_json() == {"type": "message", "user": "alice", "text": "hello"}

def test_broadcast_between_users():
    with client.websocket_connect("/ws/alice") as a:
        a.receive_json()
        with client.websocket_connect("/ws/bob") as b:
            assert a.receive_json()["text"] == "bob joined"
            b.receive_json()
            b.send_text("hi alice")
            assert a.receive_json() == {"type": "message", "user": "bob", "text": "hi alice"}
            assert b.receive_json()["text"] == "hi alice"

def test_empty_message_ignored_and_length_capped():
    with client.websocket_connect("/ws/carol") as ws:
        ws.receive_json()
        ws.send_text("   ")
        ws.send_text("x" * 2000)
        assert len(ws.receive_json()["text"]) == 1000
