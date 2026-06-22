"""Tests for the bidirectional sync logic."""

from unittest.mock import MagicMock, patch

import pytest

from todoist_reminders.models import AppleReminder, SyncResult
from todoist_reminders.sync import sync


def _task(task_id: str, content: str, completed: bool = False) -> dict:
    return {"id": task_id, "content": content, "is_completed": completed}


@pytest.fixture
def mock_apple():
    """Mock all AppleScript calls in sync module."""
    with patch("todoist_reminders.sync.add_apple_reminder"), patch(
        "todoist_reminders.sync.complete_apple_reminder"
    ), patch("todoist_reminders.sync.update_reminder_notes"):
        yield


class TestSyncTodoistToApple:
    """Push tasks from Todoist that don't exist in Apple Reminders."""

    def test_new_todoist_task_creates_apple_reminder(self, mock_apple) -> None:
        tasks = [_task("t1", "Buy milk")]
        mock_client = MagicMock()
        result = sync(tasks, [], "Todoist", mock_client)
        assert result.todoist_to_apple == ["Buy milk"]

    def test_existing_task_skipped(self, mock_apple) -> None:
        tasks = [_task("t1", "Buy milk")]
        apple = [AppleReminder(title="Buy milk", completed=False, todoist_id="t1")]
        mock_client = MagicMock()
        result = sync(tasks, apple, "Todoist", mock_client)
        assert result.todoist_to_apple == []

    def test_completed_todoist_task_not_pushed(self, mock_apple) -> None:
        tasks = [_task("t1", "Done task", completed=True)]
        mock_client = MagicMock()
        result = sync(tasks, [], "Todoist", mock_client)
        assert result.todoist_to_apple == []


class TestSyncAppleToTodoist:
    """Push reminders from Apple that don't exist in Todoist."""

    def test_new_apple_reminder_creates_todoist_task(self, mock_apple) -> None:
        apple = [AppleReminder(title="Call mom", completed=False)]
        mock_task = MagicMock()
        mock_task.id = "new-t1"
        mock_client = MagicMock()
        mock_client.add_task.return_value = mock_task
        result = sync([], apple, "Todoist", mock_client)
        assert result.apple_to_todoist == ["Call mom"]
        mock_client.add_task.assert_called_once_with(content="Call mom")

    def test_reminder_with_todoist_id_skipped(self, mock_apple) -> None:
        apple = [AppleReminder(title="Call mom", completed=False, todoist_id="t1")]
        tasks = [_task("t1", "Call mom")]
        mock_client = MagicMock()
        result = sync(tasks, apple, "Todoist", mock_client)
        assert result.apple_to_todoist == []

    def test_completed_apple_reminder_not_pushed(self, mock_apple) -> None:
        apple = [AppleReminder(title="Done", completed=True)]
        mock_client = MagicMock()
        result = sync([], apple, "Todoist", mock_client)
        assert result.apple_to_todoist == []


class TestSyncCompletion:
    """Bidirectional completion propagation."""

    def test_apple_completed_completes_todoist(self, mock_apple) -> None:
        tasks = [_task("t1", "Task")]
        apple = [AppleReminder(title="Task", completed=True, todoist_id="t1")]
        mock_client = MagicMock()
        result = sync(tasks, apple, "Todoist", mock_client)
        assert result.todoist_completed == ["Task"]
        mock_client.complete_task.assert_called_once_with(task_id="t1")

    def test_todoist_completed_completes_apple(self, mock_apple) -> None:
        tasks = [_task("t1", "Task", completed=True)]
        apple = [AppleReminder(title="Task", completed=False, todoist_id="t1")]
        mock_client = MagicMock()
        result = sync(tasks, apple, "Todoist", mock_client)
        assert result.apple_completed == ["Task"]

    def test_already_completed_skipped(self, mock_apple) -> None:
        tasks = [_task("t1", "Task", completed=True)]
        apple = [AppleReminder(title="Task", completed=True, todoist_id="t1")]
        mock_client = MagicMock()
        result = sync(tasks, apple, "Todoist", mock_client)
        assert result.apple_completed == []
        assert result.todoist_completed == []


class TestSyncDryRun:
    """Dry-run mode should not call mutating operations."""

    def test_no_writes_in_dry_run(self, mock_apple) -> None:
        tasks = [_task("t1", "Buy milk")]
        apple = [AppleReminder(title="Call mom", completed=False)]
        mock_client = MagicMock()
        result = sync(tasks, apple, "Todoist", mock_client, dry_run=True)
        assert result.todoist_to_apple == ["Buy milk"]
        assert result.apple_to_todoist == ["Call mom"]
        mock_client.add_task.assert_not_called()


class TestSyncEmpty:
    """Edge cases with empty inputs."""

    def test_both_empty(self, mock_apple) -> None:
        mock_client = MagicMock()
        result = sync([], [], "Todoist", mock_client)
        assert result == SyncResult()
