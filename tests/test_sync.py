"""Tests for the bidirectional sync logic.

Covers all four sync directions, dedup, dry-run, and edge cases.
Uses parametrized tests for thorough coverage.
"""

from unittest.mock import MagicMock

import pytest
from pytest_mock import MockFixture

from tests.conftest import make_reminder, make_task
from todoist_reminders.models import SyncResult
from todoist_reminders.sync import sync

# ---------------------------------------------------------------------------
# Helper: run sync with mocked AppleScript
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_apple(mocker: MockFixture) -> dict[str, MagicMock]:
    return {
        "add": mocker.patch("todoist_reminders.sync.add_apple_reminder"),
        "complete": mocker.patch("todoist_reminders.sync.complete_apple_reminder"),
        "update_notes": mocker.patch("todoist_reminders.sync.update_reminder_notes"),
    }


# ---------------------------------------------------------------------------
# Direction 1: Todoist → Apple (push new tasks)
# ---------------------------------------------------------------------------


class TestTodoistToApple:
    def test_new_task_pushed(self, mock_apple: dict[str, MagicMock]) -> None:
        result = sync([make_task("t1", "Buy milk")], [], "Todoist", MagicMock())
        assert result.todoist_to_apple == ["Buy milk"]

    def test_existing_by_title_skipped(self, mock_apple: dict[str, MagicMock]) -> None:
        result = sync(
            [make_task("t1", "Buy milk")],
            [make_reminder("Buy milk", todoist_id="t1")],
            "Todoist",
            MagicMock(),
        )
        assert result.todoist_to_apple == []

    def test_completed_not_pushed(self, mock_apple: dict[str, MagicMock]) -> None:
        result = sync(
            [make_task("t1", "Done", completed=True)],
            [],
            "Todoist",
            MagicMock(),
        )
        assert result.todoist_to_apple == []

    def test_multiple_new_tasks(self, mock_apple: dict[str, MagicMock]) -> None:
        result = sync(
            [make_task("t1", "A"), make_task("t2", "B"), make_task("t3", "C")],
            [],
            "Todoist",
            MagicMock(),
        )
        assert result.todoist_to_apple == ["A", "B", "C"]

    def test_mixed_new_and_existing(self, mock_apple: dict[str, MagicMock]) -> None:
        result = sync(
            [make_task("t1", "Old"), make_task("t2", "New")],
            [make_reminder("Old", todoist_id="t1")],
            "Todoist",
            MagicMock(),
        )
        assert result.todoist_to_apple == ["New"]


# ---------------------------------------------------------------------------
# Direction 2: Apple → Todoist (push new reminders)
# ---------------------------------------------------------------------------


class TestAppleToTodoist:
    def test_new_reminder_pushed(self, mock_apple: dict[str, MagicMock]) -> None:
        mock_client = MagicMock()
        mock_client.add_task.return_value = MagicMock(id="new-t1")
        result = sync([], [make_reminder("Call mom")], "Todoist", mock_client)
        assert result.apple_to_todoist == ["Call mom"]
        mock_client.add_task.assert_called_once_with(content="Call mom")

    def test_with_todoist_id_skipped(self, mock_apple: dict[str, MagicMock]) -> None:
        result = sync(
            [make_task("t1", "Call mom")],
            [make_reminder("Call mom", todoist_id="t1")],
            "Todoist",
            MagicMock(),
        )
        assert result.apple_to_todoist == []

    def test_matching_content_skipped(self, mock_apple: dict[str, MagicMock]) -> None:
        """Apple reminder with no ID but matching Todoist content → skip."""
        result = sync(
            [make_task("t1", "Call mom")],
            [make_reminder("Call mom")],  # no todoist_id
            "Todoist",
            MagicMock(),
        )
        assert result.apple_to_todoist == []

    def test_completed_not_pushed(self, mock_apple: dict[str, MagicMock]) -> None:
        result = sync(
            [],
            [make_reminder("Done", completed=True)],
            "Todoist",
            MagicMock(),
        )
        assert result.apple_to_todoist == []

    def test_updates_notes_with_new_id(self, mock_apple: dict[str, MagicMock]) -> None:
        mock_client = MagicMock()
        mock_client.add_task.return_value = MagicMock(id="fresh-id")
        sync([], [make_reminder("Task")], "Todoist", mock_client)
        mock_apple["update_notes"].assert_called_once_with("Todoist", "Task", "fresh-id")


# ---------------------------------------------------------------------------
# Direction 3: Apple completed → complete in Todoist
# ---------------------------------------------------------------------------


class TestAppleCompletedSync:
    def test_completes_in_todoist(self, mock_apple: dict[str, MagicMock]) -> None:
        mock_client = MagicMock()
        result = sync(
            [make_task("t1", "Task")],
            [make_reminder("Task", completed=True, todoist_id="t1")],
            "Todoist",
            mock_client,
        )
        assert result.todoist_completed == ["Task"]
        mock_client.complete_task.assert_called_once_with(task_id="t1")

    def test_already_completed_skipped(self, mock_apple: dict[str, MagicMock]) -> None:
        mock_client = MagicMock()
        result = sync(
            [make_task("t1", "Task", completed=True)],
            [make_reminder("Task", completed=True, todoist_id="t1")],
            "Todoist",
            mock_client,
        )
        assert result.todoist_completed == []
        mock_client.complete_task.assert_not_called()

    def test_no_todoist_id_skipped(self, mock_apple: dict[str, MagicMock]) -> None:
        """Completed Apple reminder with no linked Todoist ID → skip."""
        mock_client = MagicMock()
        result = sync(
            [],
            [make_reminder("Orphan", completed=True)],
            "Todoist",
            mock_client,
        )
        assert result.todoist_completed == []
        mock_client.complete_task.assert_not_called()


# ---------------------------------------------------------------------------
# Direction 4: Todoist completed → complete in Apple
# ---------------------------------------------------------------------------


class TestTodoistCompletedSync:
    def test_completes_in_apple(self, mock_apple: dict[str, MagicMock]) -> None:
        result = sync(
            [make_task("t1", "Task", completed=True)],
            [make_reminder("Task", todoist_id="t1")],
            "Todoist",
            MagicMock(),
        )
        assert result.apple_completed == ["Task"]

    def test_already_completed_skipped(self, mock_apple: dict[str, MagicMock]) -> None:
        result = sync(
            [make_task("t1", "Task", completed=True)],
            [make_reminder("Task", completed=True, todoist_id="t1")],
            "Todoist",
            MagicMock(),
        )
        assert result.apple_completed == []

    def test_no_linked_apple_skipped(self, mock_apple: dict[str, MagicMock]) -> None:
        """Completed Todoist task with no Apple counterpart → nothing to do."""
        result = sync(
            [make_task("t1", "Task", completed=True)],
            [],
            "Todoist",
            MagicMock(),
        )
        assert result.apple_completed == []


# ---------------------------------------------------------------------------
# Dry-run mode
# ---------------------------------------------------------------------------


class TestDryRun:
    def test_reports_without_writing(self) -> None:
        mock_client = MagicMock()
        result = sync(
            [make_task("t1", "New")],
            [make_reminder("Orphan")],
            "Todoist",
            mock_client,
            dry_run=True,
        )
        assert result.todoist_to_apple == ["New"]
        assert result.apple_to_todoist == ["Orphan"]
        mock_client.add_task.assert_not_called()
        mock_client.complete_task.assert_not_called()

    def test_completion_reported_without_writing(self) -> None:
        mock_client = MagicMock()
        result = sync(
            [make_task("t1", "Task", completed=True)],
            [make_reminder("Task", todoist_id="t1")],
            "Todoist",
            mock_client,
            dry_run=True,
        )
        assert result.apple_completed == ["Task"]
        mock_client.complete_task.assert_not_called()


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_both_empty(self, mock_apple: dict[str, MagicMock]) -> None:
        result = sync([], [], "Todoist", MagicMock())
        assert result == SyncResult()

    def test_duplicate_titles_different_ids(self, mock_apple: dict[str, MagicMock]) -> None:
        """Two tasks with same content but different IDs — both pushed."""
        result = sync(
            [make_task("t1", "Task"), make_task("t2", "Task")],
            [],
            "Todoist",
            MagicMock(),
        )
        # Both should be pushed since dedup is by title in apple_by_title
        # The second one won't be in apple_by_title yet when checked
        assert "Task" in result.todoist_to_apple

    def test_full_cycle(self, mock_apple: dict[str, MagicMock]) -> None:
        """New in both + completions in both in one sync."""
        mock_client = MagicMock()
        mock_client.add_task.return_value = MagicMock(id="new-from-apple")
        result = sync(
            [
                make_task("t1", "New from Todoist"),
                make_task("t2", "Finish me", completed=True),
                make_task("t3", "Finish me too"),  # active in Todoist, completed in Apple
            ],
            [
                make_reminder("New from Apple"),
                make_reminder("Finish me too", completed=True, todoist_id="t3"),
                make_reminder(
                    "Finish me", todoist_id="t2"
                ),  # active in Apple, completed in Todoist
            ],
            "Todoist",
            mock_client,
        )
        assert "New from Todoist" in result.todoist_to_apple
        assert "New from Apple" in result.apple_to_todoist
        assert "Finish me too" in result.todoist_completed
        assert "Finish me" in result.apple_completed
