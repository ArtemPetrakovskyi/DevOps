from unittest.mock import MagicMock, patch

import pytest
import requests

from app import create_app


@pytest.fixture()
def client():
    app = create_app("http://api-test:5000")
    with app.test_client() as c:
        yield c


def fake_response(json_data=None):
    resp = MagicMock()
    resp.json.return_value = json_data or []
    resp.raise_for_status.return_value = None
    return resp


def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}


@patch("app.requests.get")
def test_index_renders_tasks(mock_get, client):
    mock_get.return_value = fake_response([{"id": 1, "title": "Купити молоко", "done": False}])
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Купити молоко".encode() in resp.data
    mock_get.assert_called_once()
    assert mock_get.call_args.args[0] == "http://api-test:5000/api/tasks"


@patch("app.requests.get", side_effect=requests.ConnectionError)
def test_index_shows_error_when_api_down(mock_get, client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "API недоступний".encode() in resp.data


@patch("app.requests.post")
def test_add_sends_post_to_api(mock_post, client):
    resp = client.post("/add", data={"title": "Нова"})
    assert resp.status_code == 302
    mock_post.assert_called_once()
    assert mock_post.call_args.kwargs["json"] == {"title": "Нова"}


@patch("app.requests.post")
def test_add_ignores_empty_title(mock_post, client):
    client.post("/add", data={"title": "  "})
    mock_post.assert_not_called()


@patch("app.requests.patch")
def test_toggle_calls_api(mock_patch, client):
    client.post("/toggle/3")
    assert mock_patch.call_args.args[0] == "http://api-test:5000/api/tasks/3"


@patch("app.requests.delete")
def test_delete_calls_api(mock_delete, client):
    client.post("/delete/3")
    assert mock_delete.call_args.args[0] == "http://api-test:5000/api/tasks/3"
