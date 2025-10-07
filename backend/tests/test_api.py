"""Tests for API endpoints"""
import pytest
from datetime import datetime


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check(self, client):
        """Test health check returns 200"""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = response.get_json()
        assert 'status' in data
        assert 'timestamp' in data


class TestEventsEndpoint:
    """Test events API endpoint"""

    def test_get_events_no_auth(self, client):
        """Test getting events without authentication"""
        response = client.get('/api/events')
        # Should return 200 even without auth (empty results)
        assert response.status_code in [200, 503]

    def test_get_events_with_date_range(self, client):
        """Test getting events with date range"""
        start_date = datetime.now().isoformat()
        response = client.get(f'/api/events?start_date={start_date}')
        assert response.status_code in [200, 503]


class TestAccountsEndpoint:
    """Test accounts API endpoint"""

    def test_get_accounts(self, client):
        """Test getting configured accounts"""
        response = client.get('/api/accounts')
        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = response.get_json()
            assert 'accounts' in data


class TestStatusEndpoint:
    """Test status API endpoint"""

    def test_get_status(self, client):
        """Test getting sync status"""
        response = client.get('/api/status')
        assert response.status_code in [200, 503]
