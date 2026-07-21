"""CLI entrypoint for Todoist <-> Apple Reminders sync."""

import os
import sys
from argparse import ArgumentParser
from datetime import date, datetime
from itertools import chain

from todoist_api_python.api import TodoistAPI
from todoist_api_python.models import Task

from todoist_reminders import sync
from todoist_reminders.apple_reminders import fetch_apple_reminders


def _build_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Bidirectional sync between Todoist and Apple Reminders")
    parser.add_argument(
        "--list",
        default="Todoist",
        help="Apple Reminders list name (default: Todoist)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be synced without making changes",
    )
    parser.add_argument(
        "--filter",
        choices=[
            "all",
            "none",
            "inbox",
            "due",
            "upcoming-due",
            "inbox-or-due",
            "inbox-or-upcoming-due",
            "inbox-and-upcoming-due",
        ],
        default="all",
        help="Filter which Todoist tasks are pushed to Apple Reminders (default: all)",
    )
    parser.add_argument(
        "--no-complete-on-import",
        action="store_true",
        help="Do not mark Apple Reminders as completed after importing them to Todoist",
    )
    return parser


def _tasks_to_dicts(
    tasks: list[Task],
    filter_mode: str,
    inbox_project_id: str | None,
) -> list[dict[str, object]]:
    from typing import cast

    today = date.today()
    dicts = []

    for t in tasks:
        is_inbox = inbox_project_id is not None and t.project_id == inbox_project_id
        has_any_due = t.due is not None

        has_upcoming_due = False
        if t.due:
            due_val = t.due.date
            # The parser returns datetime.date or datetime.datetime
            resolved_date = (
                due_val.date() if isinstance(due_val, datetime) else cast("date", due_val)
            )
            if resolved_date >= today:
                has_upcoming_due = True

        should_push = True
        if filter_mode == "none":
            should_push = False
        elif filter_mode == "inbox":
            should_push = is_inbox
        elif filter_mode == "due":
            should_push = has_any_due
        elif filter_mode == "upcoming-due":
            should_push = has_upcoming_due
        elif filter_mode == "inbox-or-due":
            should_push = is_inbox or has_any_due
        elif filter_mode == "inbox-or-upcoming-due":
            should_push = is_inbox or has_upcoming_due
        elif filter_mode == "inbox-and-upcoming-due":
            should_push = is_inbox and has_upcoming_due

        due_date_str = None
        if t.due is not None:
            due_date_str = t.due.date.isoformat()

        dicts.append(
            {
                "id": t.id,
                "content": t.content,
                "is_completed": t.is_completed,
                "should_push": should_push,
                "due_date": due_date_str,
            }
        )
    return dicts


def main(
    args: list[str] | None = None,
    dry_run: bool | None = None,
) -> None:
    parser = _build_parser()
    parsed = parser.parse_args(args)

    token = os.environ.get("TODOIST_TOKEN")
    if not token:
        print(
            "Error: TODOIST_TOKEN environment variable not set.",
            file=sys.stderr,
        )
        sys.exit(1)

    list_name: str = parsed.list
    is_dry_run = dry_run if dry_run is not None else parsed.dry_run

    api = TodoistAPI(token)
    filter_mode: str = parsed.filter

    inbox_project_id = None
    if filter_mode not in ("all", "due", "upcoming-due"):
        try:
            raw_project_batches = list(api.get_projects())
            projects = list(chain.from_iterable(raw_project_batches))
            for p in projects:
                if getattr(p, "is_inbox_project", False):
                    inbox_project_id = p.id
                    break
        except Exception as e:
            print(
                f"Warning: Could not fetch projects to identify Inbox: {e}",
                file=sys.stderr,
            )

    # get_tasks() returns Iterator[list[Task]]; flatten to list[Task]
    raw_batches: list[list[Task]] = list(api.get_tasks())
    tasks: list[Task] = list(chain.from_iterable(raw_batches))

    task_dicts = _tasks_to_dicts(tasks, filter_mode, inbox_project_id)
    apple_reminders = fetch_apple_reminders(list_name)

    if is_dry_run:
        print("DRY RUN - no changes will be made.")

    result = sync(
        todoist_tasks=task_dicts,
        apple_reminders=apple_reminders,
        list_name=list_name,
        todoist_client=api,
        dry_run=is_dry_run,
        complete_on_import=not parsed.no_complete_on_import,
    )

    for title in result.todoist_to_apple:
        print(f"  Todoist -> Apple: {title}")
    for title in result.apple_to_todoist:
        print(f"  Apple -> Todoist: {title}")
    for title in result.todoist_completed:
        print(f"  Completed in Todoist: {title}")
    for title in result.apple_completed:
        print(f"  Completed in Apple: {title}")

    total = (
        len(result.todoist_to_apple)
        + len(result.apple_to_todoist)
        + len(result.todoist_completed)
        + len(result.apple_completed)
    )
    if total == 0:
        print("Everything is already in sync.")
    else:
        label = "Would sync" if is_dry_run else "Synced"
        print(f"{label} {total} item(s).")

    return


if __name__ == "__main__":
    main()
