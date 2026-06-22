"""Shared fixtures for todoist-reminders tests."""

import subprocess
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockFixture

from todoist_reminders.models import AppleReminder

# ---------------------------------------------------------------------------
# Fixture: mock subprocess.run at the apple_reminders module boundary
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_subprocess(mocker: MockFixture) -> MagicMock:
    """Mock subprocess.run inside apple_reminders module.

    Returns the mock so tests can configure return_value / side_effect.
    """
    mock = mocker.patch("todoist_reminders.apple_reminders.subprocess.run")
    mock.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    return mock


@pytest.fixture
def mock_osascript(mock_subprocess: MagicMock) -> MagicMock:
    """Pre-configured mock that returns successful osascript output."""
    return mock_subprocess


# ---------------------------------------------------------------------------
# Fixture: mock TodoistAPI client
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_todoist() -> MagicMock:
    """Mock TodoistAPI client with chainable methods."""
    client = MagicMock()
    client.add_task.return_value = MagicMock(id="new-task-id")
    client.complete_task.return_value = True
    client.get_tasks.return_value = iter([])  # empty iterator by default
    return client


# ---------------------------------------------------------------------------
# Fixture: mock all AppleScript calls inside sync module
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_sync_apple(mocker: MockFixture) -> dict[str, MagicMock]:
    """Mock every AppleScript boundary that sync() calls into."""
    return {
        "add": mocker.patch("todoist_reminders.sync.add_apple_reminder"),
        "complete": mocker.patch("todoist_reminders.sync.complete_apple_reminder"),
        "update_notes": mocker.patch("todoist_reminders.sync.update_reminder_notes"),
    }


# ---------------------------------------------------------------------------
# Fixture factory: sync scenarios
# ---------------------------------------------------------------------------


@dataclass
class SyncScenario:
    """Pre-configured sync test scenario.

    Attributes:
        todoist: list of task dicts
        apple:    list of AppleReminder objects
        expected_t2a: titles expected in todoist_to_apple result
        expected_a2t: titles expected in apple_to_todoist result
        expected_tc:  titles expected in todoist_completed result
        expected_ac:  titles expected in apple_completed result
    """

    todoist: list[dict[str, object]]
    apple: list[AppleReminder]
    expected_t2a: list[str]
    expected_a2t: list[str]
    expected_tc: list[str]
    expected_ac: list[str]


@pytest.fixture
def scenario() -> SyncScenario:
    """Default empty scenario — override in tests."""
    return SyncScenario(
        todoist=[],
        apple=[],
        expected_t2a=[],
        expected_a2t=[],
        expected_tc=[],
        expected_ac=[],
    )


# ---------------------------------------------------------------------------
# Helper: build task dicts
# ---------------------------------------------------------------------------


def make_task(task_id: str, content: str, completed: bool = False) -> dict[str, object]:
    """Build a Todoist task dict for sync()."""
    return {"id": task_id, "content": content, "is_completed": completed}


def make_reminder(
    title: str,
    completed: bool = False,
    todoist_id: str | None = None,
) -> AppleReminder:
    """Build an AppleReminder for tests."""
    return AppleReminder(title=title, completed=completed, todoist_id=todoist_id)
