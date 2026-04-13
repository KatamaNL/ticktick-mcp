"""Tests for start_date auto-sync and new task/project features."""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
from ticktick_mcp.src.ticktick_client import TickTickClient
import ticktick_mcp.src.server as server_mod
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


@pytest.fixture
def mock_ticktick():
    """Mock the ticktick client in server module."""
    mock_client = MagicMock()
    original = server_mod.ticktick
    server_mod.ticktick = mock_client
    yield mock_client
    server_mod.ticktick = original


# ============================================================================
# Task 1: start_date sync tests
# ============================================================================


class TestStartDateSyncCreateTask:
    """Verify that create_task auto-sets start_date when only due_date is provided."""

    def test_due_date_only_syncs_start_date(self, mock_ticktick):
        """When due_date is set but start_date is not, start_date should equal due_date."""
        mock_ticktick.create_task.return_value = {
            "id": "t1",
            "title": "Test",
            "projectId": "p1",
            "startDate": "2026-03-24T23:00:00+0000",
            "dueDate": "2026-03-24T23:00:00+0000",
        }
        asyncio.run(
            server_mod.create_task(title="Test", project_id="p1", due_date="2026-03-25")
        )
        call_kwargs = mock_ticktick.create_task.call_args[1]
        assert call_kwargs["start_date"] == call_kwargs["due_date"]
        assert call_kwargs["start_date"] is not None

    def test_both_dates_provided_no_override(self, mock_ticktick):
        """When both dates are provided, start_date should not be overridden."""
        mock_ticktick.create_task.return_value = {
            "id": "t1",
            "title": "Test",
            "projectId": "p1",
            "startDate": "2026-03-23T23:00:00+0000",
            "dueDate": "2026-03-24T23:00:00+0000",
        }
        asyncio.run(
            server_mod.create_task(
                title="Test",
                project_id="p1",
                start_date="2026-03-24",
                due_date="2026-03-25",
            )
        )
        call_kwargs = mock_ticktick.create_task.call_args[1]
        # start_date should NOT equal due_date since both were provided
        assert call_kwargs["start_date"] != call_kwargs["due_date"]

    def test_no_dates_no_sync(self, mock_ticktick):
        """When neither date is provided, both should remain None."""
        mock_ticktick.create_task.return_value = {
            "id": "t1",
            "title": "Test",
            "projectId": "p1",
        }
        asyncio.run(server_mod.create_task(title="Test", project_id="p1"))
        call_kwargs = mock_ticktick.create_task.call_args[1]
        assert call_kwargs["start_date"] is None
        assert call_kwargs["due_date"] is None

    def test_iso_date_sync(self, mock_ticktick):
        """ISO format due_date should also trigger start_date sync."""
        mock_ticktick.create_task.return_value = {
            "id": "t1",
            "title": "Test",
            "projectId": "p1",
            "startDate": "2026-03-25T10:00:00+0000",
            "dueDate": "2026-03-25T10:00:00+0000",
        }
        asyncio.run(
            server_mod.create_task(
                title="Test", project_id="p1", due_date="2026-03-25T10:00:00+0000"
            )
        )
        call_kwargs = mock_ticktick.create_task.call_args[1]
        assert call_kwargs["start_date"] == "2026-03-25T10:00:00+0000"


class TestStartDateSyncUpdateTask:
    """Verify that update_task auto-sets start_date when only due_date is provided."""

    def test_due_date_only_syncs_start_date(self, mock_ticktick):
        """When due_date is set but start_date is not, start_date should equal due_date."""
        mock_ticktick.update_task.return_value = {
            "id": "t1",
            "title": "Test",
            "projectId": "p1",
            "startDate": "2026-03-24T23:00:00+0000",
            "dueDate": "2026-03-24T23:00:00+0000",
        }
        asyncio.run(
            server_mod.update_task(task_id="t1", project_id="p1", due_date="2026-03-25")
        )
        call_kwargs = mock_ticktick.update_task.call_args[1]
        assert call_kwargs["start_date"] == call_kwargs["due_date"]
        assert call_kwargs["start_date"] is not None

    def test_both_dates_provided_no_override(self, mock_ticktick):
        """When both dates are provided, start_date should not be overridden."""
        mock_ticktick.update_task.return_value = {
            "id": "t1",
            "title": "Test",
            "projectId": "p1",
            "startDate": "2026-03-23T23:00:00+0000",
            "dueDate": "2026-03-24T23:00:00+0000",
        }
        asyncio.run(
            server_mod.update_task(
                task_id="t1",
                project_id="p1",
                start_date="2026-03-24",
                due_date="2026-03-25",
            )
        )
        call_kwargs = mock_ticktick.update_task.call_args[1]
        assert call_kwargs["start_date"] != call_kwargs["due_date"]

    def test_no_dates_no_sync(self, mock_ticktick):
        """When neither date is provided, both should remain None."""
        mock_ticktick.update_task.return_value = {
            "id": "t1",
            "title": "Test",
            "projectId": "p1",
        }
        asyncio.run(
            server_mod.update_task(task_id="t1", project_id="p1", title="New Title")
        )
        call_kwargs = mock_ticktick.update_task.call_args[1]
        assert call_kwargs["start_date"] is None
        assert call_kwargs["due_date"] is None


class TestStartDateSyncBatchUpdateTasks:
    """Verify that batch_update_tasks auto-sets start_date per task."""

    def test_due_date_only_syncs_start_date(self, mock_ticktick):
        """When due_date is set but start_date is not, start_date should equal due_date."""
        mock_ticktick.update_task.return_value = {"id": "t1", "title": "Test"}
        asyncio.run(
            server_mod.batch_update_tasks(
                [{"task_id": "t1", "project_id": "p1", "due_date": "2026-03-25"}]
            )
        )
        call_kwargs = mock_ticktick.update_task.call_args[1]
        assert call_kwargs["start_date"] == call_kwargs["due_date"]
        assert call_kwargs["start_date"] is not None

    def test_both_dates_no_override(self, mock_ticktick):
        """When both dates are provided, start_date should not be overridden."""
        mock_ticktick.update_task.return_value = {"id": "t1", "title": "Test"}
        asyncio.run(
            server_mod.batch_update_tasks(
                [
                    {
                        "task_id": "t1",
                        "project_id": "p1",
                        "start_date": "2026-03-24",
                        "due_date": "2026-03-25",
                    }
                ]
            )
        )
        call_kwargs = mock_ticktick.update_task.call_args[1]
        assert call_kwargs["start_date"] != call_kwargs["due_date"]

    def test_no_dates_no_sync(self, mock_ticktick):
        """When neither date is provided, both should remain None."""
        mock_ticktick.update_task.return_value = {"id": "t1", "title": "Test"}
        asyncio.run(
            server_mod.batch_update_tasks(
                [{"task_id": "t1", "project_id": "p1", "title": "New"}]
            )
        )
        call_kwargs = mock_ticktick.update_task.call_args[1]
        assert call_kwargs["start_date"] is None
        assert call_kwargs["due_date"] is None


class TestStartDateSyncBatchCreateTasks:
    """Verify that batch_create_tasks auto-sets start_date per task."""

    def test_due_date_only_syncs_start_date(self, mock_ticktick):
        """When due_date is set but start_date is not, start_date should equal due_date."""
        mock_ticktick.create_task.return_value = {"id": "t1", "title": "Test"}
        asyncio.run(
            server_mod.batch_create_tasks(
                [{"title": "Test", "project_id": "p1", "due_date": "2026-03-25"}]
            )
        )
        call_kwargs = mock_ticktick.create_task.call_args[1]
        assert call_kwargs["start_date"] == call_kwargs["due_date"]
        assert call_kwargs["start_date"] is not None

    def test_both_dates_no_override(self, mock_ticktick):
        """When both dates are provided, start_date should not be overridden."""
        mock_ticktick.create_task.return_value = {"id": "t1", "title": "Test"}
        asyncio.run(
            server_mod.batch_create_tasks(
                [
                    {
                        "title": "Test",
                        "project_id": "p1",
                        "start_date": "2026-03-24",
                        "due_date": "2026-03-25",
                    }
                ]
            )
        )
        call_kwargs = mock_ticktick.create_task.call_args[1]
        assert call_kwargs["start_date"] != call_kwargs["due_date"]


# ============================================================================
# Task 2: New API fields (desc, reminders, items)
# ============================================================================


class TestClientDescField:
    """Verify desc field is passed through in client methods."""

    def test_create_task_with_desc(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"id":"t1","desc":"My description"}'
        mock_resp.json.return_value = {"id": "t1", "desc": "My description"}

        with patch("requests.post", return_value=mock_resp) as mock_post:
            client.create_task(title="Test", project_id="p1", desc="My description")
            body = mock_post.call_args[1]["json"]
            assert body["desc"] == "My description"

    def test_update_task_with_desc(self, client):
        # Mock the GET for isAllDay preservation
        mock_get = MagicMock()
        mock_get.status_code = 200
        mock_get.text = '{"id":"t1","isAllDay":true}'
        mock_get.json.return_value = {"id": "t1", "isAllDay": True}

        mock_post = MagicMock()
        mock_post.status_code = 200
        mock_post.text = '{"id":"t1","desc":"Updated desc"}'
        mock_post.json.return_value = {"id": "t1", "desc": "Updated desc"}

        with (
            patch("requests.get", return_value=mock_get),
            patch("requests.post", return_value=mock_post) as mock_post_call,
        ):
            client.update_task(task_id="t1", project_id="p1", desc="Updated desc")
            body = mock_post_call.call_args[1]["json"]
            assert body["desc"] == "Updated desc"


class TestClientRemindersField:
    """Verify reminders field is passed through in client methods."""

    def test_create_task_with_reminders(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"id":"t1"}'
        mock_resp.json.return_value = {"id": "t1"}

        with patch("requests.post", return_value=mock_resp) as mock_post:
            client.create_task(
                title="Test",
                project_id="p1",
                reminders=["TRIGGER:P0DT9H0M0S", "TRIGGER:PT0S"],
            )
            body = mock_post.call_args[1]["json"]
            assert body["reminders"] == ["TRIGGER:P0DT9H0M0S", "TRIGGER:PT0S"]

    def test_update_task_with_reminders(self, client):
        mock_get = MagicMock()
        mock_get.status_code = 200
        mock_get.text = '{"id":"t1","isAllDay":true}'
        mock_get.json.return_value = {"id": "t1", "isAllDay": True}

        mock_post = MagicMock()
        mock_post.status_code = 200
        mock_post.text = '{"id":"t1"}'
        mock_post.json.return_value = {"id": "t1"}

        with (
            patch("requests.get", return_value=mock_get),
            patch("requests.post", return_value=mock_post) as mock_post_call,
        ):
            client.update_task(
                task_id="t1", project_id="p1", reminders=["TRIGGER:PT0S"]
            )
            body = mock_post_call.call_args[1]["json"]
            assert body["reminders"] == ["TRIGGER:PT0S"]


class TestClientItemsField:
    """Verify items (subtasks array) field is passed through in client methods."""

    def test_create_task_with_items(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"id":"t1"}'
        mock_resp.json.return_value = {"id": "t1"}

        items = [
            {"title": "Subtask 1", "status": 0},
            {"title": "Subtask 2", "status": 0},
        ]
        with patch("requests.post", return_value=mock_resp) as mock_post:
            client.create_task(title="Test", project_id="p1", items=items)
            body = mock_post.call_args[1]["json"]
            assert body["items"] == items

    def test_update_task_with_items(self, client):
        mock_get = MagicMock()
        mock_get.status_code = 200
        mock_get.text = '{"id":"t1","isAllDay":true}'
        mock_get.json.return_value = {"id": "t1", "isAllDay": True}

        mock_post = MagicMock()
        mock_post.status_code = 200
        mock_post.text = '{"id":"t1"}'
        mock_post.json.return_value = {"id": "t1"}

        items = [{"title": "Subtask 1", "status": 1}]
        with (
            patch("requests.get", return_value=mock_get),
            patch("requests.post", return_value=mock_post) as mock_post_call,
        ):
            client.update_task(task_id="t1", project_id="p1", items=items)
            body = mock_post_call.call_args[1]["json"]
            assert body["items"] == items


class TestClientNoFieldsWhenEmpty:
    """Fields should not appear in request body when not provided."""

    def test_no_desc_reminders_items_when_not_provided(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"id":"t1"}'
        mock_resp.json.return_value = {"id": "t1"}

        with patch("requests.post", return_value=mock_resp) as mock_post:
            client.create_task(title="Test", project_id="p1")
            body = mock_post.call_args[1]["json"]
            assert "desc" not in body
            assert "reminders" not in body
            assert "items" not in body


# ============================================================================
# Task 2: update_project MCP tool
# ============================================================================


class TestUpdateProjectTool:
    """Verify update_project MCP tool."""

    def test_update_project_name(self, mock_ticktick):
        mock_ticktick.update_project.return_value = {
            "id": "p1",
            "name": "New Name",
            "color": "#F18181",
        }
        result = asyncio.run(
            server_mod.update_project(project_id="p1", name="New Name")
        )
        assert "New Name" in result
        mock_ticktick.update_project.assert_called_once_with(
            project_id="p1", name="New Name", color=None, view_mode=None, kind=None
        )

    def test_update_project_invalid_view_mode(self, mock_ticktick):
        result = asyncio.run(
            server_mod.update_project(project_id="p1", view_mode="invalid")
        )
        assert "Invalid view_mode" in result

    def test_update_project_invalid_kind(self, mock_ticktick):
        result = asyncio.run(server_mod.update_project(project_id="p1", kind="INVALID"))
        assert "Invalid kind" in result

    def test_update_project_all_fields(self, mock_ticktick):
        mock_ticktick.update_project.return_value = {
            "id": "p1",
            "name": "Updated",
            "color": "#000000",
            "viewMode": "kanban",
            "kind": "NOTE",
        }
        result = asyncio.run(
            server_mod.update_project(
                project_id="p1",
                name="Updated",
                color="#000000",
                view_mode="kanban",
                kind="NOTE",
            )
        )
        assert "Updated" in result


# ============================================================================
# Task 2: Server-level desc/reminders/items passthrough
# ============================================================================


class TestServerDescRemindersItems:
    """Verify server tool handlers pass desc, reminders, items to client."""

    def test_create_task_passes_all_new_fields(self, mock_ticktick):
        mock_ticktick.create_task.return_value = {
            "id": "t1",
            "title": "Test",
            "projectId": "p1",
        }
        items = [{"title": "Sub", "status": 0}]
        asyncio.run(
            server_mod.create_task(
                title="Test",
                project_id="p1",
                desc="My desc",
                reminders=["TRIGGER:PT0S"],
                items=items,
            )
        )
        call_kwargs = mock_ticktick.create_task.call_args[1]
        assert call_kwargs["desc"] == "My desc"
        assert call_kwargs["reminders"] == ["TRIGGER:PT0S"]
        assert call_kwargs["items"] == items

    def test_update_task_passes_all_new_fields(self, mock_ticktick):
        mock_ticktick.update_task.return_value = {
            "id": "t1",
            "title": "Test",
            "projectId": "p1",
        }
        items = [{"title": "Sub", "status": 1}]
        asyncio.run(
            server_mod.update_task(
                task_id="t1",
                project_id="p1",
                desc="Updated desc",
                reminders=["TRIGGER:P0DT9H0M0S"],
                items=items,
            )
        )
        call_kwargs = mock_ticktick.update_task.call_args[1]
        assert call_kwargs["desc"] == "Updated desc"
        assert call_kwargs["reminders"] == ["TRIGGER:P0DT9H0M0S"]
        assert call_kwargs["items"] == items

    def test_batch_update_passes_new_fields(self, mock_ticktick):
        mock_ticktick.update_task.return_value = {"id": "t1", "title": "Test"}
        asyncio.run(
            server_mod.batch_update_tasks(
                [
                    {
                        "task_id": "t1",
                        "project_id": "p1",
                        "desc": "Desc",
                        "reminders": ["TRIGGER:PT0S"],
                        "items": [{"title": "Sub"}],
                    }
                ]
            )
        )
        call_kwargs = mock_ticktick.update_task.call_args[1]
        assert call_kwargs["desc"] == "Desc"
        assert call_kwargs["reminders"] == ["TRIGGER:PT0S"]
        assert call_kwargs["items"] == [{"title": "Sub"}]

    def test_batch_create_passes_new_fields(self, mock_ticktick):
        mock_ticktick.create_task.return_value = {"id": "t1", "title": "Test"}
        asyncio.run(
            server_mod.batch_create_tasks(
                [
                    {
                        "title": "Test",
                        "project_id": "p1",
                        "desc": "Desc",
                        "reminders": ["TRIGGER:PT0S"],
                        "items": [{"title": "Sub"}],
                    }
                ]
            )
        )
        call_kwargs = mock_ticktick.create_task.call_args[1]
        assert call_kwargs["desc"] == "Desc"
        assert call_kwargs["reminders"] == ["TRIGGER:PT0S"]
        assert call_kwargs["items"] == [{"title": "Sub"}]


# ============================================================================
# Format task tests for new fields
# ============================================================================


class TestFormatTaskNewFields:
    """Verify format_task displays desc, reminders correctly."""

    def test_format_task_with_desc(self):
        task = {"id": "t1", "title": "Test", "desc": "My checklist description"}
        formatted = server_mod.format_task(task)
        assert "Description:" in formatted
        assert "My checklist description" in formatted

    def test_format_task_with_reminders(self):
        task = {
            "id": "t1",
            "title": "Test",
            "reminders": ["TRIGGER:PT0S", "TRIGGER:P0DT9H0M0S"],
        }
        formatted = server_mod.format_task(task)
        assert "Reminders:" in formatted
        assert "TRIGGER:PT0S" in formatted

    def test_format_task_without_new_fields(self):
        task = {"id": "t1", "title": "Test"}
        formatted = server_mod.format_task(task)
        assert "Description:" not in formatted
        assert "Reminders:" not in formatted
