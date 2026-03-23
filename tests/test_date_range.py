"""Tests for end_date inclusive range fix in get_completed_tasks and filter_tasks."""
import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock
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

    def test_auto_fetches_project_ids_when_dates_without_projects(self):
        """When dates are set but project_ids is None, should auto-fetch all project IDs."""
        import ticktick_mcp.src.server as server_mod

        mock_client = MagicMock()
        mock_client.get_projects.return_value = [
            {"id": "proj1", "name": "P1"},
            {"id": "proj2", "name": "P2"},
        ]
        mock_client.filter_tasks.return_value = []

        original = server_mod.ticktick
        server_mod.ticktick = mock_client
        try:
            result = asyncio.run(server_mod.filter_tasks(
                start_date="2026-03-22", end_date="2026-03-22"
            ))
            # Should have called get_projects to auto-fetch IDs
            mock_client.get_projects.assert_called_once()
            # Should have passed the project IDs to filter_tasks
            call_args = mock_client.filter_tasks.call_args
            assert call_args[0][0] == ["proj1", "proj2"]
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
            result = asyncio.run(server_mod.filter_tasks(
                project_ids=["proj1"],
                start_date="2026-03-22", end_date="2026-03-22"
            ))
            # Should NOT have called get_projects
            mock_client.get_projects.assert_not_called()
        finally:
            server_mod.ticktick = original

    def test_no_auto_fetch_when_no_dates(self):
        """When no dates are specified, should not auto-fetch project IDs."""
        import ticktick_mcp.src.server as server_mod

        mock_client = MagicMock()
        mock_client.filter_tasks.return_value = [{"id": "t1", "title": "Test", "projectId": "p1"}]

        original = server_mod.ticktick
        server_mod.ticktick = mock_client
        try:
            result = asyncio.run(server_mod.filter_tasks(status=[0]))
            mock_client.get_projects.assert_not_called()
        finally:
            server_mod.ticktick = original
