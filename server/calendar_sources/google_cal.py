# server/calendar_sources/google_cal.py
"""
Google Calendar API integration using OAuth2
Handles authentication, calendar listing, and event synchronization
"""

import os
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .base import BaseCalendarSource, CalendarEvent
from ..config.settings import config


class GoogleCalendarSource(BaseCalendarSource):
    """Google Calendar integration via Google Calendar API"""

    # OAuth2 scopes needed for calendar access
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

    def __init__(self, account_id: str, account_config: Dict[str, Any]):
        """Initialize Google Calendar source
        
        Args:
            account_id: Unique identifier for this account
            account_config: Account configuration dictionary
        """
        super().__init__(account_id, account_config)
        self.service = None
        self.credentials = None

        # These will be set during OAuth setup
        self.client_id = None
        self.client_secret = None

    def set_oauth_credentials(self, client_id: str, client_secret: str):
        """Set OAuth2 client credentials

        Args:
            client_id: Google OAuth2 client ID
            client_secret: Google OAuth2 client secret
        """
        self.client_id = client_id
        self.client_secret = client_secret

    def set_token(self, token_data: Dict[str, Any]):
        """Set OAuth token from stored credentials

        Args:
            token_data: Dictionary containing token, refresh_token, etc.
        """
        try:
            self.credentials = Credentials.from_authorized_user_info(token_data, self.SCOPES)

            # Refresh if expired
            if not self.credentials.valid:
                if self.credentials.expired and self.credentials.refresh_token:
                    self.credentials.refresh(Request())
                    self._save_credentials()

            # Build the service
            self.service = build('calendar', 'v3', credentials=self.credentials)
            self.is_authenticated = True

        except Exception as e:
            print(f"Error setting token: {e}")
            self.is_authenticated = False

    async def authenticate(self) -> bool:
        """Authenticate with Google Calendar API

        Returns:
            True if authentication successful
        """
        try:
            # Try to load existing credentials
            stored_creds = config.get_credentials(self.account_id)

            if stored_creds and 'google_token' in stored_creds:
                # Reconstruct credentials from stored data
                creds_data = stored_creds['google_token']
                self.credentials = Credentials.from_authorized_user_info(creds_data, self.SCOPES)

                # Refresh if expired
                if not self.credentials.valid:
                    if self.credentials.expired and self.credentials.refresh_token:
                        try:
                            self.credentials.refresh(Request())
                            # Save refreshed credentials
                            self._save_credentials()
                            print(f"  ✓ Refreshed Google token for {self.config.get('display_name')}")
                        except Exception as refresh_error:
                            print(f"  ✗ Token refresh failed: {refresh_error}")
                            # Need new authentication
                            return await self._start_oauth_flow()
                    else:
                        # Need new authentication
                        return await self._start_oauth_flow()
            else:
                # No stored credentials, start OAuth flow
                return await self._start_oauth_flow()

            # Build the service
            self.service = build('calendar', 'v3', credentials=self.credentials)
            self.is_authenticated = True
            return True

        except Exception as e:
            print(f"Google authentication error for {self.account_id}: {e}")
            return False

    async def _start_oauth_flow(self) -> bool:
        """Start OAuth2 flow for Google Calendar access

        This will print a URL for the user to visit and authorize access.
        In a production setup, this would be handled by a web interface.

        Returns:
            True if authentication successful
        """
        if not self.client_id or not self.client_secret:
            print(f"Error: OAuth2 credentials not set for account {self.account_id}")
            print("Please call set_oauth_credentials() first or configure via web interface")
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
                scopes=self.SCOPES,
                redirect_uri="http://localhost:8080/callback"
            )

            # Get authorization URL
            auth_url, _ = flow.authorization_url(prompt='consent')

            print(f"\n{'='*70}")
            print(f"Google Calendar Authorization Required")
            print(f"Account: {self.config.get('display_name', self.account_id)}")
            print(f"{'='*70}")
            print(f"\nPlease visit this URL to authorize access:")
            print(f"\n{auth_url}\n")
            print("After authorization, you'll be redirected to a localhost URL.")
            print("Copy the ENTIRE URL from your browser and paste it here:")
            print(f"{'='*70}")

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

            print(f"\n✓ Successfully authenticated Google account: {self.config.get('display_name')}")
            print(f"{'='*70}\n")
            return True

        except Exception as e:
            print(f"OAuth2 flow error: {e}")
            return False

    def _save_credentials(self):
        """Save credentials to encrypted storage"""
        if self.credentials:
            creds_data = {
                'token': self.credentials.token,
                'refresh_token': self.credentials.refresh_token,
                'token_uri': self.credentials.token_uri,
                'client_id': self.credentials.client_id,
                'client_secret': self.credentials.client_secret,
                'scopes': self.credentials.scopes
            }

            config.store_credentials(self.account_id, {'google_token': creds_data})

    async def get_calendars(self) -> List[Dict[str, Any]]:
        """Get list of Google calendars for this account

        Returns:
            List of calendar info dicts with id, name, description, color, etc.
        """
        if not self.is_authenticated:
            if not await self.authenticate():
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
                    'color': cal.get('backgroundColor', '#4285f4'),
                    'primary': cal.get('primary', False),
                    'access_role': cal.get('accessRole', 'reader'),
                    'selected': cal.get('selected', True),
                    'timezone': cal.get('timeZone', 'UTC')
                })

            return result

        except HttpError as e:
            print(f"Google Calendar API error getting calendars: {e}")
            if e.resp.status == 401:
                # Token expired or invalid, clear authentication
                self.is_authenticated = False
                print(f"  Authentication expired for {self.config.get('display_name')}, re-auth required")
            return []
        except Exception as e:
            print(f"Error getting Google calendars: {e}")
            return []

    async def get_events(self, calendar_id: str, start_date: datetime,
                         end_date: datetime) -> List[CalendarEvent]:
        """Get events from a Google calendar

        Args:
            calendar_id: Google calendar ID
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of CalendarEvent objects
        """
        if not self.is_authenticated:
            if not await self.authenticate():
                return []

        try:
            # Format times for Google API (RFC3339 format)
            time_min = start_date.isoformat() + 'Z' if start_date.tzinfo is None else start_date.isoformat()
            time_max = end_date.isoformat() + 'Z' if end_date.tzinfo is None else end_date.isoformat()

            # Get events from Google API
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                maxResults=config.get('sync.max_events_per_calendar', 1000),
                singleEvents=True,  # Expand recurring events
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])

            # Convert to standard CalendarEvent format
            result = []
            for event in events:
                try:
                    # Parse event data
                    cal_event = self._parse_google_event(event, calendar_id)
                    if cal_event:
                        result.append(cal_event)

                except Exception as e:
                    print(f"  ⚠ Error parsing event {event.get('id', 'unknown')}: {e}")
                    continue

            return result

        except HttpError as e:
            print(f"Google Calendar API error getting events: {e}")
            if e.resp.status == 401:
                # Token expired or invalid
                self.is_authenticated = False
                print(f"  Authentication expired for {self.config.get('display_name')}, re-auth required")
            return []
        except Exception as e:
            print(f"Error getting Google events: {e}")
            return []

    def _parse_google_event(self, event: Dict[str, Any], calendar_id: str) -> Optional[CalendarEvent]:
        """Parse a Google Calendar event into CalendarEvent format

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
                start_dt = datetime.fromisoformat(f"{start}T00:00:00")
                end_dt = datetime.fromisoformat(f"{end}T00:00:00")
                all_day = True

            # Extract attendees
            attendees = []
            if 'attendees' in event:
                attendees = [
                    att.get('email', att.get('displayName', 'Unknown'))
                    for att in event['attendees']
                ]

            # Get event color
            event_color = self.config.get('color', '#4285f4')
            if 'colorId' in event:
                # Google uses numeric color IDs, map to hex colors
                color_map = {
                    '1': '#a4bdfc', '2': '#7ae7bf', '3': '#dbadff', '4': '#ff887c',
                    '5': '#fbd75b', '6': '#ffb878', '7': '#46d6db', '8': '#e1e1e1',
                    '9': '#5484ed', '10': '#51b749', '11': '#dc2127'
                }
                event_color = color_map.get(event['colorId'], event_color)

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

        except Exception as e:
            print(f"  ⚠ Error parsing event: {e}")
            return None

    def get_source_type(self) -> str:
        """Get source type identifier

        Returns:
            String identifier for this source type
        """
        return "google"


class GoogleCalendarSetup:
    """Helper class for Google Calendar setup and OAuth2 configuration"""

    @staticmethod
    def print_setup_instructions():
        """Print detailed instructions for setting up Google Calendar API"""
        print("\n" + "=" * 70)
        print("GOOGLE CALENDAR API SETUP INSTRUCTIONS")
        print("=" * 70)
        print("\nTo use Google Calendar with Pi Calendar System, follow these steps:\n")
        print("1. CREATE GOOGLE CLOUD PROJECT")
        print("   • Go to: https://console.developers.google.com/")
        print("   • Click 'Select a project' → 'New Project'")
        print("   • Enter project name (e.g., 'Pi Calendar')")
        print("   • Click 'Create'\n")
        print("2. ENABLE GOOGLE CALENDAR API")
        print("   • In the project, go to 'APIs & Services' → 'Library'")
        print("   • Search for 'Google Calendar API'")
        print("   • Click on it and press 'Enable'\n")
        print("3. CREATE OAUTH 2.0 CREDENTIALS")
        print("   • Go to 'APIs & Services' → 'Credentials'")
        print("   • Click 'Create Credentials' → 'OAuth 2.0 Client ID'")
        print("   • If prompted, configure OAuth consent screen:")
        print("     - User Type: External")
        print("     - App name: Pi Calendar")
        print("     - User support email: your@email.com")
        print("     - Developer contact: your@email.com")
        print("     - Click 'Save and Continue' through remaining steps")
        print("   • Application type: 'Web application'")
        print("   • Name: 'Pi Calendar Client'")
        print("   • Authorized redirect URIs:")
        print("     - Add: http://localhost:8080/callback")
        print("   • Click 'Create'\n")
        print("4. DOWNLOAD CREDENTIALS")
        print("   • You'll see a popup with Client ID and Client Secret")
        print("   • Copy these values (you'll need them for setup)")
        print("   • Or download the JSON file for reference\n")
        print("5. ADD ACCOUNT IN PI CALENDAR")
        print("   • Open Pi Calendar web interface")
        print("   • Go to 'Account Setup' → 'Add Google Account'")
        print("   • Enter display name, Client ID, and Client Secret")
        print("   • Follow OAuth authorization flow\n")
        print("=" * 70)
        print("IMPORTANT NOTES:")
        print("• Keep Client Secret secure (it's like a password)")
        print("• You can create multiple OAuth clients for different devices")
        print("• If you see 'unverified app' warning during OAuth, click 'Advanced'")
        print("  and then 'Go to Pi Calendar (unsafe)' - this is safe for personal use")
        print("=" * 70 + "\n")

    @staticmethod
    def setup_google_account(display_name: str, client_id: str, client_secret: str) -> str:
        """Set up a new Google Calendar account

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
            print("⚠ Warning: Client ID doesn't match expected format")
        
        # Generate unique account ID
        account_id = f"google_{uuid.uuid4().hex[:8]}"

        # Add account configuration
        config.add_google_account(account_id, display_name)

        # Store OAuth credentials (client info only, not tokens yet)
        config.store_credentials(account_id, {
            'client_id': client_id,
            'client_secret': client_secret
        })

        print(f"\n✓ Google account '{display_name}' configured")
        print(f"  Account ID: {account_id}")
        print(f"  Status: Ready for authentication")
        print(f"\nNext step: Start sync to begin OAuth flow\n")

        return account_id

    @staticmethod
    def validate_credentials(client_id: str, client_secret: str) -> bool:
        """Validate OAuth2 credentials format

        Args:
            client_id: Google OAuth2 client ID
            client_secret: Google OAuth2 client secret

        Returns:
            True if credentials appear valid
        """
        # Check client ID format
        if not client_id.endswith('.apps.googleusercontent.com'):
            return False
        
        # Check client secret format (starts with GOCSPX-)
        if not client_secret.startswith('GOCSPX-'):
            print("⚠ Warning: Client Secret format may be incorrect")
        
        # Check lengths
        if len(client_id) < 50 or len(client_secret) < 20:
            return False
        
        return True
