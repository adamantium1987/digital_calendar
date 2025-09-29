# server/sync/migrations.py
"""
Database migration system for schema versioning
Allows incremental schema updates without data loss
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Callable

logger = logging.getLogger(__name__)


class Migration:
    """Represents a single database migration"""

    def __init__(self, version: int, description: str, up: Callable, down: Callable = None):
        """
        Initialize migration

        Args:
            version: Target schema version
            description: Human-readable description
            up: Function to apply migration
            down: Function to rollback (optional)
        """
        self.version = version
        self.description = description
        self.up = up
        self.down = down


class MigrationManager:
    """Manages database schema migrations"""

    def __init__(self, db_path: str):
        """
        Initialize migration manager

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.migrations: List[Migration] = []
        self._register_migrations()

    def _register_migrations(self):
        """Register all available migrations"""
        # Migration 1: Initial schema
        self.migrations.append(Migration(
            version=1,
            description="Initial schema with events, calendars, sync_status",
            up=self._migration_1_up
        ))

        # Future migrations go here
        # self.migrations.append(Migration(
        #     version=2,
        #     description="Add indexes for performance",
        #     up=self._migration_2_up
        # ))

    def get_current_version(self) -> int:
        """
        Get current schema version from database

        Returns:
            Current version number (0 if no schema_version table)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
                )
                if not cursor.fetchone():
                    return 0

                cursor = conn.execute("SELECT MAX(version) FROM schema_version")
                result = cursor.fetchone()
                return result[0] if result and result[0] else 0
        except sqlite3.Error as e:
            logger.error(f"Error getting schema version: {e}", exc_info=True)
            return 0

    def migrate(self, target_version: int = None) -> bool:
        """
        Apply migrations to reach target version

        Args:
            target_version: Desired version (None = latest)

        Returns:
            True if successful
        """
        current_version = self.get_current_version()

        if target_version is None:
            target_version = max(m.version for m in self.migrations)

        if current_version == target_version:
            logger.info(f"Database already at version {current_version}")
            return True

        if current_version > target_version:
            logger.error(f"Cannot downgrade from {current_version} to {target_version}")
            return False

        logger.info(f"Migrating database from version {current_version} to {target_version}")

        # Apply migrations in order
        for migration in sorted(self.migrations, key=lambda m: m.version):
            if migration.version <= current_version:
                continue
            if migration.version > target_version:
                break

            try:
                logger.info(f"Applying migration {migration.version}: {migration.description}")
                migration.up()
                self._record_migration(migration.version, migration.description)
                logger.info(f"✓ Migration {migration.version} complete")
            except Exception as e:
                logger.error(f"Migration {migration.version} failed: {e}", exc_info=True)
                return False

        logger.info(f"✓ Database migrated to version {target_version}")
        return True

    def _record_migration(self, version: int, description: str):
        """Record completed migration in schema_version table"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO schema_version (version, description, applied_at)
                VALUES (?, ?, datetime('now'))
            """, (version, description))
            conn.commit()

    def _migration_1_up(self):
        """Initial schema creation"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Schema version table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    description TEXT NOT NULL,
                    applied_at TEXT NOT NULL
                )
            """)

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
                    attendees TEXT,
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

            # Indexes
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_account_calendar 
                ON events(account_id, calendar_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_time_range 
                ON events(start_time, end_time)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_all_day 
                ON events(all_day)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_account_time 
                ON events(account_id, start_time)
            """)

            conn.commit()