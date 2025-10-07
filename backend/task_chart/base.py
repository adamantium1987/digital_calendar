from dataclasses import dataclass
from typing import List


@dataclass
class TaskItem:
    """
    Standard task representation
    """
    id: str
    name: str
    task: str
    type: str
    days: List[str]  # ['sunday', 'monday', etc.]
    completed: bool = False
    week_start: str = None  # ISO format date for week tracking

    def __post_init__(self):
        """Initialize default values after instantiation"""
        if self.week_start is None:
            # Set to start of current week (Monday)
            from datetime import datetime, timezone, timedelta
            now = datetime.now(timezone.utc)
            week_start = now - timedelta(days=now.weekday())
            self.week_start = week_start.date().isoformat()
