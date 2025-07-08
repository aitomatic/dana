import pytest
from fastapi.testclient import TestClient
from dana.api.server.server import create_app
import uuid

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

# --- Conversations ---
def test_conversation_crud(client):
    # Create
    resp = client.post("/conversations/", json={"title": "Test Conversation"})
    assert resp.status_code == 200
    convo = resp.json()
    convo_id = convo["id"]
    assert convo["title"] == "Test Conversation"

    # List
    resp = client.get("/conversations/")
    assert resp.status_code == 200
    assert any(c["id"] == convo_id for c in resp.json())

    # Get
    resp = client.get(f"/conversations/{convo_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == convo_id

    # Update
    resp = client.put(f"/conversations/{convo_id}", json={"title": "Updated Title"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated Title"

    # Delete
    resp = client.delete(f"/conversations/{convo_id}")
    assert resp.status_code == 200
    # Confirm gone
    resp = client.get(f"/conversations/{convo_id}")
    assert resp.status_code == 404

# --- Messages ---
def test_message_crud(client):
    # Create conversation
    resp = client.post("/conversations/", json={"title": "MsgTest"})
    convo_id = resp.json()["id"]
    # Create message
    resp = client.post(f"/conversations/{convo_id}/messages/", json={"sender": "user", "content": "Hello"})
    assert resp.status_code == 200
    msg = resp.json()
    msg_id = msg["id"]
    assert msg["sender"] == "user"
    # List
    resp = client.get(f"/conversations/{convo_id}/messages/")
    assert resp.status_code == 200
    assert any(m["id"] == msg_id for m in resp.json())
    # Get
    resp = client.get(f"/conversations/{convo_id}/messages/{msg_id}")
    assert resp.status_code == 200
    # Update
    resp = client.put(f"/conversations/{convo_id}/messages/{msg_id}", json={"sender": "bot", "content": "Hi!"})
    assert resp.status_code == 200
    assert resp.json()["sender"] == "bot"
    # Delete
    resp = client.delete(f"/conversations/{convo_id}/messages/{msg_id}")
    assert resp.status_code == 200
    # Confirm gone
    resp = client.get(f"/conversations/{convo_id}/messages/{msg_id}")
    assert resp.status_code == 404

# --- Topics ---
def test_topic_crud(client):
    # Create
    resp = client.post("/topics/", json={"name": "Test Topic", "description": "desc"})
    assert resp.status_code == 200
    topic = resp.json()
    topic_id = topic["id"]
    # List
    resp = client.get("/topics/")
    assert resp.status_code == 200
    assert any(t["id"] == topic_id for t in resp.json())
    # Get
    resp = client.get(f"/topics/{topic_id}")
    assert resp.status_code == 200
    # Update
    resp = client.put(f"/topics/{topic_id}", json={"name": "Updated Topic", "description": "desc2"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Topic"
    # Delete
    resp = client.delete(f"/topics/{topic_id}")
    assert resp.status_code == 200
    # Confirm gone
    resp = client.get(f"/topics/{topic_id}")
    assert resp.status_code == 404

# --- Documents ---
def test_document_crud(client, tmp_path):
    # Create topic for document with a unique name
    unique_topic_name = f"DocTopic_{uuid.uuid4()}"
    resp = client.post("/topics/", json={"name": unique_topic_name, "description": "desc"})
    topic_id = resp.json()["id"]
    # Upload document
    file_content = b"dummy pdf content"
    files = {"file": ("test.pdf", file_content, "application/pdf")}
    data = {"title": "TestDoc", "description": "desc", "topic_id": str(topic_id)}
    resp = client.post("/documents/", data=data, files=files)
    assert resp.status_code == 200
    doc = resp.json()
    doc_id = doc["id"]
    # List
    resp = client.get("/documents/")
    assert resp.status_code == 200
    assert any(d["id"] == doc_id for d in resp.json())
    # Get
    resp = client.get(f"/documents/{doc_id}")
    assert resp.status_code == 200
    # Update (only original_filename is supported)
    resp = client.put(f"/documents/{doc_id}", json={"original_filename": "updated_test.pdf"})
    assert resp.status_code == 200
    assert resp.json()["original_filename"] == "updated_test.pdf"
    # Delete
    resp = client.delete(f"/documents/{doc_id}")
    assert resp.status_code == 200
    # Confirm gone
    resp = client.get(f"/documents/{doc_id}")
    assert resp.status_code == 404 