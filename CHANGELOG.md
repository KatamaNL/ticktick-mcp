# Changelog

## 2026-03-23

### Fixed
- `get_completed_tasks`: same-day date queries (start=end) now return results (end_date is inclusive via +1 day offset)
- `filter_tasks`: same-day date queries now work (same +1 day fix)
- `filter_tasks`: auto-fetches all project IDs when dates are used without explicit project_ids (TickTick API returns 500 without projectIds in date-filtered requests)
