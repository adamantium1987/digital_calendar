# server/config/settings.py
"""
Configuration management for Pi Calendar Server
Handles all system settings, account credentials, and preferences
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet

from .constants import *
from .config_schema import ConfigValidator, ConfigValidationError

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages configuration and encrypted credential storage"""

    def __init__(self, config_dir: str = None):
        """
        Initialize configuration manager

        Args:
            config_dir: Directory to store config files (default: ~/.pi_calendar)
        """
        if config_dir is None:
            config_dir = os.path.expanduser("~/.pi_calendar")

        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True, mode=CONFIG_DIR_PERMISSIONS)

        self.config_file = self.config_dir / "config.json"
        self.credentials_file = self.config_dir / "credentials.enc"
        self.key_file = self.config_dir / ".key"

        # Ensure secure permissions
        self._ensure_secure_permissions()

        # Initialize encryption
        self._encryption_key = self._get_or_create_key()
        self._fernet = Fernet(self._encryption_key)

        # Load or create default config
        self.config = self._load_config()

        # Validate configuration
        self._validate_config()

        # Ensure secret key exists and is persisted
        self._ensure_secret_key()

    def _ensure_secure_permissions(self):
        """Ensure configuration directory has secure permissions"""
        try:
            if self.config_dir.exists():
                os.chmod(self.config_dir, CONFIG_DIR_PERMISSIONS)
                logger.debug(f"Set config directory permissions: {oct(CONFIG_DIR_PERMISSIONS)}")
        except OSError as e:
            logger.warning(f"Could not set directory permissions: {e}")

    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key for credentials"""
        if self.key_file.exists():
            key = self.key_file.read_bytes()
            logger.debug("Loaded existing encryption key")
            return key
        else:
            key = Fernet.generate_key()
            self.key_file.write_bytes(key)
            os.chmod(self.key_file, KEY_FILE_PERMISSIONS)
            logger.info("Generated new encryption key")
            return key

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create defaults"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_file}")
                return config
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in config file: {e}", exc_info=True)
                logger.warning("Using default configuration")
                return self._get_default_config()
            except OSError as e:
                logger.error(f"Error reading config file: {e}", exc_info=True)
                return self._get_default_config()
        else:
            logger.info("No config file found, creating default configuration")
            config = self._get_default_config()
            self.save_config()
            return config

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration settings"""
        return {
            "server": {
                "host": DEFAULT_HOST,
                "port": DEFAULT_PORT,
                "debug": DEFAULT_DEBUG,
                "secret_key": None  # Will be generated if needed
            },
            "sync": {
                "interval_minutes": DEFAULT_SYNC_INTERVAL_MINUTES,
                "max_events_per_calendar": DEFAULT_MAX_EVENTS_PER_CALENDAR
            },
            "display": {
                "timezone": DEFAULT_TIMEZONE,
                "date_format": DEFAULT_DATE_FORMAT,
                "time_format": DEFAULT_TIME_FORMAT,
                "default_view": DEFAULT_VIEW
            },
            "accounts": {
                "google": [],
                "apple": []
            },
            "logging": {
                "level": "INFO",
                "file_logging": True
            }
        }

    def _validate_config(self):
        """Validate configuration against schema"""
        try:
            errors = ConfigValidator.validate_config(self.config)
            if errors:
                logger.warning("Configuration validation warnings:")
                for error in errors:
                    logger.warning(f"  - {error}")
        except Exception as e:
            logger.error(f"Error validating configuration: {e}", exc_info=True)

    def _ensure_secret_key(self):
        """Ensure Flask secret key exists and is persisted"""
        secret_key = self.get('server.secret_key')
        if not secret_key:
            import secrets
            secret_key = secrets.token_hex(32)
            self.set('server.secret_key', secret_key)
            logger.info("Generated new Flask secret key")
        else:
            logger.debug("Using existing Flask secret key")

    def save_config(self):
        """Save configuration to file with proper permissions"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            os.chmod(self.config_file, CONFIG_FILE_PERMISSIONS)
            logger.debug(f"Saved configuration to {self.config_file}")
        except OSError as e:
            logger.error(f"Error saving configuration: {e}", exc_info=True)
            raise

    def get(self, key: str, default=None) -> Any:
        """
        Get configuration value by dot-notation key

        Args:
            key: Dot-separated key path (e.g., 'server.port')
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
        """
        Set configuration value by dot-notation key

        Args:
            key: Dot-separated key path
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
        logger.debug(f"Set config: {key} = {value}")

    def add_google_account(self, account_id: str, display_name: str):
        """
        Add a Google Calendar account

        Args:
            account_id: Unique account identifier
            display_name: Human-readable name
        """
        account = {
            'id': account_id,
            'display_name': display_name,
            'type': 'google',
            'enabled': True,
            'color': COLOR_GOOGLE
        }

        if 'accounts' not in self.config:
            self.config['accounts'] = {'google': [], 'apple': []}

        if 'google' not in self.config['accounts']:
            self.config['accounts']['google'] = []

        self.config['accounts']['google'].append(account)
        self.save_config()
        logger.info(f"Added Google account: {display_name} ({account_id})")

    def add_apple_account(self, account_id: str, display_name: str,
                          username: str, server_url: str = None):
        """
        Add an Apple iCloud Calendar account

        Args:
            account_id: Unique account identifier
            display_name: Human-readable name
            username: iCloud email address
            server_url: CalDAV server URL (default: iCloud)
        """
        if server_url is None:
            server_url = APPLE_CALDAV_SERVER

        account = {
            'id': account_id,
            'display_name': display_name,
            'username': username,
            'server_url': server_url,
            'type': 'apple',
            'enabled': True,
            'color': COLOR_APPLE
        }

        if 'accounts' not in self.config:
            self.config['accounts'] = {'google': [], 'apple': []}

        if 'apple' not in self.config['accounts']:
            self.config['accounts']['apple'] = []

        self.config['accounts']['apple'].append(account)
        self.save_config()
        logger.info(f"Added Apple account: {display_name} ({account_id})")

    def remove_account(self, account_type: str, account_id: str):
        """
        Remove an account

        Args:
            account_type: 'google' or 'apple'
            account_id: Account identifier to remove
        """
        if 'accounts' in self.config and account_type in self.config['accounts']:
            original_count = len(self.config['accounts'][account_type])
            self.config['accounts'][account_type] = [
                acc for acc in self.config['accounts'][account_type]
                if acc['id'] != account_id
            ]
            removed = original_count - len(self.config['accounts'][account_type])

            if removed > 0:
                self.save_config()
                logger.info(f"Removed {account_type} account: {account_id}")
            else:
                logger.warning(f"Account not found: {account_id}")

    def list_accounts(self) -> Dict[str, list]:
        """
        Get all configured accounts

        Returns:
            Dict with 'google' and 'apple' account lists
        """
        if 'accounts' not in self.config:
            return {'google': [], 'apple': []}

        return {
            'google': self.config['accounts'].get('google', []),
            'apple': self.config['accounts'].get('apple', [])
        }

    def store_credentials(self, account_id: str, credentials: Dict[str, Any]):
        """
        Store encrypted credentials for an account

        Args:
            account_id: Account identifier
            credentials: Credentials dictionary to encrypt and store
        """
        try:
            # Load existing credentials
            if self.credentials_file.exists():
                try:
                    with open(self.credentials_file, 'rb') as f:
                        all_creds = json.loads(self._fernet.decrypt(f.read()).decode())
                except Exception as e:
                    logger.warning(f"Could not load existing credentials: {e}")
                    all_creds = {}
            else:
                all_creds = {}

            # Update with new credentials
            all_creds[account_id] = credentials

            # Save all credentials encrypted
            encrypted_all = self._fernet.encrypt(json.dumps(all_creds).encode())
            with open(self.credentials_file, 'wb') as f:
                f.write(encrypted_all)

            os.chmod(self.credentials_file, CREDENTIALS_FILE_PERMISSIONS)
            logger.debug(f"Stored credentials for account: {account_id}")

        except Exception as e:
            logger.error(f"Error storing credentials for {account_id}: {e}", exc_info=True)
            raise

    def get_credentials(self, account_id: str) -> Optional[Dict[str, Any]]:
        """
        Get decrypted credentials for an account

        Args:
            account_id: Account identifier

        Returns:
            Credentials dictionary or None if not found
        """
        if not self.credentials_file.exists():
            logger.debug(f"No credentials file exists")
            return None

        try:
            with open(self.credentials_file, 'rb') as f:
                all_creds = json.loads(self._fernet.decrypt(f.read()).decode())

            creds = all_creds.get(account_id)
            if creds:
                logger.debug(f"Retrieved credentials for account: {account_id}")
            else:
                logger.debug(f"No credentials found for account: {account_id}")

            return creds

        except Exception as e:
            logger.error(f"Error loading credentials for {account_id}: {e}", exc_info=True)
            return None


# Global config instance
config = ConfigManager()