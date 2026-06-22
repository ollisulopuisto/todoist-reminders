"""Tests for the CLI entrypoint."""

import os
from unittest.mock import MagicMock, patch

import pytest

from todoist_reminders.cli import main


class TestCli:
    def test_exits_without_token(self) -> None:
        with patch.dict(os.environ, {}, clear=True), pytest.raises(SystemExit):
            main([])

    def test_dry_run_flag(self) -> None:
        with (
            patch.dict(os.environ, {"TODOIST_TOKEN": "test-token"}),
            patch("todoist_reminders.cli.TodoistAPI") as mock_api,
            patch("todoist_reminders.cli.fetch_apple_reminders", return_value=[]),
            patch("todoist_reminders.cli.sync") as mock_sync,
        ):
            mock_client = MagicMock()
            mock_client.get_tasks.return_value = []
            mock_api.return_value = mock_client
            mock_sync.return_value = MagicMock(
                todoist_to_apple=[],
                apple_to_todoist=[],
                todoist_completed=[],
                apple_completed=[],
            )
            main(["--dry-run"])
            mock_sync.assert_called_once()

    def test_tasks_to_dicts_filters(self) -> None:
        from datetime import date, timedelta

        from todoist_reminders.cli import _tasks_to_dicts

        # Task 1: in inbox, no due date
        t1 = MagicMock()
        t1.id = "t1"
        t1.content = "Inbox task"
        t1.project_id = "inbox-id"
        t1.is_completed = False
        t1.due = None

        # Task 2: in another project, due tomorrow
        t2 = MagicMock()
        t2.id = "t2"
        t2.content = "Due tomorrow task"
        t2.project_id = "other-id"
        t2.is_completed = False
        t2.due = MagicMock()
        t2.due.date = date.today() + timedelta(days=1)

        # Task 3: in another project, due yesterday
        t3 = MagicMock()
        t3.id = "t3"
        t3.content = "Overdue task"
        t3.project_id = "other-id"
        t3.is_completed = False
        t3.due = MagicMock()
        t3.due.date = date.today() - timedelta(days=1)

        # Task 4: in another project, no due date
        t4 = MagicMock()
        t4.id = "t4"
        t4.content = "No due task"
        t4.project_id = "other-id"
        t4.is_completed = False
        t4.due = None

        tasks = [t1, t2, t3, t4]

        # Test "all" filter
        res = _tasks_to_dicts(tasks, "all", "inbox-id")
        assert [r["should_push"] for r in res] == [True, True, True, True]

        # Test "inbox" filter
        res = _tasks_to_dicts(tasks, "inbox", "inbox-id")
        assert [r["should_push"] for r in res] == [True, False, False, False]

        # Test "due" filter
        res = _tasks_to_dicts(tasks, "due", "inbox-id")
        assert [r["should_push"] for r in res] == [False, True, True, False]

        # Test "upcoming-due" filter
        res = _tasks_to_dicts(tasks, "upcoming-due", "inbox-id")
        assert [r["should_push"] for r in res] == [False, True, False, False]

        # Test "inbox-or-due" filter
        res = _tasks_to_dicts(tasks, "inbox-or-due", "inbox-id")
        assert [r["should_push"] for r in res] == [True, True, True, False]

        # Test "inbox-or-upcoming-due" filter
        res = _tasks_to_dicts(tasks, "inbox-or-upcoming-due", "inbox-id")
        assert [r["should_push"] for r in res] == [True, True, False, False]

        # Test "inbox-and-upcoming-due" filter
        res = _tasks_to_dicts(tasks, "inbox-and-upcoming-due", "inbox-id")
        # Only t1 (inbox, no due) -> False, t2 (other, due tomorrow) -> False
        # Add a task in inbox due tomorrow
        t5 = MagicMock()
        t5.id = "t5"
        t5.content = "Inbox due tomorrow"
        t5.project_id = "inbox-id"
        t5.is_completed = False
        t5.due = MagicMock()
        t5.due.date = date.today() + timedelta(days=1)

        res = _tasks_to_dicts([*tasks, t5], "inbox-and-upcoming-due", "inbox-id")
        assert [r["should_push"] for r in res] == [False, False, False, False, True]
