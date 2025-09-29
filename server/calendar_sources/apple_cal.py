# server/calendar_sources/apple_cal.py
"""
Apple iCloud Calendar integration using CalDAV protocol
Supports app-specific passwords for secure access
"""

import re
from datetime import datetime, date, timezone
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin

import caldav
from caldav.lib.error import AuthorizationError, DAVError
import vobject

from .base import BaseCalendarSource, CalendarEvent
from ..config.settings import config


class AppleCalendarSource(BaseCalendarSource):
    """Apple iCloud Calendar integration via CalDAV"""

    def __init__(self, account_id: str, account_config: Dict[str, Any]):
        super().__init__(account_id, account_config)
        self.client = None
        self.principal = None
        self.username = account_config.get('username')
        self.server_url = account_config.get('server_url', 'https://caldav.icloud.com')
        self.password = None  # App-specific password

    async def authenticate(self) -> bool:
        """Authenticate with Apple iCloud CalDAV

        Returns:
            True if authentication successful
        """
        try:
            # Try to load stored password
            stored_creds = config.get_credentials(self.account_id)

            if stored_creds and 'app_password' in stored_creds:
                self.password = stored_creds['app_password']
            else:
                # Need to get app-specific password
                print(f"No app-specific password found for {self.config.get('display_name')}")
                return False

            # Create CalDAV client
            self.client = caldav.DAVClient(
                url=self.server_url,
                username=self.username,
                password=self.password
            )

            # Test connection
            self.principal = self.client.principal()

            # Test access by getting calendar list
            calendars = self.principal.calendars()

            self.is_authenticated = True
            print(f"✓ Successfully authenticated Apple account: {self.config.get('display_name')}")
            return True

        except AuthorizationError:
            print(f"Authentication failed for Apple account {self.username}")
            print("Please check your username and app-specific password")
            return False
        except Exception as e:
            print(f"Apple CalDAV authentication error for {self.account_id}: {e}")
            return False

    async def get_calendars(self) -> List[Dict[str, Any]]:
        """Get list of Apple iCloud calendars

        Returns:
            List of calendar info dicts
        """
        if not self.is_authenticated:
            if not await self.authenticate():
                return []

        try:
            calendars = self.principal.calendars()

            result = []
            for cal in calendars:
                try:
                    # Get basic calendar properties
                    # Note: Some caldav versions don't support CalendarColor
                    name = cal.name or 'Unnamed Calendar'

                    # Try to get display name if available
                    try:
                        props = cal.get_properties([caldav.dav.DisplayName()])
                        name = str(props.get(caldav.dav.DisplayName.tag, name))
                    except Exception:
                        pass

                    # Use a default color since CalendarColor might not be available
                    color = self.config.get('color', '#FF6B6B')

                    result.append({
                        'id': str(cal.url),
                        'name': name,
                        'description': '',
                        'color': color,
                        'primary': 'personal' in name.lower() or 'home' in name.lower(),
                        'access_role': 'owner'
                    })

                    print(f"      Found calendar: {name}")

                except Exception as e:
                    print(f"      Warning: Error processing calendar: {e}")
                    continue

            return result

        except Exception as e:
            print(f"Error getting Apple calendars: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def get_events(self, calendar_id: str, start_date: datetime,
                         end_date: datetime) -> List[CalendarEvent]:
        """Get events from an Apple calendar

        Args:
            calendar_id: Calendar URL/ID
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of calendar events
        """
        if not self.is_authenticated:
            if not await self.authenticate():
                return []

        try:
            # Find the calendar by URL
            calendar = None
            for cal in self.principal.calendars():
                if cal.url == calendar_id:
                    calendar = cal
                    break

            if not calendar:
                print(f"Calendar not found: {calendar_id}")
                return []

            # Search for events in date range
            events = calendar.date_search(
                start=start_date.date(),
                end=end_date.date(),
                expand=True  # Expand recurring events
            )

            result = []
            for event in events:
                try:
                    # Parse the iCalendar data
                    vcal = vobject.readOne(event.data)

                    # Find the VEVENT component
                    vevent = None
                    for component in vcal.getChildren():
                        if component.name == 'VEVENT':
                            vevent = component
                            break

                    if not vevent:
                        continue

                    # Extract event data
                    title = str(vevent.summary.value) if hasattr(vevent, 'summary') else 'No Title'
                    description = str(vevent.description.value) if hasattr(vevent, 'description') else ''
                    location = str(vevent.location.value) if hasattr(vevent, 'location') else ''

                    # Handle start/end times
                    dtstart = vevent.dtstart.value
                    dtend = vevent.dtend.value if hasattr(vevent, 'dtend') else dtstart

                    # Determine if all-day event
                    all_day = isinstance(dtstart, date) and not isinstance(dtstart, datetime)

                    # Convert to datetime objects
                    if all_day:
                        start_dt = datetime.combine(dtstart, datetime.min.time())
                        end_dt = datetime.combine(dtend, datetime.min.time())
                        start_dt = start_dt.replace(tzinfo=timezone.utc)
                        end_dt = end_dt.replace(tzinfo=timezone.utc)
                    else:
                        start_dt = dtstart
                        end_dt = dtend

                        # Ensure timezone awareness
                        if start_dt.tzinfo is None:
                            start_dt = start_dt.replace(tzinfo=timezone.utc)
                        if end_dt.tzinfo is None:
                            end_dt = end_dt.replace(tzinfo=timezone.utc)

                    # Extract attendees
                    attendees = []
                    if hasattr(vevent, 'attendee_list'):
                        for attendee in vevent.attendee_list:
                            email = str(attendee.value).replace('mailto:', '')
                            attendees.append(email)

                    # Get event UID
                    event_id = str(getattr(vevent, 'uid', event.url))

                    # Create event object
                    cal_event = CalendarEvent(
                        id=event_id,
                        title=title,
                        description=description,
                        start_time=start_dt,
                        end_time=end_dt,
                        all_day=all_day,
                        location=location,
                        calendar_id=calendar_id,
                        account_id=self.account_id,
                        color=self.config.get('color', '#FF6B6B'),
                        attendees=attendees
                    )

                    result.append(cal_event)

                except Exception as e:
                    print(f"Error parsing Apple event: {e}")
                    continue

            return result

        except Exception as e:
            print(f"Error getting Apple events: {e}")
            return []

    def get_source_type(self) -> str:
        """Get source type identifier"""
        return "apple"


class AppleCalendarSetup:
    """Helper class for Apple iCloud Calendar setup"""

    @staticmethod
    def print_setup_instructions():
        """Print instructions for setting up Apple iCloud CalDAV"""
        print("\n" + "=" * 60)
        print("APPLE ICLOUD CALENDAR SETUP")
        print("=" * 60)
        print("Apple iCloud uses CalDAV protocol with App-Specific Passwords.")
        print()
        print("Requirements:")
        print("• Apple ID with iCloud Calendar enabled")
        print("• Two-factor authentication enabled on your Apple ID")
        print("• App-Specific Password (generated during setup)")
        print()
        print("The setup wizard will guide you through creating the")
        print("App-Specific Password when you add an Apple account.")
        print("=" * 60)

    @staticmethod
    def setup_apple_account(display_name: str, username: str,
                            server_url: str = None) -> str:
        """Set up a new Apple iCloud Calendar account

        Args:
            display_name: Human-readable name for this account
            username: iCloud email address
            server_url: CalDAV server URL (optional, defaults to iCloud)

        Returns:
            Account ID
        """
        import uuid

        if server_url is None:
            server_url = "https://caldav.icloud.com"

        # Validate email format
        if '@' not in username:
            raise ValueError("Username must be a valid email address")

        # Generate unique account ID
        account_id = f"apple_{uuid.uuid4().hex[:8]}"

        # Add account configuration
        config.add_apple_account(account_id, display_name, username, server_url)

        print(f"✓ Apple account '{display_name}' configured with ID: {account_id}")
        print(f"  Username: {username}")
        print(f"  Server: {server_url}")
        print("Run authentication to set up App-Specific Password and sync calendars.")

        return account_id

    @staticmethod
    def validate_username(username: str) -> bool:
        """Validate Apple ID username format

        Args:
            username: Username to validate

        Returns:
            True if valid format
        """
        # Basic email validation
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, username) is not None
