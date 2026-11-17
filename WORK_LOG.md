# PR 7 follow-up

List creation is inside the same AppleScript process as reminder creation,
conditional on the target list being missing. Direct add and library sync calls
therefore remain safe, and empty/dry CLI runs do not recreate a deleted list.
Ruff, mypy and all 61 tests pass under Python 3.13. No real Todoist/Reminders
accounts were accessed, and osascript was mocked on Linux.
