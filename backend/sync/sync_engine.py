# server/sync/sync_engine.py
"""
Main calendar synchronization engine
Coordinates all calendar sources and manages data updates
All operations are synchronous for simplicity and reliability
"""

import threading
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .chore_manager import ChoreManager
from ..calendar_sources.google_cal import GoogleCalendarSource
from ..calendar_sources.apple_cal import AppleCalendarSource
from ..calendar_sources.base import CalendarEvent, BaseCalendarSource
from ..config.settings import config
from ..config.constants import (
    DEFAULT_SYNC_INTERVAL_MINUTES,
    STARTUP_DELAY_SECONDS,
    SYNC_DATE_RANGE_PAST_DAYS,
    SYNC_DATE_RANGE_FUTURE_DAYS,
    CACHE_CLEANUP_INTERVAL_HOURS
)
from .cache_manager import CacheManager

logger = logging.getLogger(__name__)


class SyncEngine:
    """Main synchronization engine for all calendar sources"""

    def __init__(self) -> None:
        """Initialize sync engine with proper components"""
        self.cache_manager: CacheManager = CacheManager()
        self.chore_manager: ChoreManager = ChoreManager(self.cache_manager)
        # self.calendar_manager: CalendarManager = CalendarManager(self.cache_manager)
        self.scheduler: BackgroundScheduler = BackgroundScheduler()
        self.sources: Dict[str, BaseCalendarSource] = {}
        self.is_running: bool = False
        self.last_sync: Dict[str, datetime] = {}  # Track last sync time per account

        # Sync status tracking
        self.sync_status: Dict[str, Any] = {
            'last_full_sync': None,
            'currently_syncing': False,
            'errors': [],
            'total_events': 0,
            'total_calendars': 0
        }

        # Thread safety
        self._lock: threading.Lock = threading.Lock()

        logger.info("Sync engine initialized")

    def start(self) -> None:
        """Start the sync engine and scheduler"""
        if self.is_running:
            logger.warning("Sync engine already running")
            return

        logger.info("Starting Calendar Sync Engine...")

        # Initialize calendar sources
        self._initialize_sources()

        # Force database migration check for chores
        try:
            from .migrations import MigrationManager
            migration_manager = MigrationManager(self.cache_manager.db_path)
            migration_manager.migrate()
            logger.info("Database migrations completed")
        except Exception as e:
            logger.error(f"Migration error: {e}", exc_info=True)

        # Start background scheduler for sync
        sync_interval = config.get('sync.interval_minutes', DEFAULT_SYNC_INTERVAL_MINUTES)
        self.scheduler.add_job(
            func=self._scheduled_sync,
            trigger=IntervalTrigger(minutes=sync_interval),
            id='calendar_sync',
            name='Calendar Synchronization',
            replace_existing=True
        )

        # Add cache cleanup job
        self.scheduler.add_job(
            func=self._scheduled_cleanup,
            trigger=IntervalTrigger(hours=CACHE_CLEANUP_INTERVAL_HOURS),
            id='cache_cleanup',
            name='Cache Cleanup',
            replace_existing=True
        )

        # Add chore sync job
        self.scheduler.add_job(
            func=self._scheduled_chore_sync,
            trigger='cron',
            day_of_week='sun',
            hour=0,
            minute=0,
            id='chore_sync',
            name='Weekly Chore Sync',
            replace_existing=True
        )

        self.scheduler.start()
        self.is_running = True

        logger.info(f"✓ Sync engine started (sync interval: {sync_interval} minutes)")

        # Do initial sync in background thread
        sync_thread = threading.Thread(target=self._initial_sync, daemon=True)
        sync_thread.start()

    def stop(self) -> None:
        """Stop the sync engine and clean up resources"""
        if not self.is_running:
            logger.warning("Sync engine not running")
            return

        logger.info("Stopping Calendar Sync Engine...")

        # Shutdown scheduler
        try:
            self.scheduler.shutdown(wait=True)
        except Exception as e:
            logger.error(f"Error shutting down scheduler: {e}", exc_info=True)

        # Close all calendar sources
        for account_id, source in self.sources.items():
            try:
                source.close()
                logger.debug(f"Closed source: {account_id}")
            except Exception as e:
                logger.error(f"Error closing source {account_id}: {e}", exc_info=True)

        # Close cache manager
        try:
            self.cache_manager.close()
        except Exception as e:
            logger.error(f"Error closing cache manager: {e}", exc_info=True)

        self.is_running = False
        logger.info("✓ Sync engine stopped")

    def _initialize_sources(self) -> None:
        """Initialize all configured calendar sources"""
        try:
            accounts = config.list_accounts()

            # Initialize Google accounts
            for account in accounts['google']:
                if account.get('enabled', True):
                    account_id = account['id']
                    try:
                        source = GoogleCalendarSource(account_id, account)

                        # Load OAuth credentials if available
                        stored_creds = config.get_credentials(account_id)
                        if stored_creds and 'client_id' in stored_creds:
                            source.set_oauth_credentials(
                                stored_creds['client_id'],
                                stored_creds['client_secret']
                            )

                            # Load the OAuth token if it exists
                            if 'google_token' in stored_creds:
                                source.set_token(stored_creds['google_token'])

                        self.sources[account_id] = source
                        logger.debug(f"Initialized Google source: {account.get('display_name')}")

                    except Exception as e:
                        logger.error(f"Error initializing Google account {account_id}: {e}", exc_info=True)

            # Initialize Apple accounts
            for account in accounts['apple']:
                if account.get('enabled', True):
                    account_id = account['id']
                    try:
                        source = AppleCalendarSource(account_id, account)

                        # Authenticate if credentials are available
                        stored_creds = config.get_credentials(account_id)
                        if stored_creds and 'app_password' in stored_creds:
                            if source.authenticate():
                                self.sources[account_id] = source
                                logger.debug(f"Initialized Apple source: {account.get('display_name')}")
                            else:
                                logger.warning(f"Failed to authenticate Apple account: {account.get('display_name')}")
                        else:
                            # Add source but it will need authentication later
                            self.sources[account_id] = source
                            logger.debug(f"Added unauthenticated Apple source: {account.get('display_name')}")

                    except Exception as e:
                        logger.error(f"Error initializing Apple account {account_id}: {e}", exc_info=True)

            logger.info(f"✓ Initialized {len(self.sources)} calendar sources")

        except Exception as e:
            logger.error(f"Error initializing sources: {e}", exc_info=True)
            with self._lock:
                self.sync_status['errors'].append({
                    'time': datetime.now().isoformat(),
                    'error': str(e),
                    'type': 'initialization'
                })

    def _initial_sync(self) -> None:
        """Perform initial sync in background"""
        try:
            import time
            time.sleep(STARTUP_DELAY_SECONDS)  # Give server time to fully start
            logger.info("Starting initial sync...")
            self.sync_all()

            # Also sync chores on startup
            logger.info("Starting initial chore sync...")
            self.chore_manager.sync_chores()

        except Exception as e:
            logger.error(f"Initial sync error: {e}", exc_info=True)

    def _scheduled_sync(self) -> None:
        """Scheduled sync job (runs in scheduler thread)"""
        try:
            logger.debug("Running scheduled sync")
            self.sync_all()
        except Exception as e:
            logger.error(f"Scheduled sync error: {e}", exc_info=True)
            with self._lock:
                self.sync_status['errors'].append({
                    'time': datetime.now().isoformat(),
                    'error': str(e),
                    'type': 'scheduled_sync'
                })

    def _scheduled_cleanup(self) -> None:
        """Scheduled cache cleanup job"""
        try:
            logger.debug("Running scheduled cache cleanup")
            self.cache_manager.cleanup_old_events()
        except Exception as e:
            logger.error(f"Scheduled cleanup error: {e}", exc_info=True)

    def _scheduled_chore_sync(self) -> None:
        """Scheduled chore sync job"""
        try:
            logger.debug("Running scheduled chore sync")
            self.chore_manager.sync_chores()
        except Exception as e:
            logger.error(f"Scheduled chore sync error: {e}", exc_info=True)

    def sync_all(self) -> bool:
        """
        Sync all configured calendar sources

        Returns:
            True if sync completed successfully, False otherwise
        """
        with self._lock:
            if self.sync_status['currently_syncing']:
                logger.info("Sync already in progress, skipping...")
                return False

            self.sync_status['currently_syncing'] = True
            self.sync_status['errors'] = []

        start_time = datetime.now()
        logger.info(f"Starting full calendar sync at {start_time.strftime('%H:%M:%S')}")

        total_events = 0
        total_calendars = 0

        try:
            # Sync each source
            for account_id, source in self.sources.items():
                try:
                    events, calendars = self._sync_source(source)
                    total_events += events
                    total_calendars += calendars
                    self.last_sync[account_id] = datetime.now()

                except Exception as e:
                    error_msg = f"Error syncing {account_id}: {e}"
                    logger.error(error_msg, exc_info=True)
                    with self._lock:
                        self.sync_status['errors'].append({
                            'time': datetime.now().isoformat(),
                            'error': str(e),
                            'account_id': account_id,
                            'type': 'source_sync'
                        })

            # Update sync status
            with self._lock:
                self.sync_status.update({
                    'last_full_sync': datetime.now().isoformat(),
                    'total_events': total_events,
                    'total_calendars': total_calendars
                })

            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"✓ Sync completed in {duration:.1f}s: {total_events} events from {total_calendars} calendars")

            return True

        except Exception as e:
            logger.error(f"Full sync error: {e}", exc_info=True)
            with self._lock:
                self.sync_status['errors'].append({
                    'time': datetime.now().isoformat(),
                    'error': str(e),
                    'type': 'full_sync'
                })
            return False

        finally:
            with self._lock:
                self.sync_status['currently_syncing'] = False

    def _sync_source(self, source: BaseCalendarSource) -> Tuple[int, int]:
        """
        Sync a single calendar source

        Args:
            source: Calendar source to sync

        Returns:
            Tuple of (events_count, calendars_count)
        """
        account_id = source.account_id
        display_name = source.config.get('display_name', account_id)

        logger.info(f"Syncing {display_name}...")

        try:
            # Authenticate if needed
            if not source.is_authenticated:
                logger.warning(f"Authentication required for {display_name}")
                return 0, 0

            # Get calendars
            calendars = source.get_calendars()
            if not calendars:
                logger.warning(f"No calendars found for {display_name}")
                return 0, 0

            # Store calendar list
            self.cache_manager.store_calendars(account_id, calendars)
            logger.debug(f"Stored {len(calendars)} calendars for {display_name}")

            # Define sync date range
            start_date = datetime.now(timezone.utc) - timedelta(days=SYNC_DATE_RANGE_PAST_DAYS)
            end_date = datetime.now(timezone.utc) + timedelta(days=SYNC_DATE_RANGE_FUTURE_DAYS)

            total_events = 0

            # Get specific calendar IDs if configured
            account_config = next(
                (acc for acc_list in config.list_accounts().values()
                 for acc in acc_list if acc['id'] == account_id),
                {}
            )

            specific_calendars = account_config.get('calendar_ids', [])

            # Sync events from each calendar
            for calendar in calendars:
                calendar_id = calendar['id']
                calendar_name = calendar['name']

                # Skip if specific calendars configured and this isn't one of them
                if specific_calendars and calendar_id not in specific_calendars:
                    continue

                try:
                    logger.debug(f"Syncing calendar: {calendar_name}")
                    events = source.get_events(calendar_id, start_date, end_date)

                    if events:
                        # Store events in cache
                        self.cache_manager.store_events(account_id, calendar_id, events)
                        total_events += len(events)
                        logger.debug(f"✓ {len(events)} events from {calendar_name}")
                    else:
                        logger.debug(f"• No events in {calendar_name}")

                except Exception as e:
                    logger.error(f"Error syncing calendar {calendar_name}: {e}", exc_info=True)

            logger.info(f"✓ {display_name}: {total_events} events from {len(calendars)} calendars")
            return total_events, len(calendars)

        except Exception as e:
            logger.error(f"Error syncing source {display_name}: {e}", exc_info=True)
            return 0, 0

    def sync_account(self, account_id: str) -> bool:
        """
        Sync a specific account

        Args:
            account_id: Account to sync

        Returns:
            True if sync successful, False otherwise
        """
        if account_id not in self.sources:
            logger.warning(f"Account not found: {account_id}")
            return False

        try:
            with self._lock:
                if self.sync_status['currently_syncing']:
                    logger.info("Sync already in progress")
                    return False
                self.sync_status['currently_syncing'] = True

            try:
                events, calendars = self._sync_source(self.sources[account_id])
                self.last_sync[account_id] = datetime.now()
                logger.info(f"✓ Account {account_id} synced: {events} events from {calendars} calendars")
                return True
            finally:
                with self._lock:
                    self.sync_status['currently_syncing'] = False

        except Exception as e:
            logger.error(f"Error syncing account {account_id}: {e}", exc_info=True)
            return False

    def get_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        account_ids: Optional[List[str]] = None,
        calendar_ids: Optional[List[str]] = None
    ) -> List[CalendarEvent]:
        """
        Get cached events with optional filtering

        Args:
            start_date: Filter events starting after this date
            end_date: Filter events ending before this date
            account_ids: Filter by specific account IDs
            calendar_ids: Filter by specific calendar IDs

        Returns:
            List of calendar events
        """
        try:
            return self.cache_manager.get_events(
                start_date=start_date,
                end_date=end_date,
                account_ids=account_ids,
                calendar_ids=calendar_ids
            )
        except Exception as e:
            logger.error(f"Error getting events: {e}", exc_info=True)
            return []

    def get_calendars(self, account_id: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get cached calendar information

        Args:
            account_id: Specific account ID (None = all accounts)

        Returns:
            Dict mapping account_id to list of calendars
        """
        try:
            return self.cache_manager.get_calendars(account_id)
        except Exception as e:
            logger.error(f"Error getting calendars: {e}", exc_info=True)
            return {}

    def get_sync_status(self) -> Dict[str, Any]:
        """
        Get current sync status and statistics

        Returns:
            Dict with sync status information
        """
        with self._lock:
            status = self.sync_status.copy()

        # Add per-account last sync times
        status['account_sync_times'] = {}
        for account_id, last_sync in self.last_sync.items():
            status['account_sync_times'][account_id] = last_sync.isoformat()

        # Add source status
        status['sources'] = {}
        for account_id, source in self.sources.items():
            status['sources'][account_id] = {
                'type': source.get_source_type(),
                'authenticated': source.is_authenticated,
                'display_name': source.config.get('display_name', account_id)
            }

        return status

    def force_sync(self) -> bool:
        """
        Force immediate sync of all sources

        Returns:
            True if sync started successfully, False if already in progress
        """
        with self._lock:
            if self.sync_status['currently_syncing']:
                logger.info("Sync already in progress, cannot force sync")
                return False

        # Run sync in background thread
        sync_thread = threading.Thread(target=self.sync_all, daemon=True)
        sync_thread.start()
        logger.info("Forced sync started")
        return True

    def add_account(self, account_type: str, account_config: Dict[str, Any]) -> str:
        """
        Add a new account and initialize its source

        Args:
            account_type: 'google' or 'apple'
            account_config: Account configuration dict

        Returns:
            Account ID

        Raises:
            ValueError: If account type is unsupported
        """
        account_id = account_config['id']

        try:
            # Create appropriate source
            if account_type == 'google':
                source = GoogleCalendarSource(account_id, account_config)
            elif account_type == 'apple':
                source = AppleCalendarSource(account_id, account_config)
            else:
                raise ValueError(f"Unsupported account type: {account_type}")

            self.sources[account_id] = source
            logger.info(f"✓ Added {account_type} account: {account_config.get('display_name', account_id)}")

            return account_id

        except Exception as e:
            logger.error(f"Error adding account: {e}", exc_info=True)
            raise

    def remove_account(self, account_id: str) -> None:
        """
        Remove an account and clean up its data

        Args:
            account_id: Account to remove
        """
        try:
            # Close and remove source
            if account_id in self.sources:
                self.sources[account_id].close()
                del self.sources[account_id]

            # Remove from last sync tracking
            if account_id in self.last_sync:
                del self.last_sync[account_id]

            # Clean up cached data
            self.cache_manager.clear_account_data(account_id)

            logger.info(f"✓ Removed account: {account_id}")

        except Exception as e:
            logger.error(f"Error removing account {account_id}: {e}", exc_info=True)


# Global sync engine instance
sync_engine: SyncEngine = SyncEngine()