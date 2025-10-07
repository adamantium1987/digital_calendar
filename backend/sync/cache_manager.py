# server/sync/cache_manager.py
"""
Local cache management using SQLite
Stores calendar events and metadata for offline access and fast retrieval
Includes batch operations, connection pooling, and automatic cleanup
"""

import sqlite3
import json
import threading
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path
from contextlib import contextmanager

from ..calendar_sources.base import CalendarEvent
from ..task_chart.base import TaskItem
from ..config.settings import config
from ..config.constants import (
    CACHE_EXPIRY_DAYS,
    DB_CONNECTION_TIMEOUT,
    DB_MAX_RETRIES
)
from .migrations import MigrationManager

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages local SQLite cache for calendar data with improved performance"""

    def __init__(self, db_path: str = None):
        """
        Initialize cache manager

        Args:
            db_path: Path to SQLite database file
        """
        if db_path is None:
            cache_dir = Path(config.config_dir) / "cache"
            cache_dir.mkdir(exist_ok=True)
            db_path = cache_dir / "calendar_cache.db"

        self.db_path = str(db_path)
        self._lock = threading.Lock()
        self._local = threading.local()

        # Initialize database and run migrations
        self._init_database()

        logger.info(f"Cache manager initialized with database: {self.db_path}")

    @contextmanager
    def _get_connection(self):
        """
        Get thread-local database connection (connection pooling per thread)

        Yields:
            sqlite3.Connection
        """
        # Get or create connection for this thread
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                self.db_path,
                timeout=DB_CONNECTION_TIMEOUT,
                check_same_thread=False
            )
            self._local.connection.execute("PRAGMA foreign_keys = ON")
            self._local.connection.row_factory = sqlite3.Row
            logger.debug(f"Created new database connection for thread {threading.current_thread().name}")

        try:
            yield self._local.connection
        except Exception as e:
            self._local.connection.rollback()
            logger.error(f"Database error, rolled back transaction: {e}")
            raise
        finally:
            # Don't close connection - keep it for thread reuse
            pass

    def _init_database(self):
        """Initialize SQLite database with migrations"""
        try:
            # Run migrations to ensure schema is up-to-date
            migration_manager = MigrationManager(self.db_path)
            if migration_manager.migrate():
                logger.info("Database schema up to date")
            else:
                logger.error("Database migration failed")

        except Exception as e:
            logger.error(f"Error initializing database: {e}", exc_info=True)
            raise

    def store_events(self, account_id: str, calendar_id: str, events: List[CalendarEvent]):
        """
        Store calendar events in cache using batch operations

        Args:
            account_id: Account identifier
            calendar_id: Calendar identifier
            events: List of calendar events to store
        """
        if not events:
            logger.debug(f"No events to store for {account_id}/{calendar_id}")
            return

        with (self._lock):
            retry_count = 0
            while retry_count < DB_MAX_RETRIES:
                try:
                    with self._get_connection() as conn:
                        now = datetime.now(timezone.utc).isoformat()

                        # Clear existing events for this calendar
                        conn.execute(
                            "DELETE FROM events WHERE account_id = ? AND calendar_id = ?",
                            (account_id, calendar_id)
                        )

                        # Prepare batch insert data
                        event_data = []
                        for event in events:
                            # Convert attendees to JSON
                            attendees_json = json.dumps(event.attendees or [])

                            # Ensure datetime objects are properly converted
                            if hasattr(event.start_time, 'astimezone'):
                                start_time = event.start_time.astimezone(timezone.utc).isoformat()
                            else:
                                start_time = str(event.start_time)

                            if hasattr(event.end_time, 'astimezone'):
                                end_time = event.end_time.astimezone(timezone.utc).isoformat()
                            else:
                                end_time = str(event.end_time)

                            # Create unique ID for each event instance (handles recurring events)
                            # Create unique ID for each event instance (handles recurring events)
                            import hashlib
                            unique_id = hashlib.md5(f"{event.id}_{start_time}".encode()).hexdigest()

                            # Add this debug line:
                            logger.info(
                                f"Generated unique_id for {event.title}: original='{event.id}' -> unique='{unique_id}'")

                            event_data.append((
                                unique_id,  # Use unique ID instead of event.id
                                account_id,
                                calendar_id,
                                event.title,
                                event.description or '',
                                start_time,
                                end_time,
                                event.all_day,
                                event.location or '',
                                event.color or '',
                                attendees_json,
                                now,
                                now
                            ))

                        # Debug logging for unique IDs
                        unique_ids = [item[0] for item in event_data]
                        duplicate_ids = [id for id in set(unique_ids) if unique_ids.count(id) > 1]

                        logger.info(f"Generated {len(unique_ids)} unique IDs")
                        if duplicate_ids:
                            logger.error(f"DUPLICATE IDs FOUND: {duplicate_ids}")
                            for dup_id in duplicate_ids:
                                matching_events = [item for item in event_data if item[0] == dup_id]
                                logger.error(f"Duplicate ID {dup_id} has {len(matching_events)} events:")
                                for event_item in matching_events:
                                    logger.error(f"  - {event_item[3]} at {event_item[5]}")  # title and start_time
                        else:
                            logger.info("No duplicate IDs found - all unique")

                        # Batch insert all events
                        conn.executemany("""
                            INSERT OR REPLACE INTO events 
                            (id, account_id, calendar_id, title, description, start_time, end_time,
                             all_day, location, color, attendees, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, event_data)

                        logger.info(f"Batch insert completed. Prepared {len(event_data)} events for insertion")

                        # Check how many were actually inserted
                        cursor = conn.execute("SELECT COUNT(*) FROM events WHERE account_id = ? AND calendar_id = ?",
                                              (account_id, calendar_id))
                        actual_count = cursor.fetchone()[0]
                        logger.info(f"Actual events in database after insert: {actual_count}")

                        # Update sync status
                        conn.execute("""
                            INSERT OR REPLACE INTO sync_status 
                            (account_id, calendar_id, last_sync, event_count, last_error)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            account_id,
                            calendar_id,
                            now,
                            len(events),
                            None
                        ))

                        conn.commit()
                        logger.info(f"Stored {len(events)} events for {account_id}/{calendar_id}")
                        return

                except sqlite3.OperationalError as e:
                    retry_count += 1
                    if retry_count >= DB_MAX_RETRIES:
                        logger.error(f"Failed to store events after {DB_MAX_RETRIES} retries: {e}")
                        raise
                    logger.warning(f"Database locked, retry {retry_count}/{DB_MAX_RETRIES}")
                    import time
                    time.sleep(0.1 * retry_count)

                except Exception as e:
                    logger.error(f"Error storing events: {e}", exc_info=True)
                    raise

    def store_calendars(self, account_id: str, calendars: List[Dict[str, Any]]):
        """
        Store calendar metadata in cache using batch operations

        Args:
            account_id: Account identifier
            calendars: List of calendar info dicts
        """
        if not calendars:
            logger.debug(f"No calendars to store for {account_id}")
            return

        with self._lock:
            try:
                with self._get_connection() as conn:
                    now = datetime.now(timezone.utc).isoformat()

                    # Clear existing calendars for this account
                    conn.execute("DELETE FROM calendars WHERE account_id = ?", (account_id,))

                    # Prepare batch insert data
                    calendar_data = [
                        (
                            cal['id'],
                            account_id,
                            cal['name'],
                            cal.get('description', ''),
                            cal.get('color', '#4285f4'),
                            cal.get('primary', False),
                            cal.get('access_role', 'reader'),
                            now,
                            now
                        )
                        for cal in calendars
                    ]

                    # Batch insert all calendars
                    conn.executemany("""
                        INSERT INTO calendars
                        (id, account_id, name, description, color, primary_calendar, 
                         access_role, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, calendar_data)

                    conn.commit()
                    logger.info(f"Stored {len(calendars)} calendars for {account_id}")

            except Exception as e:
                logger.error(f"Error storing calendars: {e}", exc_info=True)
                raise

    def get_events(self, start_date: datetime = None, end_date: datetime = None,
                   account_ids: List[str] = None, calendar_ids: List[str] = None) -> List[CalendarEvent]:
        """Retrieve events from cache with optional filtering"""

        logger.info(f"Cache manager get_events called with start_date: {start_date}, end_date: {end_date}")

        with self._lock:
            try:
                with self._get_connection() as conn:
                    # Build query
                    query = "SELECT * FROM events WHERE 1=1"
                    params = []

                    # Date range filtering
                    if start_date:
                        query += " AND end_time >= ?"
                        start_iso = start_date.isoformat()
                        params.append(start_iso)
                        logger.info(f"Added start_date filter: end_time >= {start_iso}")

                    if end_date:
                        query += " AND start_time <= ?"
                        end_iso = end_date.isoformat()
                        params.append(end_iso)
                        logger.info(f"Added end_date filter: start_time <= {end_iso}")

                    # Account filtering
                    if account_ids:
                        placeholders = ','.join('?' * len(account_ids))
                        query += f" AND account_id IN ({placeholders})"
                        params.extend(account_ids)

                    # Calendar filtering
                    if calendar_ids:
                        placeholders = ','.join('?' * len(calendar_ids))
                        query += f" AND calendar_id IN ({placeholders})"
                        params.extend(calendar_ids)

                    # Order by start time
                    query += " ORDER BY start_time ASC"

                    logger.info(f"Final SQL query: {query}")

                    cursor = conn.execute(query, params)
                    rows = cursor.fetchall()

                    logger.info(f"SQL query returned {len(rows)} rows")

                    # Convert to CalendarEvent objects
                    events = []
                    for row in rows:
                        try:
                            # Parse attendees from JSON
                            attendees = json.loads(row['attendees']) if row['attendees'] else []

                            # Parse datetime strings with error handling
                            try:
                                # The values from database are already ISO strings, just parse them back to datetime
                                start_time = datetime.fromisoformat(
                                    row['start_time'].replace('Z', '+00:00')
                                )
                                end_time = datetime.fromisoformat(
                                    row['end_time'].replace('Z', '+00:00')
                                )
                            except (ValueError, AttributeError):
                                # Fallback for malformed datetime strings
                                logger.warning(f"Malformed datetime in event {row['id']}, skipping")
                                continue

                            cal_event = CalendarEvent(
                                id=row['id'],
                                title=row['title'],
                                description=row['description'],
                                start_time=start_time,
                                end_time=end_time,
                                all_day=bool(row['all_day']),
                                location=row['location'],
                                calendar_id=row['calendar_id'],
                                account_id=row['account_id'],
                                color=row['color'],
                                attendees=attendees
                            )

                            events.append(cal_event)

                        except Exception as e:
                            logger.warning(f"Error parsing event {row['id'] if 'id' in row.keys() else 'unknown'}: {e}")
                            continue

                    logger.debug(f"Retrieved {len(events)} events from cache")
                    return events

            except Exception as e:
                logger.error(f"Error getting events: {e}", exc_info=True)
                return []

    def get_calendars(self, account_id: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieve calendar metadata from cache

        Args:
            account_id: Specific account ID (None = all accounts)

        Returns:
            Dict mapping account_id to list of calendars
        """
        with self._lock:
            try:
                with self._get_connection() as conn:
                    if account_id:
                        cursor = conn.execute(
                            "SELECT * FROM calendars WHERE account_id = ? ORDER BY name",
                            (account_id,)
                        )
                    else:
                        cursor = conn.execute("SELECT * FROM calendars ORDER BY account_id, name")

                    rows = cursor.fetchall()

                    # Group by account_id
                    result = {}
                    for row in rows:
                        acc_id = row['account_id']
                        if acc_id not in result:
                            result[acc_id] = []

                        calendar_info = {
                            'id': row['id'],
                            'name': row['name'],
                            'description': row['description'],
                            'color': row['color'],
                            'primary': bool(row['primary_calendar']),
                            'access_role': row['access_role']
                        }

                        result[acc_id].append(calendar_info)

                    logger.debug(f"Retrieved calendars for {len(result)} accounts")
                    return result

            except Exception as e:
                logger.error(f"Error getting calendars: {e}", exc_info=True)
                return {}

    def cleanup_old_events(self, days: int = None):
        """
        Remove events older than specified days

        Args:
            days: Number of days to keep (default: CACHE_EXPIRY_DAYS)
        """
        if days is None:
            days = CACHE_EXPIRY_DAYS

        with self._lock:
            try:
                with self._get_connection() as conn:
                    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
                    cutoff_iso = cutoff_date.isoformat()

                    cursor = conn.execute(
                        "DELETE FROM events WHERE end_time < ?",
                        (cutoff_iso,)
                    )
                    deleted_count = cursor.rowcount
                    conn.commit()

                    if deleted_count > 0:
                        logger.info(f"Cleaned up {deleted_count} old events (older than {days} days)")
                    else:
                        logger.debug(f"No old events to clean up")

            except Exception as e:
                logger.error(f"Error cleaning up old events: {e}", exc_info=True)

    def clear_account_data(self, account_id: str):
        """
        Remove all data for a specific account

        Args:
            account_id: Account identifier
        """
        with self._lock:
            try:
                with self._get_connection() as conn:
                    conn.execute("DELETE FROM events WHERE account_id = ?", (account_id,))
                    conn.execute("DELETE FROM calendars WHERE account_id = ?", (account_id,))
                    conn.execute("DELETE FROM sync_status WHERE account_id = ?", (account_id,))
                    conn.commit()

                    logger.info(f"Cleared all data for account: {account_id}")

            except Exception as e:
                logger.error(f"Error clearing account data: {e}", exc_info=True)
                raise

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dict with cache statistics
        """
        with self._lock:
            try:
                with self._get_connection() as conn:
                    # Total events
                    cursor = conn.execute("SELECT COUNT(*) FROM events")
                    total_events = cursor.fetchone()[0]

                    # Total calendars
                    cursor = conn.execute("SELECT COUNT(*) FROM calendars")
                    total_calendars = cursor.fetchone()[0]

                    # Events by account
                    cursor = conn.execute("""
                        SELECT account_id, COUNT(*) as count 
                        FROM events 
                        GROUP BY account_id
                    """)
                    events_by_account = {row['account_id']: row['count'] for row in cursor.fetchall()}

                    # Date range
                    cursor = conn.execute("""
                        SELECT MIN(start_time) as earliest, MAX(end_time) as latest 
                        FROM events
                    """)
                    row = cursor.fetchone()
                    date_range = {
                        'earliest': row['earliest'],
                        'latest': row['latest']
                    }

                    return {
                        'total_events': total_events,
                        'total_calendars': total_calendars,
                        'events_by_account': events_by_account,
                        'date_range': date_range
                    }

            except Exception as e:
                logger.error(f"Error getting cache stats: {e}", exc_info=True)
                return {
                    'total_events': 0,
                    'total_calendars': 0,
                    'events_by_account': {},
                    'date_range': {'earliest': None, 'latest': None}
                }

    # Add after get_cache_stats method

    def store_tasks(self, tasks):
        """
        Store tasks in cache - creates one row per task per day

        Args:
            tasks: List of TaskItem objects
        """
        if not tasks:
            return

        with self._lock:
            try:
                with self._get_connection() as conn:
                    now = datetime.now(timezone.utc).isoformat()
                    week_start = tasks[0].week_start

                    # Clear existing tasks for this week
                    conn.execute(
                        "DELETE FROM tasks WHERE week_start = ?",
                        (week_start,)
                    )

                    # Get next task_id
                    cursor = conn.execute("SELECT COALESCE(MAX(task_id), 0) + 1 FROM tasks")
                    next_task_id = cursor.fetchone()[0]

                    # Prepare batch insert data - one row per task per day
                    task_data = []
                    current_task_id = next_task_id

                    for task in tasks:
                        for day in task.days:
                            task_data.append((
                                current_task_id,
                                task.name,
                                task.task,
                                task.type,
                                day,  # Individual day
                                task.week_start,
                                task.completed,
                                now,
                                now
                            ))
                        current_task_id += 1
                    # Batch insert all task-day combinations
                    conn.executemany("""
                        INSERT INTO tasks 
                        (task_id, name, task, type, day_name, week_start, completed, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, task_data)

                    conn.commit()
                    logger.info(f"Stored {len(task_data)} task-day records for week {week_start}")

            except Exception as e:
                logger.error(f"Error storing tasks: {e}", exc_info=True)
                raise

    def get_tasks(self, day_name: str = None, name: str = None, week_start: str = None):
        """
        Get tasks with optional filtering

        Args:
            day_name: Filter by day
            name: Filter by name
            week_start: Filter by week

        Returns:
            List of taskItem objects (grouped by task_id with days array)
        """
        with self._lock:
            try:
                with self._get_connection() as conn:
                    query = "SELECT * FROM tasks WHERE 1=1"
                    params = []

                    if week_start:
                        query += " AND week_start = ?"
                        params.append(week_start)

                    if name:
                        query += " AND name = ?"
                        params.append(name)

                    if day_name:
                        query += " AND day_name = ?"
                        params.append(day_name)

                    query += " ORDER BY task_id, day_name"

                    cursor = conn.execute(query, params)
                    rows = cursor.fetchall()

                    # Group by task_id to rebuild TaskItem objects
                    from ..task_chart.base import TaskItem
                    task_groups = {}

                    for row in rows:
                        try:
                            task_id = row['task_id']

                            if task_id not in task_groups:
                                task_groups[task_id] = {
                                    'id': str(task_id),  # Convert to string for TaskItem
                                    'name': row['name'],
                                    'task': row['task'],
                                    'type': row['type'],
                                    'week_start': row['week_start'],
                                    'days': [],
                                    'completed_days': []
                                }

                            task_groups[task_id]['days'].append(row['day_name'])
                            if row['completed']:
                                task_groups[task_id]['completed_days'].append(row['day_name'])

                        except Exception as e:
                            logger.warning(f"Error parsing task row {row['id'] if 'id' in row else 'unknown'}: {e}")
                            continue

                    # Convert to TaskItem objects
                    tasks = []
                    for task_data in task_groups.values():
                        # Overall completed if ALL days are completed
                        all_completed = len(task_data['completed_days']) == len(task_data['days'])

                        task = TaskItem(
                            id=task_data['id'],
                            name=task_data['name'],
                            task=task_data['task'],
                            type=task_data['type'],
                            days=task_data['days'],
                            completed=all_completed,
                            week_start=task_data['week_start']
                        )
                        tasks.append(task)

                    return tasks

            except Exception as e:
                logger.error(f"Error getting tasks: {e}", exc_info=True)
                return []

    def get_task_days(self, day_name: str = None, name: str = None, week_start: str = None):
        """
        Get individual task-day records (not grouped)

        Returns:
            List of dicts with task_id, name, task, day_name, completed
        """
        with self._lock:
            try:
                with self._get_connection() as conn:
                    query = "SELECT * FROM tasks WHERE 1=1"
                    params = []

                    if week_start:
                        query += " AND week_start = ?"
                        params.append(week_start)

                    if name:
                        query += " AND child_name = ?"
                        params.append(name)

                    if day_name:
                        query += " AND day_name = ?"
                        params.append(day_name)

                    query += " ORDER BY name, task, day_name"

                    cursor = conn.execute(query, params)
                    rows = cursor.fetchall()

                    results = []
                    for row in rows:
                        results.append({
                            'task_id': row['task_id'],
                            'name': row['name'],
                            'task': row['task'],
                            'type': row['type'],
                            'day_name': row['day_name'],
                            'completed': bool(row['completed']),
                            'week_start': row['week_start']
                        })

                    return results

            except Exception in e:
                logger.error(f"Error getting task days: {e}", exc_info=True)
                return []

    def update_task_completion(self, task_id: str, day_name: str, completed: bool, week_start: str) -> bool:
        """
        Update task completion status for a specific day

        Args:
            task_id: Task identifier
            day_name: Specific day to update
            completed: Completion status
            week_start: Week identifier

        Returns:
            True if successful
        """
        with self._lock:
            try:
                with self._get_connection() as conn:
                    now = datetime.now(timezone.utc).isoformat()

                    cursor = conn.execute("""
                        UPDATE tasks 
                        SET completed = ?, updated_at = ?
                        WHERE task_id = ? AND day_name = ? AND week_start = ?
                    """, (completed, now, task_id, day_name, week_start))

                    success = cursor.rowcount > 0
                    conn.commit()

                    if success:
                        logger.debug(f"Updated task {task_id} for {day_name} completion: {completed}")
                    else:
                        logger.warning(f"No task found to update: {task_id} on {day_name}")

                    return success

            except Exception as e:
                logger.error(f"Error updating task completion: {e}", exc_info=True)
                return False

    def close(self):
        """Close all database connections"""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
            logger.debug("Closed database connection")
