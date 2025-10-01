# server/sync/chore_manager.py
"""
Chore chart management
Reads CSV and manages chore data with weekly resets
"""

import csv
import logging
from datetime import datetime, timezone, timedelta
from typing import List
from pathlib import Path

from ..chore_chart.base import ChoreItem
from ..config.settings import config
from .cache_manager import CacheManager

logger = logging.getLogger(__name__)


class ChoreManager:
    """Manages chore chart data from CSV with weekly tracking"""

    def __init__(self, cache_manager: CacheManager):
        """
        Initialize chore manager

        Args:
            cache_manager: Cache manager instance for database operations
        """
        self.cache_manager = cache_manager
        self.csv_path = Path(config.config_dir) / "chore_chart.csv"
        logger.info(f"Chore manager initialized with CSV: {self.csv_path}")

    def load_chores_from_csv(self) -> List[ChoreItem]:
        """
        Load chores from CSV file

        Returns:
            List of ChoreItem objects
        """
        if not self.csv_path.exists():
            logger.warning(f"Chore chart CSV not found: {self.csv_path}")
            return []

        chores = []
        try:
            with open(self.csv_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                # Define day columns to check
                day_columns = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']

                for row_num, row in enumerate(reader, start=2):
                    try:
                        child_name = row['child_name'].strip()
                        task = row['task'].strip()

                        if not all([child_name, task]):
                            logger.warning(f"Empty child_name or task in CSV row {row_num}, skipping")
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
                        chore_id = f"{child_name}_{task}".replace(' ', '_').lower()

                        chore = ChoreItem(
                            id=chore_id,
                            child_name=child_name,
                            task=task,
                            days=days
                        )

                        chores.append(chore)

                    except KeyError as e:
                        logger.error(f"Missing column {e} in CSV row {row_num}")
                        continue
                    except Exception as e:
                        logger.error(f"Error parsing CSV row {row_num}: {e}")
                        continue

            logger.info(f"Loaded {len(chores)} chores from CSV")
            return chores

        except Exception as e:
            logger.error(f"Error reading chore CSV: {e}", exc_info=True)
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

    def sync_chores(self) -> bool:
        """
        Load chores from CSV and sync to database

        Returns:
            True if successful
        """
        try:
            chores = self.load_chores_from_csv()
            if not chores:
                logger.info("No chores to sync")
                return True

            # Set current week for all chores
            current_week = self.get_current_week_start()
            for chore in chores:
                chore.week_start = current_week

            # Store in database
            self.cache_manager.store_chores(chores)
            logger.info(f"Synced {len(chores)} chores for week {current_week}")
            return True

        except Exception as e:
            logger.error(f"Error syncing chores: {e}", exc_info=True)
            return False

    def get_chores_for_day(self, day_name: str, child_name: str = None) -> List[ChoreItem]:
        """
        Get chores for a specific day

        Args:
            day_name: Day name (e.g., 'monday')
            child_name: Optional child filter

        Returns:
            List of chores for that day
        """
        try:
            return self.cache_manager.get_chores(
                day_name=day_name.lower(),
                child_name=child_name,
                week_start=self.get_current_week_start()
            )
        except Exception as e:
            logger.error(f"Error getting chores for {day_name}: {e}", exc_info=True)
            return []

    def mark_chore_complete(self, chore_id: str, completed: bool = True) -> bool:
        """
        Mark a chore as complete/incomplete

        Args:
            chore_id: Chore identifier
            completed: Completion status

        Returns:
            True if successful
        """
        try:
            return self.cache_manager.update_chore_completion(
                chore_id=chore_id,
                completed=completed,
                week_start=self.get_current_week_start()
            )
        except Exception as e:
            logger.error(f"Error updating chore {chore_id}: {e}", exc_info=True)
            return False