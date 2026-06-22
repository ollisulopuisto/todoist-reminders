"""Core bidirectional sync logic."""

from todoist_api_python.api import TodoistAPI

from todoist_reminders.apple_reminders import (
    add_apple_reminder,
    complete_apple_reminder,
    update_reminder_notes,
)
from todoist_reminders.models import AppleReminder, SyncResult


def sync(
    todoist_tasks: list[dict[str, object]],
    apple_reminders: list[AppleReminder],
    list_name: str,
    todoist_client: TodoistAPI,
    dry_run: bool = False,
) -> SyncResult:
    """
    Bidirectional sync between Todoist tasks and Apple Reminders.

    - Todoist tasks not in Apple Reminders -> create in Apple
    - Apple Reminders (without todoist_id) not in Todoist -> create in Todoist
    - Completed in Apple but not in Todoist -> complete in Todoist
    - Completed in Todoist but not in Apple -> complete in Apple
    """
    result = SyncResult()

    # Build lookup maps
    todoist_by_id: dict[str, dict[str, object]] = {}
    todoist_by_content: dict[str, dict[str, object]] = {}
    for task in todoist_tasks:
        todoist_by_id[str(task["id"])] = task
        todoist_by_content[str(task["content"])] = task

    apple_by_id: dict[str, AppleReminder] = {}
    apple_by_title: dict[str, AppleReminder] = {}
    for rem in apple_reminders:
        apple_by_title[rem.title] = rem
        if rem.todoist_id:
            apple_by_id[rem.todoist_id] = rem

    # 1. Todoist -> Apple: push tasks that don't exist in Apple
    for task in todoist_tasks:
        if task.get("is_completed"):
            continue
        content = str(task["content"])
        if content not in apple_by_title:
            if not dry_run:
                add_apple_reminder(list_name, content, str(task["id"]))
            result.todoist_to_apple.append(content)

    # 2. Apple -> Todoist: push reminders that have no todoist_id and no matching
    #    content
    for rem in apple_reminders:
        if rem.completed:
            continue
        if rem.todoist_id is None and rem.title not in todoist_by_content:
            if not dry_run:
                new_task = todoist_client.add_task(content=rem.title)
                update_reminder_notes(list_name, rem.title, new_task.id)
            result.apple_to_todoist.append(rem.title)

    # 3. Apple completed -> complete in Todoist
    for rem in apple_reminders:
        if rem.completed and rem.todoist_id and rem.todoist_id in todoist_by_id:
            task = todoist_by_id[rem.todoist_id]
            if not task.get("is_completed"):
                if not dry_run:
                    todoist_client.complete_task(task_id=rem.todoist_id)
                result.todoist_completed.append(rem.title)

    # 4. Todoist completed -> complete in Apple
    for task in todoist_tasks:
        if task.get("is_completed"):
            task_id = str(task["id"])
            if task_id in apple_by_id:
                rem = apple_by_id[task_id]
                if not rem.completed:
                    if not dry_run:
                        complete_apple_reminder(list_name, rem.title)
                    result.apple_completed.append(rem.title)

    return result
