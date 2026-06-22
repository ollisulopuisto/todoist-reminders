# todoist-reminders

Bidirectional sync between **Todoist** and **Apple Reminders** (via AppleScript).
Runs as a macOS launchd agent on a schedule. Because Apple Reminders syncs via iCloud,
changes flow automatically to all your Apple devices.

```
Todoist ↔ [this script on Mac] ↔ Apple Reminders (iCloud) ↔ iPhone / iPad / other Macs
```

## How the sync works

Depending on your configured filter and options:
- **Apple Reminders → Todoist**: Reminders added in Apple Reminders (e.g., via Siri) are copied to your Todoist Inbox.
  - **Complete-on-Import**: By default, imported reminders are immediately marked completed in Apple Reminders to keep your list clean.
- **Todoist → Apple Reminders**: Tasks are pushed to Apple Reminders to show them in widgets or sync them to other devices. This can be customized using the `--filter` parameter.

Deduplication is by **Todoist task ID**, stored in each reminder's Notes/Body field. Tasks that already exist in both are never duplicated.

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

# 3. Securely enter your Todoist API token (does not write to command history)
read -rs TODOIST_TOKEN
# (paste/type your token and press Enter)

# 4. Confirm the CLI works with a dry-run
TODOIST_TOKEN=$TODOIST_TOKEN uv run todoist-reminders --dry-run
~~~

Your Todoist API token is at: **todoist.com → Settings → Integrations → Developer → API token**

## Run manually & Sync options

You can customize the sync using the following flags:

### Sync Filters (`--filter`)
Filters determine which tasks are pushed from Todoist to Apple Reminders:
*   `--filter none`: **Ingest-only mode**. Pushes nothing from Todoist to Apple Reminders. Perfect if you only want Siri reminders imported to Todoist.
*   `--filter upcoming-due` (Recommended): Pushes tasks with a due date of today or in the future to Apple Reminders (great for iPhone widgets).
*   `--filter inbox-or-upcoming-due`: Pushes tasks in the Todoist Inbox OR tasks with a due date of today/future.
*   `--filter all` (Default): Pushes all active tasks from Todoist.
*   Other choices: `inbox`, `due`, `inbox-or-due`, `inbox-and-upcoming-due`.

### Complete on Import (`--no-complete-on-import`)
By default, new reminders imported from Apple Reminders to Todoist are immediately marked as completed in Apple Reminders to prevent list clutter. Pass `--no-complete-on-import` if you want to keep them active in Apple Reminders.

### Examples

~~~bash
# Securely load token first:
read -rs TODOIST_TOKEN

# A: Unidirectional Siri -> Todoist ingest (complete on import, push nothing back)
TODOIST_TOKEN=$TODOIST_TOKEN uv run todoist-reminders --filter none

# B: Ingest Siri tasks + push upcoming deadlines to Reminders (widget sync)
TODOIST_TOKEN=$TODOIST_TOKEN uv run todoist-reminders --filter upcoming-due

# C: Dry-run check with a custom list name (default list name is "Todoist")
TODOIST_TOKEN=$TODOIST_TOKEN uv run todoist-reminders --list "Muistutukset" --filter inbox --dry-run
~~~

## Apple Reminders Setup & Siri Integration

For the best experience (so you don't have to say "Add to my Todoist list" to Siri every time):
1. Open the Apple Reminders app and create a new list named **`Todoist`**.
2. Go to **iOS/macOS Settings → Reminders → Default List** and select the new **`Todoist`** list.
3. Now, whenever you dictate a general reminder (e.g., *"Remind me to buy milk"*), it will automatically be created on the `Todoist` list, picked up by the script, created in Todoist, and cleared from Reminders!


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
