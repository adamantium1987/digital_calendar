# client/__init__.py
"""
Pi Calendar Client Package

Display client for Pi Zero touchscreen devices.
"""

__version__ = '1.0.0'
__author__ = 'Pi Calendar Project'

from .display_app import CalendarDisplayApp

__all__ = ['CalendarDisplayApp']
