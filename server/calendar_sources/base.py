# server/calendar_sources/base.py
"""
Base calendar source interface
Defines abstract base class and event model for all calendar integrations
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class CalendarEvent:
    """Standard calendar event representation
    
    This dataclass provides a unified event model across
    different calendar providers (Google, Apple, etc.)
    """
    id: str
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    all_day: bool
    location: str
    calendar_id: str
    account_id: str
    color: str = None
    attendees: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Initialize default values after instantiation"""
        if self.attendees is None:
            self.attendees = []
        if self.color is None:
            self.color = '#4285f4'  # Default blue color


class BaseCalendarSource(ABC):
    """Abstract base class for all calendar sources
    
    All calendar integrations (Google, Apple, etc.) must inherit
    from this class and implement the required methods.
    """

    def __init__(self, account_id: str, config: Dict[str, Any]):
        """Initialize calendar source
        
        Args:
            account_id: Unique identifier for this account
            config: Configuration dictionary for this account
        """
        self.account_id = account_id
        self.config = config
        self.is_authenticated = False

    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the calendar service
        
        Returns:
            True if authentication successful, False otherwise
        """
        pass

    @abstractmethod
    async def get_calendars(self) -> List[Dict[str, Any]]:
        """Get list of available calendars from this source
        
        Returns:
            List of calendar info dictionaries with keys:
                - id: Calendar identifier
                - name: Calendar display name
                - description: Calendar description
                - color: Calendar color code
                - primary: Whether this is the primary calendar
        """
        pass

    @abstractmethod
    async def get_events(self, calendar_id: str, start_date: datetime,
                         end_date: datetime) -> List[CalendarEvent]:
        """Get events from a specific calendar
        
        Args:
            calendar_id: Calendar identifier
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            List of CalendarEvent objects
        """
        pass

    @abstractmethod
    def get_source_type(self) -> str:
        """Get the source type identifier
        
        Returns:
            Source type string (e.g., 'google', 'apple')
        """
        pass
