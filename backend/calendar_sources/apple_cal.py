# server/calendar_sources/apple_cal.py
"""
Apple iCloud Calendar integration using CalDAV protocol
Supports app-specific passwords for secure access
All methods are synchronous (no async/await)
"""

import re
import logging
from datetime import datetime, date, timezone
from typing import List, Dict, Any, Optional

import caldav
from caldav.lib.error import AuthorizationError, DAVError
import vobject

from .base import BaseCalendarSource, CalendarEvent
from ..config.settings import config
from ..config.constants import APPLE_CALDAV_SERVER, APPLE_APP_PASSWORD_LENGTH, COLOR_APPLE

logger = logging.getLogger(__name__)


class AppleCalendarSource(BaseCalendarSource):
    """Apple iCloud Calendar integration via CalDAV"""

    def __init__(self, account_id: str, account_config: Dict[str, Any]):
        """
        Initialize Apple Calendar source

        Args:
            account_id: Unique identifier for this account
            account_config: Account configuration dictionary
        """
        super().__init__(account_id, account_config)
        self.client: Optional[caldav.DAVClient] = None
        self.principal: Optional[caldav.Principal] = None
        self.username: str = account_config.get('username', '')
        self.server_url: str = account_config.get('server_url', APPLE_CALDAV_SERVER)
        self.password: Optional[str] = None  # App-specific password

    def authenticate(self) -> bool:
        """
        Authenticate with Apple iCloud CalDAV

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Try to load stored password
            stored_creds = config.get_credentials(self.account_id)

            if not stored_creds or 'app_password' not in stored_creds:
                logger.warning(f"No app-specific password found for {self.config.get('display_name')}")
                return False

            self.password = stored_creds['app_password']
            # Create CalDAV client
            self.client = caldav.DAVClient(
                url=self.server_url,
                username=self.username,
                password=self.password
            )

            # Test connection and get principal
            self.principal = self.client.principal()

            # Test access by getting calendar list
            _ = self.principal.calendars()

            self.is_authenticated = True
            logger.info(f"✓ Successfully authenticated Apple account: {self.config.get('display_name')}")
            return True

        except AuthorizationError as e:
            logger.error(f"Authentication failed for Apple account {self.username}: {e}")
            logger.info("Please check your username and app-specific password")
            self.is_authenticated = False
            return False

        except DAVError as e:
            logger.error(f"CalDAV server error for {self.username}: {e}", exc_info=True)
            self.is_authenticated = False
            return False

        except ConnectionError as e:
            logger.error(f"Network connection error for {self.username}: {e}")
            self.is_authenticated = False
            return False

        except Exception as e:
            logger.error(f"Unexpected authentication error for {self.account_id}: {e}", exc_info=True)
            self.is_authenticated = False
            raise

    def get_calendars(self) -> List[Dict[str, Any]]:
        """
        Get list of Apple iCloud calendars

        Returns:
            List of calendar info dicts
        """
        if not self.is_authenticated:
            if not self.authenticate():
                logger.warning(f"Cannot get calendars, authentication failed for {self.account_id}")
                return []

        try:
            calendars = self.principal.calendars()
            result = []

            for cal in calendars:
                try:
                    # Get basic calendar properties
                    name = cal.name or 'Unnamed Calendar'

                    # Try to get display name if available
                    try:
                        props = cal.get_properties([caldav.dav.DisplayName()])
                        name = str(props.get(caldav.dav.DisplayName.tag, name))
                    except (DAVError, AttributeError):
                        pass

                    # Use default color since CalendarColor might not be available
                    color = self.config.get('color', COLOR_APPLE)

                    result.append({
                        'id': str(cal.url),
                        'name': name,
                        'description': '',
                        'color': color,
                        'primary': 'personal' in name.lower() or 'home' in name.lower(),
                        'access_role': 'owner'
                    })

                    logger.debug(f"Found calendar: {name}")

                except (DAVError, AttributeError) as e:
                    logger.warning(f"Error processing calendar: {e}")
                    continue

                except Exception as e:
                    logger.error(f"Unexpected error processing calendar: {e}", exc_info=True)
                    continue

            logger.info(f"Retrieved {len(result)} calendars for {self.config.get('display_name')}")
            return result

        except DAVError as e:
            logger.error(f"CalDAV error getting calendars for {self.account_id}: {e}", exc_info=True)
            return []

        except ConnectionError as e:
            logger.error(f"Network error getting calendars for {self.account_id}: {e}")
            return []

        except Exception as e:
            logger.error(f"Unexpected error getting calendars for {self.account_id}: {e}", exc_info=True)
            raise

    def get_events(
            self,
            calendar_id: str,
            start_date: datetime,
            end_date: datetime
    ) -> List[CalendarEvent]:
        """
        Get events from an Apple calendar

        Args:
            calendar_id: Calendar URL/ID
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of calendar events
        """
        if not self.is_authenticated:
            if not self.authenticate():
                logger.warning(f"Cannot get events, authentication failed for {self.account_id}")
                return []

        try:
            # Find the calendar by URL
            calendar = None
            for cal in self.principal.calendars():
                if str(cal.url) == calendar_id:
                    calendar = cal
                    break

            if not calendar:
                logger.warning(f"Calendar not found: {calendar_id}")
                return []

            # Search for events in date range
            events = calendar.search(
                start=start_date,
                end=end_date,
                event=True,
                expand=True
            )

            result = []
            for event in events:
                try:
                    cal_event = self._parse_apple_event(event, calendar_id)
                    print(f"EVENT => {cal_event}")
                    if cal_event:
                        result.append(cal_event)

                except (ValueError, AttributeError) as e:
                    logger.warning(f"Error parsing Apple event: {e}")
                    continue

                except Exception as e:
                    logger.error(f"Unexpected error parsing event: {e}", exc_info=True)
                    continue

            logger.info(f"Retrieved {len(result)} events from calendar {calendar_id}")
            return result

        except DAVError as e:
            logger.error(f"CalDAV error getting events for {self.account_id}: {e}", exc_info=True)
            return []

        except ConnectionError as e:
            logger.error(f"Network error getting events for {self.account_id}: {e}")
            return []

        except Exception as e:
            logger.error(f"Unexpected error getting events for {self.account_id}: {e}", exc_info=True)
            raise

    def _parse_apple_event(self, event: caldav.Event, calendar_id: str) -> Optional[CalendarEvent]:
        """
        Parse a CalDAV event into CalendarEvent format

        Args:
            event: Raw event data from CalDAV
            calendar_id: Calendar ID this event belongs to

        Returns:
            CalendarEvent object or None if parsing fails
        """
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
                logger.debug("No VEVENT component found in event")
                return None

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
                color=self.config.get('color', COLOR_APPLE),
                attendees=attendees
            )

            return cal_event

        except AttributeError as e:
            logger.warning(f"Missing required event attribute: {e}")
            return None

        except ValueError as e:
            logger.warning(f"Invalid event data format: {e}")
            return None

        except Exception as e:
            logger.error(f"Unexpected error parsing event: {e}", exc_info=True)
            return None

    def get_source_type(self) -> str:
        """Get source type identifier"""
        return "apple"

    def close(self) -> None:
        """Clean up resources"""
        if self.client:
            # CalDAV client doesn't require explicit cleanup
            self.client = None
            self.principal = None
            logger.debug(f"Closed Apple Calendar connection for {self.account_id}")


class AppleCalendarSetup:
    """Helper class for Apple iCloud Calendar setup"""

    @staticmethod
    def print_setup_instructions() -> None:
        """Print instructions for setting up Apple iCloud CalDAV"""
        instructions = """
{'='*60}
APPLE ICLOUD CALENDAR SETUP
{'='*60}
Apple iCloud uses CalDAV protocol with App-Specific Passwords.

Requirements:
• Apple ID with iCloud Calendar enabled
• Two-factor authentication enabled on your Apple ID
• App-Specific Password (generated during setup)

The setup wizard will guide you through creating the
App-Specific Password when you add an Apple account.
{'='*60}
"""
        logger.info("Printing Apple Calendar setup instructions")
        print(instructions)

    @staticmethod
    def setup_apple_account(
            display_name: str,
            username: str,
            server_url: Optional[str] = None
    ) -> str:
        """
        Set up a new Apple iCloud Calendar account

        Args:
            display_name: Human-readable name for this account
            username: iCloud email address
            server_url: CalDAV server URL (optional, defaults to iCloud)

        Returns:
            Account ID

        Raises:
            ValueError: If parameters are invalid
        """
        import uuid

        if server_url is None:
            server_url = APPLE_CALDAV_SERVER

        # Validate email format
        if '@' not in username:
            raise ValueError("Username must be a valid email address")

        if not AppleCalendarSetup.validate_username(username):
            raise ValueError("Invalid email format")

        # Generate unique account ID
        account_id = f"apple_{uuid.uuid4().hex[:8]}"

        # Add account configuration
        config.add_apple_account(account_id, display_name, username, server_url)

        logger.info(f"✓ Apple account '{display_name}' configured ({account_id})")
        print(f"✓ Apple account '{display_name}' configured with ID: {account_id}")
        print(f"  Username: {username}")
        print(f"  Server: {server_url}")
        print("Run authentication to set up App-Specific Password and sync calendars.")

        return account_id

    @staticmethod
    def validate_username(username: str) -> bool:
        """
        Validate Apple ID username format

        Args:
            username: Username to validate

        Returns:
            True if valid format
        """
        # Basic email validation
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        is_valid = bool(re.match(pattern, username))

        if not is_valid:
            logger.warning(f"Invalid username format: {username}")

        return is_valid