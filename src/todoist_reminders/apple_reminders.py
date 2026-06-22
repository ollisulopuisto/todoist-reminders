"""AppleScript helpers for Apple Reminders."""

import subprocess

from todoist_reminders.models import AppleReminder


def run_applescript(script: str) -> str:
    """Execute an AppleScript command and return stdout."""
    result = subprocess.run(
        ["/usr/bin/osascript", "-e", script],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def escape_applescript(value: str) -> str:
    """Escape a string for safe use inside AppleScript double quotes."""
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("'", "\\'")


def ensure_list_exists(list_name: str) -> None:
    """Create the Apple Reminders list if it doesn't exist."""
    safe = escape_applescript(list_name)
    run_applescript(
        f'tell application "Reminders"\n'
        f'    if not (exists list "{safe}") then\n'
        f'        make new list with properties {{name:"{safe}"}}\n'
        f"    end if\n"
        f"end tell"
    )


def fetch_apple_reminders(list_name: str) -> list[AppleReminder]:
    """Fetch all reminders from an Apple Reminders list."""
    safe = escape_applescript(list_name)
    output = run_applescript(
        f'tell application "Reminders"\n'
        f'    set result_list to ""\n'
        f'    if exists list "{safe}" then\n'
        f'        set all_reminders to every reminder of list "{safe}"\n'
        f"        repeat with r in all_reminders\n"
        f"            set r_name to name of r\n"
        f"            set r_completed to completed of r\n"
        f'            set r_notes to ""\n'
        f"            try\n"
        f"                set r_notes to body of r\n"
        f"            end try\n"
        f"            set result_list to result_list"
        f" & r_name & tab & r_completed & tab & r_notes & linefeed\n"
        f"        end repeat\n"
        f"    end if\n"
        f"    return result_list\n"
        f"end tell"
    )
    reminders: list[AppleReminder] = []
    if not output.strip():
        return reminders
    for line in output.strip().split("\n"):
        parts = line.split("\t")
        if len(parts) >= 2:
            title = parts[0]
            completed = parts[1] == "true"
            todoist_id = parts[2] if len(parts) >= 3 and parts[2] else None
            reminders.append(AppleReminder(title=title, completed=completed, todoist_id=todoist_id))
    return reminders


def add_apple_reminder(list_name: str, title: str, todoist_id: str) -> None:
    """Add a reminder to Apple Reminders, storing the Todoist ID in notes."""
    safe_list = escape_applescript(list_name)
    safe_title = escape_applescript(title)
    safe_id = escape_applescript(todoist_id)
    ensure_list_exists(list_name)
    run_applescript(
        f'tell application "Reminders"\n'
        f'    tell list "{safe_list}"\n'
        f"        make new reminder with properties"
        f' {{name:"{safe_title}", body:"{safe_id}"}}\n'
        f"    end tell\n"
        f"end tell"
    )


def complete_apple_reminder(list_name: str, title: str) -> None:
    """Mark an Apple Reminder as completed."""
    safe_list = escape_applescript(list_name)
    safe_title = escape_applescript(title)
    run_applescript(
        f'tell application "Reminders"\n'
        f'    tell list "{safe_list}"\n'
        f"        set target to (first reminder"
        f' whose name is "{safe_title}" and completed is false)\n'
        f"        set completed of target to true\n"
        f"    end tell\n"
        f"end tell"
    )


def update_reminder_notes(list_name: str, title: str, todoist_id: str) -> None:
    """Update the notes/body of an Apple Reminder with a Todoist ID."""
    safe_list = escape_applescript(list_name)
    safe_title = escape_applescript(title)
    safe_id = escape_applescript(todoist_id)
    run_applescript(
        f'tell application "Reminders"\n'
        f'    tell list "{safe_list}"\n'
        f"        set target to (first reminder"
        f' whose name is "{safe_title}" and completed is false)\n'
        f'        set body of target to "{safe_id}"\n'
        f"    end tell\n"
        f"end tell"
    )
