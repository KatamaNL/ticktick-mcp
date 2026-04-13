"""Unit tests for new TickTickClient methods using mocked HTTP."""

import pytest
from unittest.mock import patch, MagicMock
from ticktick_mcp.src.ticktick_client import TickTickClient
import os


@pytest.fixture
def client():
    """Create a TickTickClient with fake credentials."""
    with patch.dict(
        os.environ,
        {
            "TICKTICK_ACCESS_TOKEN": "fake-token",
            "TICKTICK_CLIENT_ID": "fake-id",
            "TICKTICK_CLIENT_SECRET": "fake-secret",
        },
    ):
        c = TickTickClient()
        return c


class TestGetCompletedTasks:
    def test_basic_call(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '[{"id":"t1","title":"Done task","status":2}]'
        mock_resp.json.return_value = [{"id": "t1", "title": "Done task", "status": 2}]

        with patch("requests.post", return_value=mock_resp):
            result = client.get_completed_tasks(
                project_ids=["proj1"],
                start_date="2026-03-22T00:00:00+0000",
                end_date="2026-03-23T23:59:59+0000",
            )
            assert isinstance(result, list)
            assert result[0]["id"] == "t1"

    def test_empty_params(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "[]"
        mock_resp.json.return_value = []

        with patch("requests.post", return_value=mock_resp):
            result = client.get_completed_tasks()
            assert result == []


class TestFilterTasks:
    def test_filter_by_status(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '[{"id":"t1","status":0}]'
        mock_resp.json.return_value = [{"id": "t1", "status": 0}]

        with patch("requests.post", return_value=mock_resp):
            result = client.filter_tasks(project_ids=["proj1"], status=[0])
            assert isinstance(result, list)

    def test_filter_by_tags(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '[{"id":"t1","tags":["urgent"]}]'
        mock_resp.json.return_value = [{"id": "t1", "tags": ["urgent"]}]

        with patch("requests.post", return_value=mock_resp) as mock_post:
            client.filter_tasks(tags=["urgent"])
            call_kwargs = mock_post.call_args
            body = call_kwargs[1]["json"]
            assert body["tag"] == ["urgent"]

    def test_priority_typo(self, client):
        """The API has a typo: 'proiority' instead of 'priority'. We must match it."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "[]"
        mock_resp.json.return_value = []

        with patch("requests.post", return_value=mock_resp) as mock_post:
            client.filter_tasks(priority=[5])
            body = mock_post.call_args[1]["json"]
            assert "proiority" in body
            assert "priority" not in body


class TestMoveTasks:
    def test_move_single(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '[{"id":"t1","etag":"abc"}]'
        mock_resp.json.return_value = [{"id": "t1", "etag": "abc"}]

        with patch("requests.post", return_value=mock_resp):
            result = client.move_tasks(
                [{"taskId": "t1", "fromProjectId": "proj1", "toProjectId": "proj2"}]
            )
            assert result[0]["id"] == "t1"

    def test_move_sends_array(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "[]"
        mock_resp.json.return_value = []

        with patch("requests.post", return_value=mock_resp) as mock_post:
            client.move_tasks(
                [{"taskId": "t1", "fromProjectId": "p1", "toProjectId": "p2"}]
            )
            body = mock_post.call_args[1]["json"]
            assert isinstance(body, list)


class TestCreateTaskWithTags:
    def test_tags_in_body(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"id":"t1","tags":["label1"]}'
        mock_resp.json.return_value = {"id": "t1", "tags": ["label1"]}

        with patch("requests.post", return_value=mock_resp) as mock_post:
            client.create_task(title="Test", project_id="proj1", tags=["label1"])
            call_body = mock_post.call_args[1]["json"]
            assert call_body["tags"] == ["label1"]

    def test_no_tags_not_in_body(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"id":"t1"}'
        mock_resp.json.return_value = {"id": "t1"}

        with patch("requests.post", return_value=mock_resp) as mock_post:
            client.create_task(title="Test", project_id="proj1")
            call_body = mock_post.call_args[1]["json"]
            assert "tags" not in call_body


class TestUpdateTaskWithTags:
    def test_tags_in_update(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"id":"t1","tags":["new-tag"]}'
        mock_resp.json.return_value = {"id": "t1", "tags": ["new-tag"]}

        with patch("requests.post", return_value=mock_resp) as mock_post:
            client.update_task(task_id="t1", project_id="p1", tags=["new-tag"])
            call_body = mock_post.call_args[1]["json"]
            assert call_body["tags"] == ["new-tag"]
