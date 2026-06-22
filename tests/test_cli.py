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
