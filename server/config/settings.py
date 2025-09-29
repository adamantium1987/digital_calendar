# server/config/settings.py
"""
Configuration management for Pi Calendar Server
Handles all system settings, account credentials, and preferences
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet


class ConfigManager:
    """Manages configuration and encrypted credential storage"""
    
    def __init__(self, config_dir: str = None):
        """Initialize configuration manager
        
        Args:
            config_dir: Directory to store config files (default: ~/.pi_calendar)
        """
        if config_dir is None:
            config_dir = os.path.expanduser("~/.pi_calendar")
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.config_file = self.config_dir / "config.json"
        self.credentials_file = self.config_dir / "credentials.enc"
        self.key_file = self.config_dir / ".key"
        
        # Initialize encryption
        self._encryption_key = self._get_or_create_key()
        self._fernet = Fernet(self._encryption_key)
        
        # Load or create default config
        self.config = self._load_config()
    
    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key for credentials"""
        if self.key_file.exists():
            return self.key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            self.key_file.write_bytes(key)
            os.chmod(self.key_file, 0o600)
            return key
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create defaults"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration settings"""
        return {
            "server": {
                "host": "0.0.0.0",
                "port": 5000,
                "debug": False
            },
            "sync": {
                "interval_minutes": 15,
                "max_events_per_calendar": 1000
            },
            "display": {
                "timezone": "UTC",
                "date_format": "%Y-%m-%d",
                "time_format": "%H:%M",
                "default_view": "week"
            },
            "accounts": {
                "google": [],
                "apple": []
            }
        }
    
    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get(self, key: str, default=None) -> Any:
        """Get configuration value by dot-notation key"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value by dot-notation key"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.save_config()
    
    def add_google_account(self, account_id: str, display_name: str):
        """Add a Google Calendar account"""
        account = {
            'id': account_id,
            'display_name': display_name,
            'type': 'google',
            'enabled': True,
            'color': '#4285f4'
        }
        
        if 'accounts' not in self.config:
            self.config['accounts'] = {'google': [], 'apple': []}
        
        if 'google' not in self.config['accounts']:
            self.config['accounts']['google'] = []
        
        self.config['accounts']['google'].append(account)
        self.save_config()

    def add_apple_account(self, account_id: str, display_name: str, username: str, server_url: str = None):
        """Add an Apple iCloud Calendar account"""
        if server_url is None:
            server_url = "https://caldav.icloud.com"

        account = {
            'id': account_id,
            'display_name': display_name,
            'username': username,
            'server_url': server_url,  # Add this line
            'type': 'apple',
            'enabled': True,
            'color': '#000000'
        }

        if 'accounts' not in self.config:
            self.config['accounts'] = {'google': [], 'apple': []}

        if 'apple' not in self.config['accounts']:
            self.config['accounts']['apple'] = []

        self.config['accounts']['apple'].append(account)
        self.save_config()
    
    def remove_account(self, account_type: str, account_id: str):
        """Remove an account"""
        if 'accounts' in self.config and account_type in self.config['accounts']:
            self.config['accounts'][account_type] = [
                acc for acc in self.config['accounts'][account_type]
                if acc['id'] != account_id
            ]
            self.save_config()
    
    def list_accounts(self) -> Dict[str, list]:
        """Get all configured accounts"""
        if 'accounts' not in self.config:
            return {'google': [], 'apple': []}
        
        return {
            'google': self.config['accounts'].get('google', []),
            'apple': self.config['accounts'].get('apple', [])
        }
    
    def store_credentials(self, account_id: str, credentials: Dict[str, Any]):
        """Store encrypted credentials for an account"""
        # Encrypt credentials
        creds_json = json.dumps(credentials)
        encrypted = self._fernet.encrypt(creds_json.encode())
        
        # Load existing credentials
        if self.credentials_file.exists():
            with open(self.credentials_file, 'rb') as f:
                try:
                    all_creds = json.loads(self._fernet.decrypt(f.read()).decode())
                except:
                    all_creds = {}
        else:
            all_creds = {}
        
        all_creds[account_id] = credentials
        
        # Save all credentials encrypted
        encrypted_all = self._fernet.encrypt(json.dumps(all_creds).encode())
        with open(self.credentials_file, 'wb') as f:
            f.write(encrypted_all)
        
        os.chmod(self.credentials_file, 0o600)
    
    def get_credentials(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get decrypted credentials for an account"""
        if not self.credentials_file.exists():
            return None
        
        try:
            with open(self.credentials_file, 'rb') as f:
                all_creds = json.loads(self._fernet.decrypt(f.read()).decode())
            
            return all_creds.get(account_id)
        except Exception as e:
            print(f"Error loading credentials: {e}")
            return None


# Global config instance
config = ConfigManager()
