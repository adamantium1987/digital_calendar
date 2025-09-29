# client/config/settings.py
"""
Configuration management for Pi Calendar Client
Handles client settings, server connection, and display preferences
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class ClientConfigManager:
    """Manages client configuration and preferences"""

    def __init__(self, config_dir: str = None):
        """Initialize client configuration manager

        Args:
            config_dir: Directory to store config files (default: ~/.pi_calendar_client)
        """
        if config_dir is None:
            config_dir = os.path.expanduser("~/.pi_calendar_client")

        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)

        self.config_file = self.config_dir / "config.json"

        # Load or create default config
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create defaults"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default client configuration settings"""
        return {
            "server": {
                "host": "192.168.1.100",
                "port": 5001,
                "timeout": 10,
                "retry_attempts": 3,
                "retry_delay": 2
            },
            "display": {
                "fullscreen": True,
                "width": 800,
                "height": 480,
                "default_view": "week",
                "refresh_interval": 300,
                "background_color": "black"
            },
            "touch": {
                "swipe_threshold": 50,
                "long_press_duration": 0.8,
                "double_tap_window": 0.3,
                "tap_move_tolerance": 10,
                "edge_threshold": 60
            },
            "calendar": {
                "show_weekends": True,
                "start_hour": 6,
                "end_hour": 22,
                "time_format": "12h",
                "date_format": "%Y-%m-%d"
            }
        }

    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def get(self, key: str, default=None) -> Any:
        """Get configuration value by dot-notation key

        Args:
            key: Configuration key (e.g., 'server.host')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """Set configuration value by dot-notation key

        Args:
            key: Configuration key (e.g., 'server.host')
            value: Value to set
        """
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value
        self.save_config()

    def get_server_config(self) -> Dict[str, Any]:
        """Get server connection configuration

        Returns:
            Dictionary with server connection settings
        """
        return {
            'host': self.get('server.host', '192.168.1.100'),
            'port': self.get('server.port', 5001),
            'timeout': self.get('server.timeout', 10),
            'retry_attempts': self.get('server.retry_attempts', 3),
            'retry_delay': self.get('server.retry_delay', 2)
        }

    def get_display_config(self) -> Dict[str, Any]:
        """Get display configuration

        Returns:
            Dictionary with display settings
        """
        return {
            'fullscreen': self.get('display.fullscreen', True),
            'width': self.get('display.width', 800),
            'height': self.get('display.height', 480),
            'default_view': self.get('display.default_view', 'week'),
            'refresh_interval': self.get('display.refresh_interval', 300),
            'background_color': self.get('display.background_color', 'black')
        }

    def get_touch_config(self) -> Dict[str, Any]:
        """Get touch gesture configuration

        Returns:
            Dictionary with touch settings
        """
        return {
            'swipe_threshold': self.get('touch.swipe_threshold', 50),
            'long_press_duration': self.get('touch.long_press_duration', 0.8),
            'double_tap_window': self.get('touch.double_tap_window', 0.3),
            'tap_move_tolerance': self.get('touch.tap_move_tolerance', 10),
            'edge_threshold': self.get('touch.edge_threshold', 60)
        }

    def get_calendar_config(self) -> Dict[str, Any]:
        """Get calendar display configuration

        Returns:
            Dictionary with calendar settings
        """
        return {
            'show_weekends': self.get('calendar.show_weekends', True),
            'start_hour': self.get('calendar.start_hour', 6),
            'end_hour': self.get('calendar.end_hour', 22),
            'time_format': self.get('calendar.time_format', '12h'),
            'date_format': self.get('calendar.date_format', '%Y-%m-%d')
        }


# Global client config instance
client_config = ClientConfigManager()