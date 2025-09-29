# server/sync/sync_engine.py
"""
Main calendar synchronization engine - FIXED VERSION
Coordinates all calendar sources and manages data updates
"""

import threading
import time
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from ..calendar_sources.google_cal import GoogleCalendarSource
from ..calendar_sources.apple_cal import AppleCalendarSource
from ..calendar_sources.base import CalendarEvent, BaseCalendarSource
from ..config.settings import config
from .cache_manager import CacheManager


class SyncEngine:
    """Main synchronization engine for all calendar sources"""

    def __init__(self):
        """Initialize sync engine with proper components"""
        # Fixed: Initialize cache manager properly
        self.cache_manager = CacheManager()
        self.scheduler = BackgroundScheduler()
        self.sources: Dict[str, BaseCalendarSource] = {}
        self.is_running = False
        self.last_sync = {}  # Track last sync time per account

        # Sync status tracking
        self.sync_status = {
            'last_full_sync': None,
            'currently_syncing': False,
            'errors': [],
            'total_events': 0,
            'total_calendars': 0
        }

        # Thread safety
        self._lock = threading.Lock()

    def start(self):
        """Start the sync engine and scheduler"""
        if self.is_running:
            return

        print("Starting Calendar Sync Engine...")

        # Initialize calendar sources
        self._initialize_sources()

        # Start background scheduler
        sync_interval = config.get('sync.interval_minutes', 15)
        self.scheduler.add_job(
            func=self._scheduled_sync,
            trigger=IntervalTrigger(minutes=sync_interval),
            id='calendar_sync',
            name='Calendar Synchronization',
            replace_existing=True
        )

        self.scheduler.start()
        self.is_running = True

        print(f"✓ Sync engine started (interval: {sync_interval} minutes)")

        # Do initial sync in background thread
        sync_thread = threading.Thread(target=self._initial_sync, daemon=True)
        sync_thread.start()

    def stop(self):
        """Stop the sync engine"""
        if not self.is_running:
            return

        print("Stopping Calendar Sync Engine...")
        self.scheduler.shutdown()
        self.is_running = False
        print("✓ Sync engine stopped")

    def _initialize_sources(self):
        """Initialize all configured calendar sources"""
        try:
            accounts = config.list_accounts()

            # Initialize Google accounts
            # Initialize Google accounts
            for account in accounts['google']:
                if account.get('enabled', True):
                    account_id = account['id']
                    source = GoogleCalendarSource(account_id, account)

                    # Load OAuth credentials if available
                    stored_creds = config.get_credentials(account_id)
                    if stored_creds and 'client_id' in stored_creds:
                        source.set_oauth_credentials(
                            stored_creds['client_id'],
                            stored_creds['client_secret']
                        )

                        # NEW: Load the OAuth token if it exists
                        if 'google_token' in stored_creds:
                            source.set_token(stored_creds['google_token'])

                    self.sources[account_id] = source

            # Initialize Apple accounts
            # Initialize Apple accounts
            for account in accounts['apple']:
                if account.get('enabled', True):
                    account_id = account['id']
                    source = AppleCalendarSource(account_id, account)

                    # Authenticate if credentials are available
                    stored_creds = config.get_credentials(account_id)
                    if stored_creds and 'app_password' in stored_creds:
                        # Authenticate the source
                        import asyncio
                        try:
                            authenticated = asyncio.run(source.authenticate())
                            if authenticated:
                                self.sources[account_id] = source
                            else:
                                print(f"  ⚠ Failed to authenticate Apple account: {account.get('display_name')}")
                        except Exception as e:
                            print(f"  ⚠ Error authenticating Apple account: {e}")
                    else:
                        # Add source but it will need authentication later
                        self.sources[account_id] = source

            print(f"✓ Initialized {len(self.sources)} calendar sources")

        except Exception as e:
            print(f"Error initializing sources: {e}")
            self.sync_status['errors'].append({
                'time': datetime.now().isoformat(),
                'error': str(e),
                'type': 'initialization'
            })

    def _initial_sync(self):
        """Perform initial sync in background"""
        try:
            time.sleep(2)  # Give server time to fully start
            self.sync_all()
        except Exception as e:
            print(f"Initial sync error: {e}")

    def _scheduled_sync(self):
        """Scheduled sync job (runs in scheduler thread)"""
        try:
            self.sync_all()
        except Exception as e:
            print(f"Scheduled sync error: {e}")
            with self._lock:
                self.sync_status['errors'].append({
                    'time': datetime.now().isoformat(),
                    'error': str(e),
                    'type': 'scheduled_sync'
                })

    def sync_all(self) -> bool:
        """Sync all configured calendar sources - FIXED VERSION

        Returns:
            True if sync completed successfully
        """
        with self._lock:
            if self.sync_status['currently_syncing']:
                print("Sync already in progress, skipping...")
                return False

            self.sync_status['currently_syncing'] = True
            self.sync_status['errors'] = []

        start_time = datetime.now()
        print(f"Starting full calendar sync at {start_time.strftime('%H:%M:%S')}")

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
                    print(error_msg)
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
            print(f"✓ Sync completed in {duration:.1f}s: {total_events} events from {total_calendars} calendars")

            return True

        except Exception as e:
            print(f"Full sync error: {e}")
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

    def _sync_source(self, source: BaseCalendarSource) -> tuple:
        """Sync a single calendar source - FIXED VERSION

        Args:
            source: Calendar source to sync

        Returns:
            Tuple of (events_count, calendars_count)
        """
        account_id = source.account_id
        display_name = source.config.get('display_name', account_id)

        print(f"  Syncing {display_name}...")

        try:
            # Authenticate if needed (synchronous version)
            if not source.is_authenticated:
                # For now, skip authentication if not already done
                # TODO: Implement proper web-based auth flow
                print(f"    ⚠ Authentication required for {display_name}")
                return 0, 0

            # Get calendars (convert async to sync)
            calendars = self._run_sync(source.get_calendars())
            if not calendars:
                print(f"    ⚠ No calendars found for {display_name}")
                return 0, 0

            # Store calendar list
            self.cache_manager.store_calendars(account_id, calendars)

            # Define sync date range (past 30 days, future 90 days)
            start_date = datetime.now() - timedelta(days=30)
            end_date = datetime.now() + timedelta(days=90)

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
                    print(f"    Syncing calendar: {calendar_name}")
                    events = self._run_sync(source.get_events(calendar_id, start_date, end_date))

                    if events:
                        # Store events in cache
                        self.cache_manager.store_events(account_id, calendar_id, events)
                        total_events += len(events)
                        print(f"      ✓ {len(events)} events")
                    else:
                        print(f"      • No events")

                except Exception as e:
                    print(f"      ⚠ Error syncing calendar {calendar_name}: {e}")

            print(f"    ✓ {display_name}: {total_events} events from {len(calendars)} calendars")
            return total_events, len(calendars)

        except Exception as e:
            print(f"    ✗ Error syncing source {display_name}: {e}")
            return 0, 0

    def _run_sync(self, coroutine):
        """Convert async coroutine to synchronous call - FIXED VERSION"""
        import asyncio

        try:
            # Try to get existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, we can't use run_until_complete
                # For now, return empty result
                print("    Warning: Cannot run async operation in running loop")
                return []
        except RuntimeError:
            # No event loop, create new one
            loop = None

        try:
            if loop is None or not loop.is_running():
                return asyncio.run(coroutine)
            else:
                # Fallback: return empty result for now
                # TODO: Implement proper async handling
                return []
        except Exception as e:
            print(f"    Error running async operation: {e}")
            return []

    def sync_account(self, account_id: str) -> bool:
        """Sync a specific account

        Args:
            account_id: Account to sync

        Returns:
            True if sync successful
        """
        if account_id not in self.sources:
            print(f"Account not found: {account_id}")
            return False

        try:
            with self._lock:
                if self.sync_status['currently_syncing']:
                    return False
                self.sync_status['currently_syncing'] = True

            try:
                events, calendars = self._sync_source(self.sources[account_id])
                self.last_sync[account_id] = datetime.now()
                print(f"✓ Account {account_id} synced: {events} events from {calendars} calendars")
                return True
            finally:
                with self._lock:
                    self.sync_status['currently_syncing'] = False

        except Exception as e:
            print(f"Error syncing account {account_id}: {e}")
            return False

    def get_events(self, start_date: datetime = None, end_date: datetime = None,
                   account_ids: List[str] = None, calendar_ids: List[str] = None) -> List[CalendarEvent]:
        """Get cached events with optional filtering

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
            print(f"Error getting events: {e}")
            return []

    def get_calendars(self, account_id: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get cached calendar information

        Args:
            account_id: Specific account ID (None = all accounts)

        Returns:
            Dict mapping account_id to list of calendars
        """
        try:
            return self.cache_manager.get_calendars(account_id)
        except Exception as e:
            print(f"Error getting calendars: {e}")
            return {}

    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status and statistics

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
        """Force immediate sync of all sources

        Returns:
            True if sync started successfully
        """
        with self._lock:
            if self.sync_status['currently_syncing']:
                return False

        # Run sync in background thread instead of async task
        sync_thread = threading.Thread(target=self.sync_all, daemon=True)
        sync_thread.start()
        return True

    def add_account(self, account_type: str, account_config: Dict[str, Any]) -> str:
        """Add a new account and initialize its source

        Args:
            account_type: 'google' or 'apple'
            account_config: Account configuration dict

        Returns:
            Account ID
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
            print(f"✓ Added {account_type} account: {account_config.get('display_name', account_id)}")

            return account_id

        except Exception as e:
            print(f"Error adding account: {e}")
            raise

    def remove_account(self, account_id: str):
        """Remove an account and clean up its data

        Args:
            account_id: Account to remove
        """
        try:
            if account_id in self.sources:
                del self.sources[account_id]

            if account_id in self.last_sync:
                del self.last_sync[account_id]

            # Clean up cached data
            self.cache_manager.clear_account_data(account_id)

            print(f"✓ Removed account: {account_id}")

        except Exception as e:
            print(f"Error removing account {account_id}: {e}")


# Global sync engine instance
sync_engine = SyncEngine()
