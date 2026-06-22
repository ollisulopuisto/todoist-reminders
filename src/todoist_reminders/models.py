"""Data models for todoist-reminders."""

from dataclasses import dataclass, field


@dataclass
class AppleReminder:
    """A reminder from Apple Reminders."""

    title: str
    completed: bool
    todoist_id: str | None = None  # stored in notes/body field


@dataclass
class SyncResult:
    """Result of a sync operation."""

    todoist_to_apple: list[str] = field(default_factory=list)
    apple_to_todoist: list[str] = field(default_factory=list)
    todoist_completed: list[str] = field(default_factory=list)
    apple_completed: list[str] = field(default_factory=list)
