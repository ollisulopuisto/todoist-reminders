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
        f'            set r_date to ""\n'
        f"            try\n"
        f"                if due date of r is not missing value then\n"
        f"                    set d to due date of r\n"
        f"                else if remind me date of r is not missing value then\n"
        f"                    set d to remind me date of r\n"
        f"                else\n"
        f"                    set d to missing value\n"
        f"                end if\n"
        f"                if d is not missing value then\n"
        f"                    set y to year of d\n"
        f'                    set m to text -2 thru -1 of ("0" & (month of d as integer))\n'
        f'                    set day_val to text -2 thru -1 of ("0" & (day of d))\n'
        f'                    set h to text -2 thru -1 of ("0" & (hours of d))\n'
        f'                    set min_val to text -2 thru -1 of ("0" & (minutes of d))\n'
        f'                    set s to text -2 thru -1 of ("0" & (seconds of d))\n'
        f'                    if h is "00" and min_val is "00" and s is "00" then\n'
        f'                        set r_date to (y as string) & "-" & m & "-" & day_val\n'
        f"                    else\n"
        f'                        set r_date to (y as string) & "-" & m & "-" & day_val & " " & h & ":" & min_val & ":" & s\n'
        f"                    end if\n"
        f"                end if\n"
        f"            end try\n"
        f"            set result_list to result_list"
        f" & r_name & tab & r_completed & tab & r_notes & tab & r_date & linefeed\n"
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
            if todoist_id in ("missing value", ""):
                todoist_id = None
            due_date = parts[3] if len(parts) >= 4 and parts[3] else None
            if due_date in ("missing value", ""):
                due_date = None
            reminders.append(
                AppleReminder(
                    title=title,
                    completed=completed,
                    todoist_id=todoist_id,
                    due_date=due_date,
                )
            )
    return reminders


def add_apple_reminder(
    list_name: str,
    title: str,
    todoist_id: str,
    due_date: str | None = None,
) -> None:
    """Add a reminder to Apple Reminders, storing the Todoist ID in notes."""
    safe_list = escape_applescript(list_name)
    safe_title = escape_applescript(title)
    safe_id = escape_applescript(todoist_id)
    ensure_list_exists(list_name)

    date_script = ""
    if due_date:
        try:
            clean_date = due_date.replace("T", " ").replace("Z", "").split(".")[0]
            parts = clean_date.split(" ")
            ymd = parts[0].split("-")
            year, month, day = int(ymd[0]), int(ymd[1]), int(ymd[2])
            hour, minute, second = 0, 0, 0
            if len(parts) > 1 and ":" in parts[1]:
                hms = parts[1].split(":")
                hour = int(hms[0])
                minute = int(hms[1])
                second = int(hms[2]) if len(hms) > 2 else 0

            date_script = (
                f"        set new_date to (current date)\n"
                f"        set year of new_date to {year}\n"
                f"        set month of new_date to {month}\n"
                f"        set day of new_date to {day}\n"
                f"        set hours of new_date to {hour}\n"
                f"        set minutes of new_date to {minute}\n"
                f"        set seconds of new_date to {second}\n"
                f"        set due date of new_rem to new_date\n"
            )
        except Exception:
            date_script = ""

    run_applescript(
        f'tell application "Reminders"\n'
        f'    tell list "{safe_list}"\n'
        f"        set new_rem to make new reminder with properties"
        f' {{name:"{safe_title}", body:"{safe_id}"}}\n'
        f"{date_script}"
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
