"""Tests for Apple Reminders AppleScript helpers."""

import subprocess
from unittest.mock import patch

import pytest

from todoist_reminders.apple_reminders import (
    add_apple_reminder,
    complete_apple_reminder,
    escape_applescript,
    fetch_apple_reminders,
    run_applescript,
)


class TestRunApplescript:
    def test_returns_stdout(self) -> None:
        with patch("todoist_reminders.apple_reminders.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="hello\n", stderr=""
            )
            result = run_applescript('return "hello"')
            assert result == "hello\n"

    def test_raises_on_failure(self) -> None:
        with patch("todoist_reminders.apple_reminders.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                1, "osascript", stderr="boom"
            )
            with pytest.raises(subprocess.CalledProcessError):
                run_applescript("error")


class TestEscapeApplescript:
    def test_escapes_double_quotes(self) -> None:
        assert escape_applescript('say "hi"') == 'say \\"hi\\"'

    def test_escapes_backslashes(self) -> None:
        assert escape_applescript("path\\to") == "path\\\\to"

    def test_escapes_single_quotes(self) -> None:
        assert escape_applescript("it's") == "it\\'s"

    def test_plain_string_unchanged(self) -> None:
        assert escape_applescript("hello world") == "hello world"


class TestFetchAppleReminders:
    def test_empty_list(self) -> None:
        with patch(
            "todoist_reminders.apple_reminders.run_applescript", return_value=""
        ):
            result = fetch_apple_reminders("TestList")
            assert result == []

    def test_single_reminder(self) -> None:
        with patch(
            "todoist_reminders.apple_reminders.run_applescript",
            return_value="Buy milk\tfalse\t\n",
        ):
            result = fetch_apple_reminders("TestList")
            assert len(result) == 1
            assert result[0].title == "Buy milk"
            assert result[0].completed is False
            assert result[0].todoist_id is None

    def test_reminder_with_todoist_id(self) -> None:
        with patch(
            "todoist_reminders.apple_reminders.run_applescript",
            return_value="Buy milk\tfalse\tabc123\n",
        ):
            result = fetch_apple_reminders("TestList")
            assert result[0].todoist_id == "abc123"

    def test_completed_reminder(self) -> None:
        with patch(
            "todoist_reminders.apple_reminders.run_applescript",
            return_value="Done task\ttrue\tabc456\n",
        ):
            result = fetch_apple_reminders("TestList")
            assert result[0].completed is True

    def test_multiple_reminders(self) -> None:
        output = "Task A\tfalse\t\nTask B\ttrue\tid1\nTask C\tfalse\tid2\n"
        with patch(
            "todoist_reminders.apple_reminders.run_applescript", return_value=output
        ):
            result = fetch_apple_reminders("TestList")
            assert len(result) == 3
            assert result[0].title == "Task A"
            assert result[1].title == "Task B"
            assert result[2].title == "Task C"


class TestAddAppleReminder:
    def test_calls_applescript(self) -> None:
        with patch(
            "todoist_reminders.apple_reminders.run_applescript"
        ) as mock_run:
            add_apple_reminder("MyList", "New task", "todoist-123")
            assert mock_run.call_count == 2  # ensure_list + add

    def test_escapes_special_chars(self) -> None:
        with patch(
            "todoist_reminders.apple_reminders.run_applescript"
        ) as mock_run:
            add_apple_reminder("MyList", 'Task with "quotes"', "id1")
            # The add call (second call) should contain escaped quotes
            second_call_args = mock_run.call_args_list[1][0][0]
            assert '\\"' in second_call_args


class TestCompleteAppleReminder:
    def test_marks_completed(self) -> None:
        with patch(
            "todoist_reminders.apple_reminders.run_applescript"
        ) as mock_run:
            complete_apple_reminder("MyList", "Done task")
            mock_run.assert_called_once()
            script = mock_run.call_args[0][0]
            assert "set completed" in script
