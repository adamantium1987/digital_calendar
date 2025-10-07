"""
Pydantic schemas for API request/response validation

This module defines data validation models using Pydantic for all API endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator, EmailStr
from enum import Enum


# Enums
class ViewType(str, Enum):
    """Calendar view types"""
    day = "day"
    week = "week"
    month = "month"


class AccountType(str, Enum):
    """Account provider types"""
    google = "google"
    apple = "apple"


class SyncStatus(str, Enum):
    """Sync status values"""
    pending = "pending"
    syncing = "syncing"
    completed = "completed"
    failed = "failed"


# Request Schemas
class EventQueryParams(BaseModel):
    """Query parameters for event listing"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    view: ViewType = ViewType.month
    accounts: Optional[str] = None
    calendars: Optional[str] = None

    @validator('accounts', 'calendars')
    def split_comma_list(cls, v: Optional[str]) -> Optional[List[str]]:
        """Split comma-separated string into list"""
        if v:
            return [item.strip() for item in v.split(',') if item.strip()]
        return None


class GoogleAccountCreate(BaseModel):
    """Schema for creating a Google account"""
    display_name: str = Field(..., min_length=1, max_length=100)
    client_id: str = Field(..., min_length=10)
    client_secret: str = Field(..., min_length=10)

    @validator('client_id')
    def validate_client_id(cls, v: str) -> str:
        """Validate Google client ID format"""
        if not v.endswith('.apps.googleusercontent.com'):
            raise ValueError('Invalid Google client ID format')
        return v


class AppleAccountCreate(BaseModel):
    """Schema for creating an Apple account"""
    display_name: str = Field(..., min_length=1, max_length=100)
    username: EmailStr
    app_password: Optional[str] = Field(None, min_length=16, max_length=16)

    @validator('app_password')
    def validate_app_password(cls, v: Optional[str]) -> Optional[str]:
        """Validate Apple app-specific password format"""
        if v:
            # Remove spaces and dashes
            cleaned = v.replace(' ', '').replace('-', '')
            if len(cleaned) != 16 or not cleaned.isalnum():
                raise ValueError('Invalid app password format (must be 16 alphanumeric characters)')
            return cleaned
        return v


class TaskComplete(BaseModel):
    """Schema for marking task complete"""
    completed: bool = True


class TaskCreate(BaseModel):
    """Schema for creating a task"""
    name: str = Field(..., min_length=1, max_length=100)
    task: str = Field(..., min_length=1, max_length=200)
    days: List[str] = Field(..., min_items=1)

    @validator('days')
    def validate_days(cls, v: List[str]) -> List[str]:
        """Validate day names"""
        valid_days = {'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'}
        normalized = [day.lower() for day in v]
        if not all(day in valid_days for day in normalized):
            raise ValueError(f'Invalid day name. Must be one of: {", ".join(valid_days)}')
        return normalized


# Response Schemas
class CalendarEventResponse(BaseModel):
    """Calendar event response model"""
    id: str
    title: str
    description: Optional[str] = ""
    start_time: datetime
    end_time: datetime
    all_day: bool
    location: Optional[str] = ""
    calendar_id: str
    account_id: str
    color: str
    attendees: List[str] = []

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CalendarResponse(BaseModel):
    """Calendar information response"""
    id: str
    name: str
    description: Optional[str] = ""
    color: str
    primary: bool = False
    access_role: str = "reader"
    selected: bool = True
    timezone: str = "UTC"


class AccountResponse(BaseModel):
    """Account information response"""
    id: str
    display_name: str
    type: AccountType
    enabled: bool = True
    authenticated: bool = False
    sync_status: str = "not_configured"
    username: Optional[str] = None


class SyncStatusResponse(BaseModel):
    """Sync status response"""
    last_full_sync: Optional[datetime] = None
    currently_syncing: bool = False
    total_events: int = 0
    total_calendars: int = 0
    errors: List[Dict[str, Any]] = []
    cache_stats: Optional[Dict[str, Any]] = None
    server_info: Optional[Dict[str, Any]] = None
    sources: Dict[str, Any] = {}

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    checks: Dict[str, Any] = {}

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TaskResponse(BaseModel):
    """Task response model"""
    id: str
    name: str
    type: Optional[str] = None
    task: str
    days: List[str]
    completed: Dict[str, bool] = {}
    week_start: str


class ApiErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    path: Optional[str] = None


class SuccessResponse(BaseModel):
    """Standard success response"""
    status: str = "success"
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Metadata Models
class PaginationMeta(BaseModel):
    """Pagination metadata"""
    page: int = 1
    per_page: int = 50
    total: int = 0
    pages: int = 0


class EventsListResponse(BaseModel):
    """Events list with metadata"""
    events: List[CalendarEventResponse]
    metadata: Dict[str, Any]


class AccountsListResponse(BaseModel):
    """Accounts list with metadata"""
    accounts: Dict[str, List[AccountResponse]]
    metadata: Dict[str, Any]
