"""Tests for end_date inclusive range fix in get_completed_tasks and filter_tasks."""

from datetime import date, timedelta
from unittest.mock import MagicMock
import asyncio

from ticktick_mcp.src.timezone import parse_local_date, to_ticktick_utc


class TestEndDateInclusive:
    """Verify that end_date is converted to end-of-day (next day midnight)."""

    def test_same_day_range_produces_different_utc(self):
        """When start=end='2026-03-22', end UTC should be 1 day later than start."""
        d = parse_local_date("2026-03-22")
        sd = to_ticktick_utc(d)
        ed = to_ticktick_utc(d + timedelta(days=1))
        assert sd != ed, "start and end must differ for same-day queries"
        # end should be exactly 24h later
        assert sd == "2026-03-21T23:00:00+0000"  # midnight CET Mar 22
        assert ed == "2026-03-22T23:00:00+0000"  # midnight CET Mar 23

    def test_single_day_range_spans_24h(self):
        """A single-day query should produce a 24h window."""
        d = parse_local_date("2026-03-15")
        sd = to_ticktick_utc(d)
        ed = to_ticktick_utc(d + timedelta(days=1))
        # Both should be T23:00:00 (CET winter) but different dates
        assert "2026-03-14T23:00:00+0000" == sd
        assert "2026-03-15T23:00:00+0000" == ed

    def test_multi_day_range(self):
        """A multi-day range should extend end by 1 day."""
        start = parse_local_date("2026-03-20")
        end = parse_local_date("2026-03-23")
        sd = to_ticktick_utc(start)
        ed = to_ticktick_utc(end + timedelta(days=1))
        assert sd == "2026-03-19T23:00:00+0000"
        assert ed == "2026-03-23T23:00:00+0000"

    def test_dst_boundary(self):
        """DST switch is at 02:00, so midnight Mar 29 is still CET (UTC+1)."""
        d = parse_local_date("2026-03-29")
        utc = to_ticktick_utc(d)
        # Midnight Mar 29 is before the 02:00 switch, so still CET (23:00 UTC)
        assert utc == "2026-03-28T23:00:00+0000"
        # But Mar 30 midnight IS CEST (22:00 UTC)
        d2 = parse_local_date("2026-03-30")
        utc2 = to_ticktick_utc(d2)
        assert utc2 == "2026-03-29T22:00:00+0000"

    def test_smart_date_vandaag(self):
        """'vandaag' should parse to today."""
        today = date.today()
        parsed = parse_local_date("vandaag")
        assert parsed == today

    def test_smart_date_morgen(self):
        """'morgen' should parse to tomorrow."""
        tomorrow = date.today() + timedelta(days=1)
        parsed = parse_local_date("morgen")
        assert parsed == tomorrow


class TestFilterTasksAutoProjectIds:
    """Verify that filter_tasks auto-fetches project IDs when dates are used without project_ids."""

    def test_auto_fetches_only_task_projects(self):
        """When auto-fetching, should exclude NOTE-kind projects."""
        import ticktick_mcp.src.server as server_mod

        mock_client = MagicMock()
        mock_client.get_projects.return_value = [
            {"id": "proj1", "name": "P1", "kind": "TASK"},
            {"id": "proj2", "name": "P2 Notes", "kind": "NOTE"},
            {"id": "proj3", "name": "P3"},  # no kind = defaults to TASK
        ]
        mock_client.filter_tasks.return_value = []

        original = server_mod.ticktick
        server_mod.ticktick = mock_client
        try:
            asyncio.run(
                server_mod.filter_tasks(start_date="2026-03-22", end_date="2026-03-22")
            )
            mock_client.get_projects.assert_called_once()
            call_args = mock_client.filter_tasks.call_args
            # Should only include TASK-kind projects (proj2 with NOTE excluded)
            assert call_args[0][0] == ["proj1", "proj3"]
        finally:
            server_mod.ticktick = original

    def test_no_auto_fetch_when_project_ids_provided(self):
        """When project_ids are explicitly provided, should not auto-fetch."""
        import ticktick_mcp.src.server as server_mod

        mock_client = MagicMock()
        mock_client.filter_tasks.return_value = []

        original = server_mod.ticktick
        server_mod.ticktick = mock_client
        try:
            asyncio.run(
                server_mod.filter_tasks(
                    project_ids=["proj1"],
                    start_date="2026-03-22",
                    end_date="2026-03-22",
                )
            )
            mock_client.get_projects.assert_not_called()
        finally:
            server_mod.ticktick = original

    def test_no_auto_fetch_when_no_dates(self):
        """When no dates are specified, should not auto-fetch project IDs."""
        import ticktick_mcp.src.server as server_mod

        mock_client = MagicMock()
        mock_client.filter_tasks.return_value = [
            {"id": "t1", "title": "Test", "projectId": "p1"}
        ]

        original = server_mod.ticktick
        server_mod.ticktick = mock_client
        try:
            asyncio.run(server_mod.filter_tasks(status=[0]))
            mock_client.get_projects.assert_not_called()
        finally:
            server_mod.ticktick = original

    def test_fallback_on_api_500(self):
        """When filter API returns error, should fall back to client-side filtering."""
        import ticktick_mcp.src.server as server_mod

        mock_client = MagicMock()
        mock_client.get_projects.return_value = [
            {"id": "proj1", "name": "P1", "kind": "TASK"},
        ]
        mock_client.filter_tasks.return_value = {"error": "500 Server Error"}
        mock_client.get_project_with_data.return_value = {
            "tasks": [
                {
                    "id": "t1",
                    "title": "Today task",
                    "projectId": "proj1",
                    "startDate": to_ticktick_utc(date(2026, 3, 22)),
                    "status": 0,
                    "priority": 3,
                },
                {
                    "id": "t2",
                    "title": "Tomorrow task",
                    "projectId": "proj1",
                    "startDate": to_ticktick_utc(date(2026, 3, 23)),
                    "status": 0,
                    "priority": 0,
                },
            ]
        }

        original = server_mod.ticktick
        server_mod.ticktick = mock_client
        try:
            result = asyncio.run(
                server_mod.filter_tasks(start_date="2026-03-22", end_date="2026-03-22")
            )
            # Should have fallen back to client-side filtering
            mock_client.get_project_with_data.assert_called_once_with("proj1")
            assert "Today task" in result
            assert "Tomorrow task" not in result
        finally:
            server_mod.ticktick = original


class TestFilterTasksClientSide:
    """Test the _filter_tasks_client_side helper."""

    def test_filter_by_project(self):
        from ticktick_mcp.src.server import _filter_tasks_client_side

        tasks = [
            {"id": "t1", "projectId": "p1", "status": 0},
            {"id": "t2", "projectId": "p2", "status": 0},
        ]
        result = _filter_tasks_client_side(tasks, project_ids=["p1"])
        assert len(result) == 1
        assert result[0]["id"] == "t1"

    def test_filter_by_priority(self):
        from ticktick_mcp.src.server import _filter_tasks_client_side

        tasks = [
            {"id": "t1", "priority": 5, "status": 0},
            {"id": "t2", "priority": 0, "status": 0},
        ]
        result = _filter_tasks_client_side(tasks, priority=[5])
        assert len(result) == 1
        assert result[0]["id"] == "t1"

    def test_filter_by_tags(self):
        from ticktick_mcp.src.server import _filter_tasks_client_side

        tasks = [
            {"id": "t1", "tags": ["Dev", "Blogic"], "status": 0},
            {"id": "t2", "tags": ["Admin"], "status": 0},
            {"id": "t3", "status": 0},  # no tags
        ]
        result = _filter_tasks_client_side(tasks, tags=["Dev"])
        assert len(result) == 1
        assert result[0]["id"] == "t1"

    def test_filter_by_status(self):
        from ticktick_mcp.src.server import _filter_tasks_client_side

        tasks = [
            {"id": "t1", "status": 0},
            {"id": "t2", "status": 2},
        ]
        result = _filter_tasks_client_side(tasks, status=[0])
        assert len(result) == 1
        assert result[0]["id"] == "t1"

    def test_filter_by_date_range(self):
        from ticktick_mcp.src.server import _filter_tasks_client_side

        tasks = [
            {"id": "t1", "startDate": to_ticktick_utc(date(2026, 3, 22)), "status": 0},
            {"id": "t2", "startDate": to_ticktick_utc(date(2026, 3, 24)), "status": 0},
            {"id": "t3", "status": 0},  # no date - excluded
        ]
        result = _filter_tasks_client_side(
            tasks, local_start=date(2026, 3, 22), local_end=date(2026, 3, 23)
        )
        assert len(result) == 1
        assert result[0]["id"] == "t1"
