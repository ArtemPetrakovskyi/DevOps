import pytest

from app import create_app


@pytest.fixture()
def client():
    app = create_app("sqlite:///:memory:")
    with app.test_client() as c:
        yield c


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_info_returns_version_and_pod(monkeypatch):
    monkeypatch.setenv("APP_VERSION", "1.2.3")
    app = create_app("sqlite:///:memory:")
    body = app.test_client().get("/api/info").get_json()
    assert body["service"] == "api"
    assert body["version"] == "1.2.3"
    assert body["pod"]


def test_list_is_empty_at_start(client):
    resp = client.get("/api/tasks")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_create_task(client):
    resp = client.post("/api/tasks", json={"title": "Вивчити Docker"})
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["title"] == "Вивчити Docker"
    assert body["done"] is False
    assert len(client.get("/api/tasks").get_json()) == 1


def test_create_task_without_title_returns_400(client):
    resp = client.post("/api/tasks", json={"title": "   "})
    assert resp.status_code == 400


def test_toggle_task(client):
    task_id = client.post("/api/tasks", json={"title": "t"}).get_json()["id"]
    resp = client.patch(f"/api/tasks/{task_id}", json={})
    assert resp.get_json()["done"] is True
    resp = client.patch(f"/api/tasks/{task_id}", json={})
    assert resp.get_json()["done"] is False


def test_delete_task(client):
    task_id = client.post("/api/tasks", json={"title": "t"}).get_json()["id"]
    assert client.delete(f"/api/tasks/{task_id}").status_code == 204
    assert client.get("/api/tasks").get_json() == []


def test_unknown_task_returns_404(client):
    assert client.patch("/api/tasks/999", json={}).status_code == 404
    assert client.delete("/api/tasks/999").status_code == 404
