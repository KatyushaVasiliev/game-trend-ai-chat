from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_data_summary_and_crud():
    assert client.get("/api/data/summary").status_code == 200
    created = client.post("/api/data", json={"date":"2026-01-01","value":1400,"memo":"테스트 관측"})
    assert created.status_code == 201
    item = created.json()
    assert client.put(f"/api/data/{item['id']}", json={"date":"2026-01-02","value":1500,"memo":"수정됨"}).status_code == 200
    assert client.delete(f"/api/data/{item['id']}").status_code == 204

def test_chat_saves_and_loads_conversation():
    response = client.post("/api/chat", json={"message":"최근 추세는?"})
    assert response.status_code == 200
    convo_id = response.json()["conversation_id"]
    loaded = client.get(f"/api/conversations/{convo_id}")
    assert loaded.status_code == 200
    assert len(loaded.json()["messages"]) == 2
