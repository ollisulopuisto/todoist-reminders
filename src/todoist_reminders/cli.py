"""CLI entrypoint for Todoist <-> Apple Reminders sync."""

import os
import sys
from argparse import ArgumentParser
from itertools import chain

from todoist_api_python.api import TodoistAPI
from todoist_api_python.models import Task

from todoist_reminders import SyncResult, sync
from todoist_reminders.apple_reminders import fetch_apple_reminders


def _build_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="Bidirectional sync between Todoist and Apple Reminders"
    )
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
    return parser


def _tasks_to_dicts(tasks: list[Task]) -> list[dict[str, object]]:
    return [
        {
            "id": t.id,
            "content": t.content,
            "is_completed": t.is_completed,
        }
        for t in tasks
    ]


def main(
    args: list[str] | None = None,
    dry_run: bool | None = None,
) -> SyncResult:
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
    # get_tasks() returns Iterator[list[Task]]; flatten to list[Task]
    raw_batches: list[list[Task]] = list(api.get_tasks())
    tasks: list[Task] = list(chain.from_iterable(raw_batches))

    task_dicts = _tasks_to_dicts(tasks)
    apple_reminders = fetch_apple_reminders(list_name)

    if is_dry_run:
        print("DRY RUN - no changes will be made.")

    result = sync(
        todoist_tasks=task_dicts,
        apple_reminders=apple_reminders,
        list_name=list_name,
        todoist_client=api,
        dry_run=is_dry_run,
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

    return result


if __name__ == "__main__":
    main()
