# server/config/config_schema.py
"""
Configuration validation schema
Ensures loaded configuration meets requirements
"""

from typing import Dict, Any, List
import re


class ConfigValidationError(Exception):
    """Raised when configuration validation fails"""
    pass


class ConfigValidator:
    """Validates configuration against schema"""

    @staticmethod
    def validate_config(config: Dict[str, Any]) -> List[str]:
        """
        Validate configuration dictionary

        Args:
            config: Configuration to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Server validation
        if 'server' in config:
            errors.extend(ConfigValidator._validate_server(config['server']))

        # Sync validation
        if 'sync' in config:
            errors.extend(ConfigValidator._validate_sync(config['sync']))

        # Display validation
        if 'display' in config:
            errors.extend(ConfigValidator._validate_display(config['display']))

        # Accounts validation
        if 'accounts' in config:
            errors.extend(ConfigValidator._validate_accounts(config['accounts']))

        return errors

    @staticmethod
    def _validate_server(server: Dict[str, Any]) -> List[str]:
        """Validate server configuration"""
        errors = []

        if 'port' in server:
            port = server['port']
            if not isinstance(port, int) or port < 1 or port > 65535:
                errors.append(f"Invalid server port: {port} (must be 1-65535)")

        if 'host' in server:
            host = server['host']
            if not isinstance(host, str) or not host.strip():
                errors.append(f"Invalid server host: {host}")

        if 'debug' in server:
            if not isinstance(server['debug'], bool):
                errors.append(f"server.debug must be boolean, got {type(server['debug'])}")

        return errors

    @staticmethod
    def _validate_sync(sync: Dict[str, Any]) -> List[str]:
        """Validate sync configuration"""
        errors = []

        if 'interval_minutes' in sync:
            interval = sync['interval_minutes']
            if not isinstance(interval, (int, float)) or interval <= 0:
                errors.append(f"Invalid sync interval: {interval} (must be > 0)")
            if interval < 5:
                errors.append(f"Warning: sync interval {interval} is very frequent (< 5 minutes)")

        if 'max_events_per_calendar' in sync:
            max_events = sync['max_events_per_calendar']
            if not isinstance(max_events, int) or max_events < 1:
                errors.append(f"Invalid max_events_per_calendar: {max_events} (must be >= 1)")

        return errors

    @staticmethod
    def _validate_display(display: Dict[str, Any]) -> List[str]:
        """Validate display configuration"""
        errors = []

        if 'default_view' in display:
            view = display['default_view']
            if view not in ['day', 'week', 'month']:
                errors.append(f"Invalid default_view: {view} (must be 'day', 'week', or 'month')")

        return errors

    @staticmethod
    def _validate_accounts(accounts: Dict[str, Any]) -> List[str]:
        """Validate accounts configuration"""
        errors = []

        if 'google' in accounts:
            if not isinstance(accounts['google'], list):
                errors.append("accounts.google must be a list")
            else:
                for i, account in enumerate(accounts['google']):
                    errors.extend(ConfigValidator._validate_google_account(account, i))

        if 'apple' in accounts:
            if not isinstance(accounts['apple'], list):
                errors.append("accounts.apple must be a list")
            else:
                for i, account in enumerate(accounts['apple']):
                    errors.extend(ConfigValidator._validate_apple_account(account, i))

        return errors

    @staticmethod
    def _validate_google_account(account: Dict[str, Any], index: int) -> List[str]:
        """Validate Google account configuration"""
        errors = []
        prefix = f"accounts.google[{index}]"

        if 'id' not in account or not account['id']:
            errors.append(f"{prefix}.id is required")

        if 'display_name' not in account or not account['display_name']:
            errors.append(f"{prefix}.display_name is required")

        if 'type' in account and account['type'] != 'google':
            errors.append(f"{prefix}.type must be 'google'")

        return errors

    @staticmethod
    def _validate_apple_account(account: Dict[str, Any], index: int) -> List[str]:
        """Validate Apple account configuration"""
        errors = []
        prefix = f"accounts.apple[{index}]"

        if 'id' not in account or not account['id']:
            errors.append(f"{prefix}.id is required")

        if 'display_name' not in account or not account['display_name']:
            errors.append(f"{prefix}.display_name is required")

        if 'username' not in account or not account['username']:
            errors.append(f"{prefix}.username is required")
        elif not ConfigValidator._is_valid_email(account['username']):
            errors.append(f"{prefix}.username must be valid email")

        if 'type' in account and account['type'] != 'apple':
            errors.append(f"{prefix}.type must be 'apple'")

        return errors

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))