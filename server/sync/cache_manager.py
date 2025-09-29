# server/sync/cache_manager.py
"""
Local cache management using SQLite - FIXED VERSION
Stores calendar events and metadata for offline access and fast retrieval
"""

import sqlite3
import json
import threading
from datetime import datetime, timedelta, timezone  # FIXED: Added timedelta import
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..calendar_sources.base import CalendarEvent
from ..config.settings import config


class CacheManager:
    """Manages local SQLite cache for calendar data"""

    def __init__(self, db_path: str = None):
        """Initialize cache manager

        Args:
            db_path: Path to SQLite database file
        """
        if db_path is None:
            cache_dir = Path(config.config_dir) / "cache"
            cache_dir.mkdir(exist_ok=True)
            db_path = cache_dir / "calendar_cache.db"

        self.db_path = str(db_path)
        self._lock = threading.Lock()

        # Initialize database
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")

                # Events table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS events (
                        id TEXT PRIMARY KEY,
                        account_id TEXT NOT NULL,
                        calendar_id TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        start_time TEXT NOT NULL,
                        end_time TEXT NOT NULL,
                        all_day BOOLEAN NOT NULL,
                        location TEXT,
                        color TEXT,
                        attendees TEXT,  -- JSON array
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        UNIQUE(id, account_id, calendar_id)
                    )
                """)

                # Calendars table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS calendars (
                        id TEXT NOT NULL,
                        account_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        description TEXT,
                        color TEXT,
                        primary_calendar BOOLEAN,
                        access_role TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        PRIMARY KEY (id, account_id)
                    )
                """)

                # Sync status table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS sync_status (
                        account_id TEXT PRIMARY KEY,
                        calendar_id TEXT NOT NULL,
                        last_sync TEXT NOT NULL,
                        event_count INTEGER NOT NULL,
                        last_error TEXT
                    )
                """)

                # Create indexes for performance
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_events_account_calendar ON events(account_id, calendar_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_events_time_range ON events(start_time, end_time)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_events_all_day ON events(all_day)")

                conn.commit()

        except Exception as e:
            print(f"Error initializing database: {e}")
            raise

    def store_events(self, account_id: str, calendar_id: str, events: List[CalendarEvent]):
        """Store calendar events in cache

        Args:
            account_id: Account identifier
            calendar_id: Calendar identifier
            events: List of calendar events to store
        """
        if not events:
            return

        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    now = datetime.now(timezone.utc).isoformat()

                    # Clear existing events for this calendar
                    conn.execute(
                        "DELETE FROM events WHERE account_id = ? AND calendar_id = ?",
                        (account_id, calendar_id)
                    )

                    # Insert new events
                    for event in events:
                        # Convert attendees to JSON
                        attendees_json = json.dumps(event.attendees or [])

                        # FIXED: Ensure all datetime objects are properly converted
                        start_time = event.start_time.isoformat() if hasattr(event.start_time, 'isoformat') else str(
                            event.start_time)
                        end_time = event.end_time.isoformat() if hasattr(event.end_time, 'isoformat') else str(
                            event.end_time)

                        conn.execute("""
                            INSERT OR REPLACE INTO events 
                            (id, account_id, calendar_id, title, description, start_time, end_time,
                             all_day, location, color, attendees, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
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

            except Exception as e:
                print(f"Error storing events: {e}")
                raise

    def store_calendars(self, account_id: str, calendars: List[Dict[str, Any]]):
        """Store calendar metadata in cache

        Args:
            account_id: Account identifier
            calendars: List of calendar info dicts
        """
        if not calendars:
            return

        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    now = datetime.now(timezone.utc).isoformat()

                    # Clear existing calendars for this account
                    conn.execute("DELETE FROM calendars WHERE account_id = ?", (account_id,))

                    # Insert new calendars
                    for cal in calendars:
                        conn.execute("""
                            INSERT INTO calendars
                            (id, account_id, name, description, color, primary_calendar, 
                             access_role, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            cal['id'],
                            account_id,
                            cal['name'],
                            cal.get('description', ''),
                            cal.get('color', '#4285f4'),
                            cal.get('primary', False),
                            cal.get('access_role', 'reader'),
                            now,
                            now
                        ))

                    conn.commit()

            except Exception as e:
                print(f"Error storing calendars: {e}")
                raise

    def get_events(self, start_date: datetime = None, end_date: datetime = None,
                   account_ids: List[str] = None, calendar_ids: List[str] = None) -> List[CalendarEvent]:
        """Retrieve events from cache with optional filtering

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
                with sqlite3.connect(self.db_path) as conn:
                    # FIXED: Set row factory for easier dict access
                    conn.row_factory = sqlite3.Row

                    # Build query
                    query = "SELECT * FROM events WHERE 1=1"
                    params = []

                    # Date range filtering
                    if start_date:
                        query += " AND end_time >= ?"
                        start_iso = start_date.isoformat() if hasattr(start_date, 'isoformat') else str(start_date)
                        params.append(start_iso)

                    if end_date:
                        query += " AND start_time <= ?"
                        end_iso = end_date.isoformat() if hasattr(end_date, 'isoformat') else str(end_date)
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

                            # FIXED: Parse datetime strings with error handling
                            try:
                                start_time = datetime.fromisoformat(row['start_time'].replace('Z', '+00:00'))
                                end_time = datetime.fromisoformat(row['end_time'].replace('Z', '+00:00'))
                            except ValueError:
                                # Fallback for malformed datetime strings
                                start_time = datetime.now()
                                end_time = datetime.now() + timedelta(hours=1)

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
                            print(f"Error parsing event {row.get('id', 'unknown')}: {e}")
                            continue

                    return events

            except Exception as e:
                print(f"Error getting events: {e}")
                return []

    def get_calendars(self, account_id: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """Retrieve calendar metadata from cache

        Args:
            account_id: Specific account ID (None = all accounts)

        Returns:
            Dict mapping account_id to list of calendars
        """
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row

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

                    return result

            except Exception as e:
                print(f"Error getting calendars: {e}")
                return {}

    def get_sync_status(self, account_id: str = None) -> Dict[str, Any]:
        """Get sync status for accounts

        Args:
            account_id: Specific account (None = all accounts)

        Returns:
            Dict with sync status information
        """
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row

                    if account_id:
                        cursor = conn.execute(
                            "SELECT * FROM sync_status WHERE account_id = ?",
                            (account_id,)
                        )
                    else:
                        cursor = conn.execute("SELECT * FROM sync_status")

                    rows = cursor.fetchall()

                    result = {}
                    for row in rows:
                        acc_id = row['account_id']
                        if acc_id not in result:
                            result[acc_id] = []

                        status = {
                            'calendar_id': row['calendar_id'],
                            'last_sync': row['last_sync'],
                            'event_count': row['event_count'],
                            'last_error': row['last_error']
                        }

                        result[acc_id].append(status)

                    return result

            except Exception as e:
                print(f"Error getting sync status: {e}")
