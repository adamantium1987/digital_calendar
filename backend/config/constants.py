# server/config/constants.py
"""
Configuration constants and default values
Centralizes magic numbers and hard-coded values
All constants use standardized naming conventions
"""

# ===============================
# SERVER CONFIGURATION
# ===============================
DEFAULT_SERVER_HOST = "0.0.0.0"
DEFAULT_SERVER_PORT = 5000
DEFAULT_SERVER_DEBUG = False

# ===============================
# SYNC CONFIGURATION
# ===============================
DEFAULT_SYNC_INTERVAL_MINUTES = 15
DEFAULT_MAX_EVENTS_PER_CALENDAR = 1000
STARTUP_DELAY_SECONDS = 2  # Allow Flask to bind socket before initial sync
SYNC_DATE_RANGE_PAST_DAYS = 30
SYNC_DATE_RANGE_FUTURE_DAYS = 90

# ===============================
# AUTHENTICATION CONFIGURATION
# ===============================
APPLE_APP_PASSWORD_LENGTH = 16  # Standardized from APPLE_PASSWORD_LENGTH
SESSION_TOKEN_LENGTH = 32
API_KEY_LENGTH = 32
PASSWORD_SALT_LENGTH = 16

# ===============================
# CACHE CONFIGURATION
# ===============================
CACHE_EXPIRY_DAYS = 90  # Delete events older than this
CACHE_CLEANUP_INTERVAL_HOURS = 24
DB_CONNECTION_TIMEOUT = 30  # seconds
DB_MAX_RETRIES = 3

# ===============================
# API CONFIGURATION
# ===============================
API_VERSION = "v1"
API_RATE_LIMIT_PER_HOUR = 100  # Default rate limit for most endpoints
API_RATE_LIMIT_SYNC = 10  # Stricter limit for sync operations

# ===============================
# DISPLAY CONFIGURATION
# ===============================
DEFAULT_TIMEZONE = "UTC"
DEFAULT_DATE_FORMAT = "%Y-%m-%d"
DEFAULT_TIME_FORMAT = "%H:%M"
DEFAULT_VIEW = "week"
EVENT_REFRESH_INTERVAL_MINUTES = 5

# ===============================
# COLOR DEFAULTS
# ===============================
COLOR_GOOGLE = "#4285f4"
COLOR_APPLE = "#000000"
COLOR_DEFAULT = "#666666"

# Legacy aliases for backward compatibility (deprecated - use COLOR_* instead)
GOOGLE_CALENDAR_COLOR = COLOR_GOOGLE
APPLE_CALENDAR_COLOR = COLOR_APPLE
DEFAULT_EVENT_COLOR = COLOR_DEFAULT

# ===============================
# GOOGLE CALENDAR API
# ===============================
GOOGLE_CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
GOOGLE_COLOR_MAP = {
    '1': '#a4bdfc', '2': '#7ae7bf', '3': '#dbadff', '4': '#ff887c',
    '5': '#fbd75b', '6': '#ffb878', '7': '#46d6db', '8': '#e1e1e1',
    '9': '#5484ed', '10': '#51b749', '11': '#dc2127'
}

# ===============================
# APPLE CALDAV
# ===============================
APPLE_CALDAV_SERVER = "https://caldav.icloud.com"

# ===============================
# FILE PERMISSIONS
# ===============================
CONFIG_DIR_PERMISSIONS = 0o700
CONFIG_FILE_PERMISSIONS = 0o600
CREDENTIALS_FILE_PERMISSIONS = 0o600
KEY_FILE_PERMISSIONS = 0o600

# ===============================
# SCHEMA VERSION
# ===============================
CURRENT_SCHEMA_VERSION = 1

# ===============================
# LEGACY CONSTANT ALIASES
# ===============================
# These are kept for backward compatibility but should be migrated
DEFAULT_HOST = DEFAULT_SERVER_HOST
DEFAULT_PORT = DEFAULT_SERVER_PORT
DEFAULT_DEBUG = DEFAULT_SERVER_DEBUG