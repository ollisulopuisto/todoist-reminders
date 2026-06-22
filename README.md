# todoist-reminders

Bidirectional sync between **Todoist** and **Apple Reminders** (via AppleScript).
Runs as a macOS launchd agent on a schedule. Because Apple Reminders syncs via iCloud,
changes flow automatically to all your Apple devices.

```
Todoist ↔ [this script on Mac] ↔ Apple Reminders (iCloud) ↔ iPhone / iPad / other Macs
```

## How the sync works

| Situation | Action |
|-----------|--------|
| Task in Todoist, not in Apple Reminders | Created in Apple Reminders |
| Reminder in Apple (no Todoist ID, no matching content) | Created in Todoist |
| Reminder completed in Apple | Completed in Todoist |
| Task completed in Todoist | Completed in Apple Reminders |

Deduplication is by **Todoist task ID**, stored in each reminder's Notes field.
Tasks that already exist in both are never duplicated.

## Requirements

- macOS with Apple Reminders (iCloud sync recommended)
- Python 3.13+
- [`uv`](https://docs.astral.sh/uv/) for dependency management

## Installation

~~~bash
# 1. Clone / go to the project
cd ~/Documents/koodi/todoist-reminders

# 2. Install the package and its dependencies into the local venv
uv pip install -e .

# 3. Confirm the CLI works
TODOIST_TOKEN=your_token_here uv run todoist-reminders --dry-run
~~~

Your Todoist API token is at: **todoist.com → Settings → Integrations → API token**

## Run manually

~~~bash
export TODOIST_TOKEN=your_token_here

# Dry-run (shows what would happen, changes nothing)
uv run todoist-reminders --dry-run

# Live sync (default list name: "Todoist")
uv run todoist-reminders

# Sync into a different Reminders list
uv run todoist-reminders --list "Work"
~~~

## Schedule with launchd (runs every 5 minutes)

~~~bash
# 1. Copy the template
cp launchd/com.todoist-reminders.plist ~/Library/LaunchAgents/com.todoist-reminders.plist

# 2. Fill in your real API token
#    Open ~/Library/LaunchAgents/com.todoist-reminders.plist
#    Replace YOUR_TODOIST_API_TOKEN_HERE with your actual token

# 3. Reinstall the package so the venv script exists
uv pip install -e .

# 4. Load the agent
launchctl load ~/Library/LaunchAgents/com.todoist-reminders.plist

# 5. Check it's running
launchctl list | grep todoist
~~~

### Useful commands

~~~bash
# Watch the log in real time
tail -f ~/Library/Logs/todoist-reminders.log

# Unload / stop the agent
launchctl unload ~/Library/LaunchAgents/com.todoist-reminders.plist

# Reload after editing the plist
launchctl unload ~/Library/LaunchAgents/com.todoist-reminders.plist
launchctl load   ~/Library/LaunchAgents/com.todoist-reminders.plist

# Trigger an immediate sync (without waiting for the 5-min interval)
launchctl start com.todoist-reminders
~~~

## Development

~~~bash
# Run the full quality suite before committing
uv run ruff check src/ tests/
uv run mypy src/
uv run pytest
~~~

## Security note

The plist in `~/Library/LaunchAgents/` contains your Todoist API token in plaintext.
It is readable only by your user account (`-rw-------`). Do **not** commit that file to git —
only the template in `launchd/` (which contains a placeholder) is tracked.
