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
