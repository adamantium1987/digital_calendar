# server/calendar_sources/__init__.py
"""
Calendar source integrations package

Note: Google and Apple integrations require external dependencies.
Import them explicitly when needed:
    from server.calendar_sources.google_cal import GoogleCalendarSource
    from server.calendar_sources.apple_cal import AppleCalendarSource
"""

from .base import BaseCalendarSource, CalendarEvent

__all__ = [
    'BaseCalendarSource',
    'CalendarEvent'
]
