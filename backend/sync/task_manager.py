# server/sync/task_manager.py
"""
Task chart management
Reads CSV and manages task data with weekly resets
"""

import csv
import logging
from datetime import datetime, timezone, timedelta
from typing import List
from pathlib import Path

from ..task_chart.base import TaskItem
from ..config.settings import config
from .cache_manager import CacheManager

logger = logging.getLogger(__name__)


class TaskManager:
    """Manages task chart data from CSV with weekly tracking"""

    def __init__(self, cache_manager: CacheManager):
        """
        Initialize task manager

        Args:
            cache_manager: Cache manager instance for database operations
        """
        self.cache_manager = cache_manager
        self.csv_path = Path(config.config_dir) / "task_chart.csv"
        logger.info(f"Task manager initialized with CSV: {self.csv_path}")

    def load_tasks_from_csv(self) -> List[TaskItem]:
        """
        Load tasks from CSV file

        Returns:
            List of TaskItem objects
        """
        if not self.csv_path.exists():
            logger.warning(f"Task chart CSV not found: {self.csv_path}")
            return []

        tasks = []
        try:
            with open(self.csv_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                # Define day columns to check
                day_columns = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']

                for row_num, row in enumerate(reader, start=2):
                    try:
                        name = row['name'].strip()
                        task_name = row['task'].strip()
                        task_type = row['type'].strip()

                        if not all([name, task_name]):
                            logger.warning(f"Empty name or task in CSV row {row_num}, skipping")
                            continue

                        # Parse individual day columns (Y means enabled)
                        days = []
                        for day in day_columns:
                            try:
                                day_value = row[day].strip().upper()
                                if day_value == 'Y':
                                    days.append(day)
                            except KeyError:
                                logger.warning(f"Missing column '{day}' in CSV row {row_num}")
                                continue

                        if not days:
                            logger.warning(f"No days marked 'Y' in CSV row {row_num}, skipping")
                            continue

                        # Create unique ID
                        task_id = f"{name}_{task_name}".replace(' ', '_').lower()

                        task = TaskItem(
                            id=task_id,
                            name=name,
                            task=task_name,
                            type=task_type,
                            days=days
                        )

                        tasks.append(task)

                    except KeyError as e:
                        logger.error(f"Missing column {e} in CSV row {row_num}")
                        continue
                    except Exception as e:
                        logger.error(f"Error parsing CSV row {row_num}: {e}")
                        continue
            logger.info(f"Loaded {len(tasks)} tasks from CSV")
            return tasks

        except Exception as e:
            logger.error(f"Error reading task CSV: {e}", exc_info=True)
            return []

    def get_current_week_start(self) -> str:
        """
        Get current week start date (Sunday) in ISO format

        Returns:
            ISO format date string
        """
        now = datetime.now(timezone.utc)
        # Calculate days since Sunday (0=Sunday, 1=Monday, etc.)
        days_since_sunday = (now.weekday() + 1) % 7
        week_start = now - timedelta(days=days_since_sunday)
        return week_start.date().isoformat()

    def sync_tasks(self) -> bool:
        """
        Load tasks from CSV and sync to database

        Returns:
            True if successful
        """
        try:
            tasks = self.load_tasks_from_csv()
            if not tasks:
                logger.info("No tasks to sync")
                return True

            # Set current week for all tasks
            current_week = self.get_current_week_start()
            for task in tasks:
                task.week_start = current_week

            # Store in database
            self.cache_manager.store_tasks(tasks)
            logger.info(f"Synced {len(tasks)} tasks for week {current_week}")
            return True

        except Exception as e:
            logger.error(f"Error syncing tasks: {e}", exc_info=True)
            return False

    def get_tasks_for_day(self, day_name: str, name: str = None) -> List[TaskItem]:
        """
        Get tasks for a specific day

        Args:
            day_name: Day name (e.g., 'monday')
            name: Optional name filter

        Returns:
            List of tasks for that day
        """
        try:
            return self.cache_manager.get_tasks(
                day_name=day_name.lower(),
                name=name,
                week_start=self.get_current_week_start()
            )
        except Exception as e:
            logger.error(f"Error getting tasks for {day_name}: {e}", exc_info=True)
            return []

    def mark_task_complete(self, task_id: str, completed: bool = True) -> bool:
        """
        Mark a task as complete/incomplete

        Args:
            task_id: Task identifier
            completed: Completion status

        Returns:
            True if successful
        """
        try:
            return self.cache_manager.update_task_completion(
                task_id=task_id,
                completed=completed,
                week_start=self.get_current_week_start()
            )
        except Exception as e:
            logger.error(f"Error updating task {task_id}: {e}", exc_info=True)
            return False
