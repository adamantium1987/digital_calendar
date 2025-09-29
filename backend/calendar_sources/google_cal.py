# server/calendar_sources/google_cal.py
"""
Google Calendar API integration using OAuth2
Handles authentication, calendar listing, and event synchronization
All methods are synchronous (no async/await)
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError, GoogleAuthError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
# from google_auth_oauthlib.exceptions import OAuthError
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .base import BaseCalendarSource, CalendarEvent
from ..config.settings import config
from ..config.constants import GOOGLE_CALENDAR_SCOPES, GOOGLE_COLOR_MAP, COLOR_GOOGLE

logger = logging.getLogger(__name__)


class GoogleCalendarSource(BaseCalendarSource):
    """Google Calendar integration via Google Calendar API"""

    def __init__(self, account_id: str, account_config: Dict[str, Any]):
        """
        Initialize Google Calendar source

        Args:
            account_id: Unique identifier for this account
            account_config: Account configuration dictionary
        """
        super().__init__(account_id, account_config)
        self.service = None
        self.credentials: Optional[Credentials] = None
        self.client_id: Optional[str] = None
        self.client_secret: Optional[str] = None

    def set_oauth_credentials(self, client_id: str, client_secret: str) -> None:
        """
        Set OAuth2 client credentials

        Args:
            client_id: Google OAuth2 client ID
            client_secret: Google OAuth2 client secret
        """
        self.client_id = client_id
        self.client_secret = client_secret
        logger.debug(f"Set OAuth credentials for {self.account_id}")

    def set_token(self, token_data: Dict[str, Any]) -> None:
        """
        Set OAuth token from stored credentials

        Args:
            token_data: Dictionary containing token, refresh_token, etc.
        """
        try:
            self.credentials = Credentials.from_authorized_user_info(
                token_data, GOOGLE_CALENDAR_SCOPES
            )

            # Refresh if expired
            if not self.credentials.valid:
                if self.credentials.expired and self.credentials.refresh_token:
                    try:
                        self.credentials.refresh(Request())
                        self._save_credentials()
                        logger.info(f"Refreshed token for {self.config.get('display_name')}")
                    except RefreshError as e:
                        logger.error(f"Token refresh failed for {self.account_id}: {e}")
                        self.is_authenticated = False
                        return

            # Build the service
            self.service = build('calendar', 'v3', credentials=self.credentials)
            self.is_authenticated = True
            logger.debug(f"Token set successfully for {self.account_id}")

        except GoogleAuthError as e:
            logger.error(f"Google auth error setting token for {self.account_id}: {e}", exc_info=True)
            self.is_authenticated = False

        except Exception as e:
            logger.error(f"Unexpected error setting token for {self.account_id}: {e}", exc_info=True)
            self.is_authenticated = False
            raise

    def authenticate(self) -> bool:
        """
        Authenticate with Google Calendar API

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Try to load existing credentials
            stored_creds = config.get_credentials(self.account_id)

            if stored_creds and 'google_token' in stored_creds:
                # Reconstruct credentials from stored data
                creds_data = stored_creds['google_token']
                self.credentials = Credentials.from_authorized_user_info(
                    creds_data, GOOGLE_CALENDAR_SCOPES
                )

                # Refresh if expired
                if not self.credentials.valid:
                    if self.credentials.expired and self.credentials.refresh_token:
                        try:
                            self.credentials.refresh(Request())
                            self._save_credentials()
                            logger.info(f"Refreshed token for {self.config.get('display_name')}")
                        except RefreshError as e:
                            logger.error(f"Token refresh failed for {self.account_id}: {e}")
                            return self._start_oauth_flow()
                    else:
                        logger.warning(f"No refresh token available for {self.account_id}")
                        return self._start_oauth_flow()
            else:
                logger.info(f"No stored credentials for {self.account_id}, starting OAuth")
                return self._start_oauth_flow()

            # Build the service
            self.service = build('calendar', 'v3', credentials=self.credentials)
            self.is_authenticated = True
            logger.info(f"✓ Authenticated Google account: {self.config.get('display_name')}")
            return True

        except GoogleAuthError as e:
            logger.error(f"Google authentication error for {self.account_id}: {e}", exc_info=True)
            self.is_authenticated = False
            return False

        except Exception as e:
            logger.error(f"Unexpected authentication error for {self.account_id}: {e}", exc_info=True)
            self.is_authenticated = False
            raise

    def _start_oauth_flow(self) -> bool:
        """
        Start OAuth2 flow for Google Calendar access

        Returns:
            True if authentication successful, False otherwise
        """
        if not self.client_id or not self.client_secret:
            logger.error(f"OAuth2 credentials not set for account {self.account_id}")
            return False

        # Create client config
        client_config = {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost:8080/callback"]
            }
        }

        try:
            # Create flow
            flow = Flow.from_client_config(
                client_config,
                scopes=GOOGLE_CALENDAR_SCOPES,
                redirect_uri="http://localhost:8080/callback"
            )

            # Get authorization URL
            auth_url, _ = flow.authorization_url(prompt='consent')

            logger.info(f"Google Calendar Authorization Required for {self.config.get('display_name')}")
            logger.info(f"Visit: {auth_url}")
            print(f"\n{'=' * 70}")
            print(f"Google Calendar Authorization Required")
            print(f"Account: {self.config.get('display_name', self.account_id)}")
            print(f"{'=' * 70}")
            print(f"\nPlease visit this URL to authorize access:")
            print(f"\n{auth_url}\n")
            print("After authorization, you'll be redirected to a localhost URL.")
            print("Copy the ENTIRE URL from your browser and paste it here:")
            print(f"{'=' * 70}")

            # Get authorization response
            authorization_response = input("\nEnter the full redirect URL: ").strip()

            # Exchange authorization code for credentials
            flow.fetch_token(authorization_response=authorization_response)
            self.credentials = flow.credentials

            # Save credentials
            self._save_credentials()

            # Build service
            self.service = build('calendar', 'v3', credentials=self.credentials)
            self.is_authenticated = True

            logger.info(f"✓ Successfully authenticated Google account: {self.config.get('display_name')}")
            print(f"\n✓ Successfully authenticated Google account: {self.config.get('display_name')}")
            print(f"{'=' * 70}\n")
            return True

        except OAuthError as e:
            logger.error(f"OAuth flow error for {self.account_id}: {e}", exc_info=True)
            return False

        except ValueError as e:
            logger.error(f"Invalid authorization response for {self.account_id}: {e}")
            return False

        except Exception as e:
            logger.error(f"Unexpected OAuth error for {self.account_id}: {e}", exc_info=True)
            raise

    def _save_credentials(self) -> None:
        """Save credentials to encrypted storage"""
        if not self.credentials:
            logger.warning(f"No credentials to save for {self.account_id}")
            return

        try:
            creds_data = {
                'token': self.credentials.token,
                'refresh_token': self.credentials.refresh_token,
                'token_uri': self.credentials.token_uri,
                'client_id': self.credentials.client_id,
                'client_secret': self.credentials.client_secret,
                'scopes': self.credentials.scopes
            }

            # Get existing credentials to preserve OAuth client info
            stored = config.get_credentials(self.account_id) or {}
            stored['google_token'] = creds_data

            config.store_credentials(self.account_id, stored)
            logger.debug(f"Saved credentials for {self.account_id}")

        except Exception as e:
            logger.error(f"Error saving credentials for {self.account_id}: {e}", exc_info=True)
            raise

    def get_calendars(self) -> List[Dict[str, Any]]:
        """
        Get list of Google calendars for this account

        Returns:
            List of calendar info dicts with id, name, description, color, etc.
        """
        if not self.is_authenticated:
            if not self.authenticate():
                logger.warning(f"Cannot get calendars, authentication failed for {self.account_id}")
                return []

        try:
            # Get calendar list from Google API
            calendars_result = self.service.calendarList().list().execute()
            calendars = calendars_result.get('items', [])

            # Convert to standard format
            result = []
            for cal in calendars:
                result.append({
                    'id': cal['id'],
                    'name': cal['summary'],
                    'description': cal.get('description', ''),
                    'color': cal.get('backgroundColor', COLOR_GOOGLE),
                    'primary': cal.get('primary', False),
                    'access_role': cal.get('accessRole', 'reader'),
                    'selected': cal.get('selected', True),
                    'timezone': cal.get('timeZone', 'UTC')
                })

            logger.info(f"Retrieved {len(result)} calendars for {self.config.get('display_name')}")
            return result

        except HttpError as e:
            if e.resp.status == 401:
                # Token expired or invalid, clear authentication
                self.is_authenticated = False
                logger.warning(f"Authentication expired for {self.config.get('display_name')}, re-auth required")
            elif e.resp.status == 403:
                logger.error(f"Permission denied getting calendars for {self.account_id}: {e}")
            else:
                logger.error(f"HTTP error getting calendars for {self.account_id}: {e}", exc_info=True)
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
        Get events from a Google calendar

        Args:
            calendar_id: Google calendar ID
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of CalendarEvent objects
        """
        if not self.is_authenticated:
            if not self.authenticate():
                logger.warning(f"Cannot get events, authentication failed for {self.account_id}")
                return []

        try:
            # Format times for Google API (RFC3339 format)
            time_min = start_date.isoformat() if start_date.tzinfo else start_date.isoformat() + 'Z'
            time_max = end_date.isoformat() if end_date.tzinfo else end_date.isoformat() + 'Z'

            # Get events from Google API
            from ..config.constants import DEFAULT_MAX_EVENTS_PER_CALENDAR
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                maxResults=config.get('sync.max_events_per_calendar', DEFAULT_MAX_EVENTS_PER_CALENDAR),
                singleEvents=True,  # Expand recurring events
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])

            # Convert to standard CalendarEvent format
            result = []
            for event in events:
                try:
                    cal_event = self._parse_google_event(event, calendar_id)
                    if cal_event:
                        result.append(cal_event)
                except (ValueError, KeyError) as e:
                    logger.warning(f"Error parsing event {event.get('id', 'unknown')}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error parsing event {event.get('id', 'unknown')}: {e}", exc_info=True)
                    continue

            logger.info(f"Retrieved {len(result)} events from calendar {calendar_id}")
            return result

        except HttpError as e:
            if e.resp.status == 401:
                self.is_authenticated = False
                logger.warning(f"Authentication expired for {self.config.get('display_name')}, re-auth required")
            elif e.resp.status == 404:
                logger.warning(f"Calendar not found: {calendar_id}")
            else:
                logger.error(f"HTTP error getting events for {self.account_id}: {e}", exc_info=True)
            return []

        except ConnectionError as e:
            logger.error(f"Network error getting events for {self.account_id}: {e}")
            return []

        except Exception as e:
            logger.error(f"Unexpected error getting events for {self.account_id}: {e}", exc_info=True)
            raise

    def _parse_google_event(self, event: Dict[str, Any], calendar_id: str) -> Optional[CalendarEvent]:
        """
        Parse a Google Calendar event into CalendarEvent format

        Args:
            event: Raw event data from Google API
            calendar_id: Calendar ID this event belongs to

        Returns:
            CalendarEvent object or None if parsing fails
        """
        try:
            # Handle all-day events vs timed events
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))

            # Parse datetime
            if 'T' in start:  # Timed event
                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                all_day = False
            else:  # All-day event
                start_dt = datetime.fromisoformat(f"{start}T00:00:00+00:00")
                end_dt = datetime.fromisoformat(f"{end}T00:00:00+00:00")
                all_day = True

            # Extract attendees
            attendees = []
            if 'attendees' in event:
                attendees = [
                    att.get('email', att.get('displayName', 'Unknown'))
                    for att in event['attendees']
                ]

            # Get event color
            event_color = self.config.get('color', COLOR_GOOGLE)
            if 'colorId' in event:
                event_color = GOOGLE_COLOR_MAP.get(event['colorId'], event_color)

            # Create CalendarEvent object
            cal_event = CalendarEvent(
                id=event['id'],
                title=event.get('summary', '(No Title)'),
                description=event.get('description', ''),
                start_time=start_dt,
                end_time=end_dt,
                all_day=all_day,
                location=event.get('location', ''),
                calendar_id=calendar_id,
                account_id=self.account_id,
                color=event_color,
                attendees=attendees
            )

            return cal_event

        except KeyError as e:
            logger.warning(f"Missing required event field: {e}")
            return None

        except ValueError as e:
            logger.warning(f"Invalid event data format: {e}")
            return None

        except Exception as e:
            logger.error(f"Unexpected error parsing Google event: {e}", exc_info=True)
            return None

    def get_source_type(self) -> str:
        """Get source type identifier"""
        return "google"

    def close(self) -> None:
        """Clean up resources"""
        if self.service:
            self.service.close()
            self.service = None
            logger.debug(f"Closed Google Calendar service for {self.account_id}")


class GoogleCalendarSetup:
    """Helper class for Google Calendar setup and OAuth2 configuration"""

    @staticmethod
    def print_setup_instructions() -> None:
        """Print detailed instructions for setting up Google Calendar API"""
        instructions = """
{'='*70}
GOOGLE CALENDAR API SETUP INSTRUCTIONS
{'='*70}

To use Google Calendar with Pi Calendar System, follow these steps:

1. CREATE GOOGLE CLOUD PROJECT
   • Go to: https://console.developers.google.com/
   • Click 'Select a project' → 'New Project'
   • Enter project name (e.g., 'Pi Calendar')
   • Click 'Create'

2. ENABLE GOOGLE CALENDAR API
   • In the project, go to 'APIs & Services' → 'Library'
   • Search for 'Google Calendar API'
   • Click on it and press 'Enable'

3. CREATE OAUTH 2.0 CREDENTIALS
   • Go to 'APIs & Services' → 'Credentials'
   • Click 'Create Credentials' → 'OAuth 2.0 Client ID'
   • If prompted, configure OAuth consent screen:
     - User Type: External
     - App name: Pi Calendar
     - User support email: your@email.com
     - Developer contact: your@email.com
     - Click 'Save and Continue' through remaining steps
   • Application type: 'Web application'
   • Name: 'Pi Calendar Client'
   • Authorized redirect URIs:
     - Add: http://localhost:8080/callback
   • Click 'Create'

4. DOWNLOAD CREDENTIALS
   • You'll see a popup with Client ID and Client Secret
   • Copy these values (you'll need them for setup)
   • Or download the JSON file for reference

5. ADD ACCOUNT IN PI CALENDAR
   • Open Pi Calendar web interface
   • Go to 'Account Setup' → 'Add Google Account'
   • Enter display name, Client ID, and Client Secret
   • Follow OAuth authorization flow

{'='*70}
IMPORTANT NOTES:
• Keep Client Secret secure (it's like a password)
• You can create multiple OAuth clients for different devices
• If you see 'unverified app' warning during OAuth, click 'Advanced'
  and then 'Go to Pi Calendar (unsafe)' - this is safe for personal use
{'='*70}
"""
        logger.info("Printing Google Calendar setup instructions")
        print(instructions)

    @staticmethod
    def setup_google_account(display_name: str, client_id: str, client_secret: str) -> str:
        """
        Set up a new Google Calendar account

        Args:
            display_name: Human-readable name for this account
            client_id: Google OAuth2 client ID
            client_secret: Google OAuth2 client secret

        Returns:
            Account ID

        Raises:
            ValueError: If parameters are invalid
        """
        import uuid

        # Validate inputs
        if not display_name or not display_name.strip():
            raise ValueError("Display name cannot be empty")

        if not client_id or not client_id.strip():
            raise ValueError("Client ID cannot be empty")

        if not client_secret or not client_secret.strip():
            raise ValueError("Client Secret cannot be empty")

        # Validate client ID format (basic check)
        if not client_id.endswith('.apps.googleusercontent.com'):
            logger.warning("Client ID doesn't match expected format")

        # Generate unique account ID
        account_id = f"google_{uuid.uuid4().hex[:8]}"

        # Add account configuration
        config.add_google_account(account_id, display_name)

        # Store OAuth credentials (client info only, not tokens yet)
        config.store_credentials(account_id, {
            'client_id': client_id,
            'client_secret': client_secret
        })

        logger.info(f"✓ Google account '{display_name}' configured ({account_id})")
        print(f"\n✓ Google account '{display_name}' configured")
        print(f"  Account ID: {account_id}")
        print(f"  Status: Ready for authentication")
        print(f"\nNext step: Start sync to begin OAuth flow\n")

        return account_id

    @staticmethod
    def validate_credentials(client_id: str, client_secret: str) -> bool:
        """
        Validate OAuth2 credentials format

        Args:
            client_id: Google OAuth2 client ID
            client_secret: Google OAuth2 client secret

        Returns:
            True if credentials appear valid
        """
        # Check client ID format
        if not client_id.endswith('.apps.googleusercontent.com'):
            logger.warning("Client ID format may be incorrect")
            return False

        # Check client secret format (starts with GOCSPX-)
        if not client_secret.startswith('GOCSPX-'):
            logger.warning("Client Secret format may be incorrect")

        # Check lengths
        if len(client_id) < 50 or len(client_secret) < 20:
            logger.warning("Credentials appear too short")
            return False

        return True