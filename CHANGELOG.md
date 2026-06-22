# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project uses [Calendar Versioning](https://calver.org/) (`vYY.MM.DD.N`).

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
