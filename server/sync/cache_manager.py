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
            # Run migrations to ensure schema is up to date
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

        with self._lock:
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
                            start_time = event.start_time.isoformat() if hasattr(
                                event.start_time, 'isoformat'
                            ) else str(event.start_time)
                            end_time = event.end_time.isoformat() if hasattr(
                                event.end_time, 'isoformat'
                            ) else str(event.end_time)

                            event_data.append((
                                event.id,
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

                        # Batch insert all events
                        conn.executemany("""
                            INSERT OR REPLACE INTO events 
                            (id, account_id, calendar_id, title, description, start_time, end_time,
                             all_day, location, color, attendees, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, event_data)

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
        """
        Retrieve events from cache with optional filtering

        Args:
            start_date: Filter events starting after this date
            end_date: Filter events ending before this date
            account_ids: Filter by specific account IDs
            calendar_ids: Filter by specific calendar IDs

        Returns:
            List of calendar events
        """
        with self._lock:
            try:
                with self._get_connection() as conn:
                    # Build query
                    query = "SELECT * FROM events WHERE 1=1"
                    params = []

                    # Date range filtering
                    if start_date:
                        query += " AND end_time >= ?"
                        start_iso = start_date.isoformat() if hasattr(
                            start_date, 'isoformat'
                        ) else str(start_date)
                        params.append(start_iso)

                    if end_date:
                        query += " AND start_time <= ?"
                        end_iso = end_date.isoformat() if hasattr(
                            end_date, 'isoformat'
                        ) else str(end_date)
                        params.append(end_iso)

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

                    cursor = conn.execute(query, params)
                    rows = cursor.fetchall()

                    # Convert to CalendarEvent objects
                    events = []
                    for row in rows:
                        try:
                            # Parse attendees from JSON
                            attendees = json.loads(row['attendees']) if row['attendees'] else []

                            # Parse datetime strings with error handling
                            try:
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

                            event = CalendarEvent(
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

                            events.append(event)

                        except Exception as e:
                            logger.warning(f"Error parsing event {row.get('id', 'unknown')}: {e}")
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

    def close(self):
        """Close all database connections"""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
            logger.debug("Closed database connection")