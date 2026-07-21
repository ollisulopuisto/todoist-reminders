# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project uses [Calendar Versioning](https://calver.org/) (`vYY.MM.DD.N`).

## [v26.07.21.12] - 2026-07-21

### Fixed
- Reverted AppleScript query in `fetch_apple_reminders` to fetch all list reminders safely without AppleScript error -1728.

## [v26.07.21.11] - 2026-07-21

### Fixed
- Fixed AppleScript error delay by using standard `due date` property in `fetch_apple_reminders`.

## [v26.07.21.10] - 2026-07-21

### Added
- Bidirectional due date/time sync between Apple Reminders and Todoist (`due date` / `remind me date` → Todoist `due_string`, and Todoist `due.date` → Apple `due date`).

## [v26.07.21.9] - 2026-07-21

### Added
- Added MIT License (`LICENSE` file).

## [v26.07.13.8] - 2026-07-13

### Fixed
- Fixed CLI wrapper script crash on completion. Changed `main()`'s return type from `SyncResult` to `None`. This prevents `sys.exit()` in the auto-generated `todoist-reminders` wrapper script from printing the `SyncResult` dataclass to `sys.stderr` and exiting with code `1`, which was causing launchd to register sync runs as failures.

## [v26.06.22.7] - 2026-06-22

### Fixed
- AppleScript output parsing for `todoist_id` values. If the notes/body field of a reminder was empty, AppleScript returned `"missing value"`, which was interpreted as a valid string and bypassed imports. Normalized both `"missing value"` and empty strings to `None`.

## [v26.06.22.6] - 2026-06-22

### Changed
- Updated `README.md` documentation to cover the new `--filter` and `--no-complete-on-import` parameters, secure API token load guidelines, dry-run instructions, and iPhone/iOS Siri list configuration.

## [v26.06.22.5] - 2026-06-22

### Added
- `--no-complete-on-import` CLI flag to disable the automatic completion of imported reminders in Apple Reminders.
- Support for `none` choice in `--filter` parameter to prevent pushing any Todoist tasks to Apple Reminders (ideal for unidirectional Siri-to-Todoist ingest).
- Unit tests for `complete_on_import` mode and `none` filter.

### Changed
- By default, Apple Reminders imported to Todoist are now immediately marked as completed in Apple Reminders to prevent clutter (complete-on-import mode).

## [v26.06.22.4] - 2026-06-22

### Added
- `--filter` CLI flag with choices: `all`, `inbox`, `due`, `upcoming-due`, `inbox-or-due`, `inbox-or-upcoming-due`, `inbox-and-upcoming-due` (default: `all`) to filter which Todoist tasks get pushed to Apple Reminders.
- Support for fetching the Todoist Inbox project ID dynamically to support Inbox-specific sync filters.
- Unit tests for all sync filters in `tests/test_cli.py`.

### Changed
- Sync logic now respects the `"should_push"` flag attached to tasks to avoid copying all Todoist tasks to Apple Reminders while keeping completion-tracking intact.

## [v26.06.22.3] - 2026-06-22

### Added
- `[project.scripts]` entry point: `todoist-reminders` CLI command wired to `todoist_reminders.cli:main`
- `.gitignore` covering `__pycache__`, `.venv`, caches, and secret files
- `README.md` with installation, token setup, manual run, and launchd scheduling guide
- `launchd/com.todoist-reminders.plist` template for macOS scheduled syncing every 5 minutes
- `CHANGELOG.md` (this file)

### Fixed
- Test suite: 16 broken tests repaired
  - `pytest.MockFixture` → `pytest_mock.MockFixture` (doesn't exist on the `pytest` module)
  - `mock_osascript.return_value = "string"` → `.return_value.stdout = "string"` (mock patches `subprocess.run`, which returns a `CompletedProcess`)
  - `call_args[0][0]` → `call_args[0][0][-1]` to extract the AppleScript string from the command-list argument
  - Bare `pytest.param()` positional args in `@pytest.mark.parametrize` → wrapped in a list
  - `"raw,escaped"` string as first parametrize arg (PT006) → `("raw", "escaped")` tuple
  - Broken string literal `'a"b\\c\'d'` in escape test → `"a\"b\\c'd"`
  - Unused imports removed (`Iterator`, `patch`, `call`, `AppleReminder`)
  - `test_full_cycle` missing Todoist task `t3` and linked Apple reminder for `t2`, causing two sync directions to never fire
- `main.py` stub updated to call `todoist_reminders.cli:main`

## [v26.06.22.2] - 2026-06-22

### Added
- `AGENTS.md` project conventions document

## [v26.06.22.1] - 2026-06-22

### Added
- Initial implementation: bidirectional Todoist ↔ Apple Reminders sync
- `apple_reminders.py`: AppleScript helpers with injection-safe escaping
- `sync.py`: pure bidirectional sync logic (Todoist→Apple, Apple→Todoist, both completion directions)
- `cli.py`: `ArgumentParser` CLI with `--list` and `--dry-run` flags
- `models.py`: `AppleReminder` and `SyncResult` dataclasses
- Full test suite: 54 tests covering all sync directions, escaping, parsing, dry-run, and edge cases
