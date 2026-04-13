# Changelog

## 2026-04-13

### Changed
- Migratie van pip (requirements.txt + setup.py) naar uv (pyproject.toml + uv.lock) (@herriaan)
- README instructies bijgewerkt voor uv (@herriaan)

## 2026-03-30

### Fixed
- `filter_tasks`: auto-fetch excludes NOTE-kind projects (only TASK projects), preventing TickTick API 500 errors
- `filter_tasks`: client-side fallback when TickTick filter API returns 500 (fetches tasks per project and filters locally by project, date, priority, tags, status)

## 2026-03-23 (v2)

### Fixed
- **start_date sync bug (CRITICAL)**: `create_task`, `update_task`, `batch_create_tasks`, `batch_update_tasks` now auto-set `start_date = due_date` when `due_date` is provided but `start_date` is not. TickTick's "Today" view uses `startDate` to display tasks, so without this fix tasks with only `dueDate` set would still appear in "Today" even after rescheduling.

### Added
- `update_project` MCP tool: update project name, color, viewMode, and kind
- `desc` field support in `create_task`, `update_task`, `batch_create_tasks`, `batch_update_tasks` (checklist description)
- `reminders` field support in `create_task`, `update_task`, `batch_create_tasks`, `batch_update_tasks` (e.g. `["TRIGGER:PT0S"]`)
- `items` field support in `create_task`, `update_task`, `batch_create_tasks`, `batch_update_tasks` (inline subtasks array)
- `format_task` now displays `desc`, `reminders` fields in output
- Tests for all new features in `tests/test_start_date_sync.py`

## 2026-03-23

### Fixed
- `get_completed_tasks`: same-day date queries (start=end) now return results (end_date is inclusive via +1 day offset)
- `filter_tasks`: same-day date queries now work (same +1 day fix)
- `filter_tasks`: auto-fetches all project IDs when dates are used without explicit project_ids (TickTick API returns 500 without projectIds in date-filtered requests)
- `update_task` / `batch_update_tasks`: no longer reset `isAllDay` to false when not explicitly provided (now fetches current value from API)
- `batch_create_tasks`: tags are now passed through to the API (were silently ignored)
- `batch_create_tasks`: now supports "vandaag"/"morgen"/"overmorgen" and YYYY-MM-DD date formats (was ISO-only)
