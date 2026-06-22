"""Tests for Apple Reminders AppleScript helpers.

Covers:
- subprocess invocation & error propagation
- string escaping (injection prevention)
- fetch parsing (empty, single, multi, with/without IDs)
- add/complete/update call structure
"""

import subprocess
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockFixture

from todoist_reminders.apple_reminders import (
    add_apple_reminder,
    complete_apple_reminder,
    escape_applescript,
    fetch_apple_reminders,
    run_applescript,
    update_reminder_notes,
)

# ---------------------------------------------------------------------------
# run_applescript
# ---------------------------------------------------------------------------


class TestRunApplescript:
    def test_returns_stdout(self, mock_subprocess: MockFixture) -> None:
        mock_subprocess.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="hello\n", stderr=""
        )
        result = run_applescript('return "hello"')
        assert result == "hello\n"

    def test_propagates_failure(self, mock_subprocess: MockFixture) -> None:
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            1, "osascript", stderr="execution error: -1728"
        )
        with pytest.raises(subprocess.CalledProcessError):
            run_applescript("error")

    def test_passes_full_osascript_path(self, mock_subprocess: MockFixture) -> None:
        run_applescript("test")
        cmd = mock_subprocess.call_args[0][0]
        assert cmd[0] == "/usr/bin/osascript"
        assert cmd[1] == "-e"

    def test_check_true_is_set(self, mock_subprocess: MockFixture) -> None:
        run_applescript("test")
        assert mock_subprocess.call_args.kwargs["check"] is True


# ---------------------------------------------------------------------------
# escape_applescript — parametrized edge cases
# ---------------------------------------------------------------------------


class TestEscapeApplescript:
    @pytest.mark.parametrize(
        ("raw", "escaped"),
        [
            ('say "hi"', 'say \\"hi\\"'),
            ("path\\to", "path\\\\to"),
            ("it's", "it\\'s"),
            ("a\"b\\c'd", "a\\\"b\\\\c\\'d"),
            ("hello world", "hello world"),
            ("", ""),
            ('"', '\\"'),
            ("\\", "\\\\"),
            ("'", "\\'"),
            ('\\"', '\\\\\\"'),  # backslash + quote
        ],
        ids=[
            "double-quotes",
            "backslash",
            "single-quote",
            "all-special",
            "plain",
            "empty",
            "only-quote",
            "only-backslash",
            "only-apostrophe",
            "backslash-then-quote",
        ],
    )
    def test_escaping(self, raw: str, escaped: str) -> None:
        assert escape_applescript(raw) == escaped


# ---------------------------------------------------------------------------
# fetch_apple_reminders
# ---------------------------------------------------------------------------


class TestFetchAppleReminders:
    def test_empty_output(self, mock_osascript: MagicMock) -> None:
        mock_osascript.return_value.stdout = ""
        assert fetch_apple_reminders("AnyList") == []

    def test_whitespace_only_output(self, mock_osascript: MagicMock) -> None:
        mock_osascript.return_value.stdout = "   \n  "
        assert fetch_apple_reminders("AnyList") == []

    @pytest.mark.parametrize(
        ("stdout", "expected"),
        [
            pytest.param(
                "Buy milk\tfalse\t\n",
                [("Buy milk", False, None)],
                id="single-no-id",
            ),
            pytest.param(
                "Buy milk\tfalse\tabc123\n",
                [("Buy milk", False, "abc123")],
                id="single-with-id",
            ),
            pytest.param(
                "Done\ttrue\tid1\n",
                [("Done", True, "id1")],
                id="completed-with-id",
            ),
            pytest.param(
                "A\tfalse\t\nB\ttrue\tid1\nC\tfalse\tid2\n",
                [("A", False, None), ("B", True, "id1"), ("C", False, "id2")],
                id="multiple-mixed",
            ),
            pytest.param(
                "Task\tfalse\t\n",
                [("Task", False, None)],
                id="empty-notes-field",
            ),
        ],
    )
    def test_parsing(
        self,
        mock_osascript: MagicMock,
        stdout: str,
        expected: list[tuple[str, bool, str | None]],
    ) -> None:
        mock_osascript.return_value.stdout = stdout
        result = fetch_apple_reminders("TestList")
        assert len(result) == len(expected)
        for rem, (title, completed, tid) in zip(result, expected, strict=True):
            assert rem.title == title
            assert rem.completed is completed
            assert rem.todoist_id == tid

    def test_escapes_list_name_in_script(self, mock_osascript: MagicMock) -> None:
        fetch_apple_reminders('List"WithQuotes')
        script = mock_osascript.call_args[0][0][-1]
        assert '\\"' in script

    def test_malformed_line_skipped(self, mock_osascript: MagicMock) -> None:
        """Lines with fewer than 2 tab-separated fields are skipped."""
        mock_osascript.return_value.stdout = "only-one-field\nValid\tfalse\t\n"
        result = fetch_apple_reminders("TestList")
        assert len(result) == 1
        assert result[0].title == "Valid"


# ---------------------------------------------------------------------------
# add_apple_reminder
# ---------------------------------------------------------------------------


class TestAddAppleReminder:
    def test_creates_list_then_adds(self, mock_osascript: MagicMock) -> None:
        add_apple_reminder("MyList", "Task", "tid-1")
        assert mock_osascript.call_count == 2  # ensure_list + add

    def test_escapes_all_user_input(self, mock_osascript: MagicMock) -> None:
        add_apple_reminder('L"1', 'T"2', 'id"3')
        # Every call should have escaped quotes
        for c in mock_osascript.call_args_list:
            script = c[0][0][-1]
            # The raw unescaped " should not appear in the script
            # (it should be \\" instead)
            assert '"3"' not in script or '\\"' in script

    def test_add_call_contains_body_with_id(self, mock_osascript: MagicMock) -> None:
        add_apple_reminder("MyList", "Task", "my-id-42")
        add_script = mock_osascript.call_args_list[1][0][0][-1]
        assert "my-id-42" in add_script
        assert "body" in add_script


# ---------------------------------------------------------------------------
# complete_apple_reminder
# ---------------------------------------------------------------------------


class TestCompleteAppleReminder:
    def test_sets_completed_true(self, mock_osascript: MagicMock) -> None:
        complete_apple_reminder("MyList", "Done task")
        script = mock_osascript.call_args[0][0][-1]
        assert "set completed of target to true" in script

    def test_targets_incomplete_only(self, mock_osascript: MagicMock) -> None:
        complete_apple_reminder("MyList", "Task")
        script = mock_osascript.call_args[0][0][-1]
        assert "completed is false" in script

    def test_escapes_title(self, mock_osascript: MagicMock) -> None:
        complete_apple_reminder("MyList", 'Task "important"')
        script = mock_osascript.call_args[0][0][-1]
        assert '\\"' in script


# ---------------------------------------------------------------------------
# update_reminder_notes
# ---------------------------------------------------------------------------


class TestUpdateReminderNotes:
    def test_sets_body_to_todoist_id(self, mock_osascript: MagicMock) -> None:
        update_reminder_notes("MyList", "Task", "new-id-99")
        script = mock_osascript.call_args[0][0][-1]
        assert "set body of target to" in script
        assert "new-id-99" in script

    def test_escapes_all_inputs(self, mock_osascript: MagicMock) -> None:
        update_reminder_notes('L"1', 'T"2', 'id"3')
        script = mock_osascript.call_args[0][0][-1]
        # Should not contain raw unescaped user quotes
        assert '"3"' not in script.split("id")[-1] or '\\"' in script
