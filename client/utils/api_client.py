# client/utils/api_client.py
"""
API client for communicating with Pi 4 calendar server - FIXED VERSION
Handles all HTTP requests and error handling
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional


class APIClient:
    """HTTP API client for Pi 4 calendar server"""

    def __init__(self, host: str, port: int, timeout: int = 10):
        """Initialize API client

        Args:
            host: Server IP address
            port: Server port
            timeout: Request timeout in seconds
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}/api"

        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PiZero-Calendar-Client/1.0',
            'Accept': 'application/json',
            'Connection': 'keep-alive'
        })

        # Connection status
        self.last_successful_request = None
        self.consecutive_failures = 0

        # Request retry settings
        self.max_retries = 3
        self.retry_delay = 1  # seconds

    def _make_request(self, method: str, endpoint: str, params: Dict = None,
                      data: Dict = None, retries: int = None) -> Optional[Dict[str, Any]]:
        """Make HTTP request with error handling and retries

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without /api prefix)
            params: Query parameters
            data: Request body data
            retries: Number of retries (defaults to max_retries)

        Returns:
            Response data as dict, or None on error
        """
        if retries is None:
            retries = self.max_retries

        url = f"{self.base_url}{endpoint}"

        for attempt in range(retries + 1):
            try:
                # Prepare request arguments
                request_kwargs = {
                    'timeout': self.timeout,
                    'params': params or {}
                }

                # Make request based on method
                if method.upper() == 'GET':
                    response = self.session.get(url, **request_kwargs)
                elif method.upper() == 'POST':
                    request_kwargs['json'] = data
                    response = self.session.post(url, **request_kwargs)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                # Check response status
                response.raise_for_status()

                # Parse JSON response
                try:
                    result = response.json()
                except json.JSONDecodeError as e:
                    print(f"JSON decode error for {url}: {e}")
                    if attempt < retries:
                        time.sleep(self.retry_delay)
                        continue
                    return None

                # Update success tracking
                self.last_successful_request = datetime.now()
                self.consecutive_failures = 0

                return result

            except requests.exceptions.ConnectionError as e:
                error_msg = f"Connection error (attempt {attempt + 1}/{retries + 1}): Cannot connect to {self.host}:{self.port}"
                if attempt < retries:
                    print(f"{error_msg}, retrying in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                    continue
                else:
                    print(f"{error_msg}, giving up")
                    self.consecutive_failures += 1
                    return None

            except requests.exceptions.Timeout as e:
                error_msg = f"Request timeout (attempt {attempt + 1}/{retries + 1}): {url}"
                if attempt < retries:
                    print(f"{error_msg}, retrying in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                    continue
                else:
                    print(f"{error_msg}, giving up")
                    self.consecutive_failures += 1
                    return None

            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response else 'unknown'
                error_msg = f"HTTP error {status_code}: {url}"

                # Don't retry on client errors (4xx)
                if e.response and 400 <= e.response.status_code < 500:
                    print(error_msg)
                    self.consecutive_failures += 1
                    return None

                # Retry on server errors (5xx)
                if attempt < retries:
                    print(f"{error_msg}, retrying in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                    continue
                else:
                    print(f"{error_msg}, giving up")
                    self.consecutive_failures += 1
                    return None

            except Exception as e:
                error_msg = f"Unexpected error (attempt {attempt + 1}/{retries + 1}): {e}"
                if attempt < retries:
                    print(f"{error_msg}, retrying in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                    continue
                else:
                    print(f"{error_msg}, giving up")
                    self.consecutive_failures += 1
                    return None

        return None

    def health_check(self) -> bool:
        """Check if server is responding

        Returns:
            True if server is healthy
        """
        try:
            result = self._make_request('GET', '/health', retries=1)
            return result is not None and result.get('status') == 'healthy'
        except Exception as e:
            print(f"Health check error: {e}")
            return False

    def get_events(self, start_date: datetime = None, end_date: datetime = None,
                   view: str = 'week', accounts: List[str] = None,
                   calendars: List[str] = None) -> Optional[Dict[str, Any]]:
        """Get calendar events from server

        Args:
            start_date: Start of date range
            end_date: End of date range
            view: View type (day, week, month)
            accounts: Filter by account IDs
            calendars: Filter by calendar IDs

        Returns:
            Events data or None on error
        """
        try:
            params = {'view': view}

            if start_date:
                params['start_date'] = start_date.isoformat()
            if end_date:
                params['end_date'] = end_date.isoformat()
            if accounts:
                params['accounts'] = ','.join(accounts)
            if calendars:
                params['calendars'] = ','.join(calendars)

            return self._make_request('GET', '/events', params=params)
        except Exception as e:
            print(f"Error in get_events: {e}")
            return None

    def get_today_events(self) -> Optional[Dict[str, Any]]:
        """Get today's events (convenience method)"""
        try:
            return self._make_request('GET', '/events/today')
        except Exception as e:
            print(f"Error in get_today_events: {e}")
            return None

    def get_week_events(self) -> Optional[Dict[str, Any]]:
        """Get this week's events (convenience method)"""
        try:
            return self._make_request('GET', '/events/week')
        except Exception as e:
            print(f"Error in get_week_events: {e}")
            return None

    def get_calendars(self, account_id: str = None) -> Optional[Dict[str, Any]]:
        """Get calendar list from server

        Args:
            account_id: Specific account ID (optional)

        Returns:
            Calendars data or None on error
        """
        try:
            params = {}
            if account_id:
                params['account_id'] = account_id

            return self._make_request('GET', '/calendars', params=params)
        except Exception as e:
            print(f"Error in get_calendars: {e}")
            return None

    def get_status(self) -> Optional[Dict[str, Any]]:
        """Get server sync status

        Returns:
            Status data or None on error
        """
        try:
            return self._make_request('GET', '/status')
        except Exception as e:
            print(f"Error in get_status: {e}")
            return None

    def get_config(self) -> Optional[Dict[str, Any]]:
        """Get display configuration from server

        Returns:
            Configuration data or None on error
        """
        try:
            return self._make_request('GET', '/config')
        except Exception as e:
            print(f"Error in get_config: {e}")
            return None

    def get_accounts(self) -> Optional[Dict[str, Any]]:
        """Get account information from server

        Returns:
            Accounts data or None on error
        """
        try:
            return self._make_request('GET', '/accounts')
        except Exception as e:
            print(f"Error in get_accounts: {e}")
            return None

    def get_server_time(self) -> Optional[Dict[str, Any]]:
        """Get current server time

        Returns:
            Time data or None on error
        """
        try:
            return self._make_request('GET', '/time')
        except Exception as e:
            print(f"Error in get_server_time: {e}")
            return None

    def trigger_sync(self) -> Optional[Dict[str, Any]]:
        """Trigger immediate synchronization on server

        Returns:
            Sync response or None on error
        """
        try:
            return self._make_request('POST', '/sync')
        except Exception as e:
            print(f"Error in trigger_sync: {e}")
            return None

    def is_connected(self) -> bool:
        """Check if client is currently connected to server

        Returns:
            True if connected (based on recent successful requests)
        """
        if not self.last_successful_request:
            return False

        # Consider connected if last request was within 10 minutes
        time_since_success = datetime.now() - self.last_successful_request
        return time_since_success.total_seconds() < 600  # 10 minutes

    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection status information

        Returns:
            Dict with connection details
        """
        return {
            'server_url': self.base_url,
            'connected': self.is_connected(),
            'last_successful_request': self.last_successful_request.isoformat() if self.last_successful_request else None,
            'consecutive_failures': self.consecutive_failures,
            'timeout': self.timeout
        }

    def test_connection(self, verbose: bool = True) -> Dict[str, Any]:
        """Test connection to server and return detailed results

        Args:
            verbose: Print test progress

        Returns:
            Dict with test results
        """
        if verbose:
            print(f"Testing connection to {self.host}:{self.port}...")

        results = {
            'overall_status': 'unknown',
            'tests': {},
            'server_info': {},
            'sync_status': False
        }

        # Test health endpoint
        start_time = time.time()
        health_ok = self.health_check()
        health_time = time.time() - start_time

        results['tests']['health'] = {
            'ok': health_ok,
            'response_time': round(health_time, 3)
        }

        if verbose:
            status = "✓" if health_ok else "✗"
            print(f"  {status} Health check: {health_time:.3f}s")

        if not health_ok:
            results['overall_status'] = 'disconnected'
            return results

        # Test status endpoint
        start_time = time.time()
        status_result = self.get_status()
        status_ok = status_result is not None
        status_time = time.time() - start_time

        results['tests']['status'] = {
            'ok': status_ok,
            'response_time': round(status_time, 3)
        }

        if verbose:
            status = "✓" if status_ok else "✗"
            print(f"  {status} Status endpoint: {status_time:.3f}s")

        if status_result:
            results['server_info'] = status_result.get('server_info', {})
            results['sync_status'] = status_result.get('currently_syncing', False)

        # Test events endpoint
        start_time = time.time()
        events_result = self.get_today_events()
        events_ok = events_result is not None
        events_time = time.time() - start_time

        results['tests']['events'] = {
            'ok': events_ok,
            'response_time': round(events_time, 3),
            'event_count': len(events_result.get('events', [])) if events_result else 0
        }

        if verbose:
            status = "✓" if events_ok else "✗"
            print(f"  {status} Events endpoint: {events_time:.3f}s")

        # Overall status
        if all([health_ok, status_ok, events_ok]):
            results['overall_status'] = 'connected'
            if verbose:
                print("✓ All tests passed - connection successful")
        else:
            results['overall_status'] = 'error'
            if verbose:
                print("✗ Some tests failed - connection issues detected")

        return results

    def wait_for_server(self, timeout: int = 60, retry_interval: int = 5,
                        verbose: bool = True) -> bool:
        """Wait for server to become available

        Args:
            timeout: Maximum time to wait in seconds
            retry_interval: Time between retries in seconds
            verbose: Print waiting progress

        Returns:
            True if server became available
        """
        if verbose:
            print(f"Waiting for server at {self.host}:{self.port}...")

        start_time = time.time()
        attempt = 1

        while time.time() - start_time < timeout:
            if verbose:
                print(f"  Attempt {attempt}: ", end='', flush=True)

            if self.health_check():
                if verbose:
                    print("✓ Server is available")
                return True
            else:
                if verbose:
                    print("✗ Server not responding")

            attempt += 1

            # Don't sleep on the last iteration
            if time.time() - start_time + retry_interval < timeout:
                time.sleep(retry_interval)

        if verbose:
            print(f"✗ Server did not respond within {timeout} seconds")
        return False

    def close(self):
        """Close the API client and clean up resources"""
        try:
            if self.session:
                self.session.close()
        except Exception as e:
            print(f"Error closing session: {e}")


# Utility functions for common operations
def create_client_from_config(config: Dict[str, Any]) -> APIClient:
    """Create API client from configuration dict

    Args:
        config: Configuration dictionary

    Returns:
        Configured APIClient instance
    """
    return APIClient(
        host=config.get('server_host', 'localhost'),
        port=config.get('server_port', 5000),
        timeout=config.get('connection_timeout', 10)
    )


def test_server_connection(host: str, port: int, verbose: bool = True) -> bool:
    """Test if server is reachable

    Args:
        host: Server IP address
        port: Server port
        verbose: Print test progress

    Returns:
        True if server is reachable
    """
    client = APIClient(host, port)
    try:
        result = client.test_connection(verbose=verbose)
        return result['overall_status'] == 'connected'
    finally:
        client.close()
