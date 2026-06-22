# AGENTS.md

## Project

Bidirectional sync between **Todoist** and **Apple Reminders**. Runs on macOS
(as a Mac Mini helper script). Uses Todoist REST API and AppleScript for
Reminders.

## Stack & Layout

- **Python 3.13**, managed by **uv** (not pip/venv)
- Source: `src/todoist_reminders/` (editable install via `uv pip install -e .`)
- Tests: `tests/`
- Packages: `todoist-api-python`, `pytest`, `pytest-mock`, `mypy`, `ruff`

```txt
__init__.py          re-exports AppleReminder, SyncResult, sync
apple_reminders.py   AppleScript subprocess helpers (CRUD + escaping)
models.py            AppleReminder, SyncResult dataclasses
sync.py              Pure sync logic (no AppleScript calls, testable)
cli.py               ArgumentParser entrypoint, env var, orchestration
```

## Dev Workflow

Every change must pass **all three** before committing:

```bash
uv run ruff check src/ tests/   # lint
uv run mypy src/                # typecheck
uv run pytest                   # tests
```

- Token lives in `TODOIST_TOKEN` env var, never in source.
- Use `uv run ...` — the project venv is in `.venv/`.

## Key Conventions

- **`get_tasks()` returns `Iterator[list[Task]]`** (batches), not flat list.
  `cli.py` flattens with `chain.from_iterable`.
- **Dedup by Todoist ID** (stored in Apple Reminder's `body`/notes field),
  not by content text.
- **AppleScript escaping**: use `escape_applescript()` for every string
  interpolated into osascript. Never raw f-strings with user content.
- **`subprocess.run` uses `check=True`** and full path `/usr/bin/osascript`.
- Sync tests mock `add_apple_reminder`, `complete_apple_reminder`,
  `update_reminder_notes` at the `todoist_reminders.sync` boundary.
- `sync()` accepts `list[dict]` for Todoist tasks (not Task dataclass)
  to keep the sync layer decoupled from the API library.
