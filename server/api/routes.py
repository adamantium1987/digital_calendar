# server/api/routes.py
"""
REST API endpoints for Pi Zero display clients
Provides clean JSON APIs for calendar data retrieval
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from typing import List, Dict, Any

from ..sync.sync_engine import sync_engine
from ..config.settings import config

# Create API blueprint
api_bp = Blueprint('api', __name__)


# ===============================
# CALENDAR DATA ENDPOINTS
# ===============================

@api_bp.route('/events')
def get_events():
    """Get calendar events with optional filtering

    Query Parameters:
        start_date: ISO format date (default: today)
        end_date: ISO format date (default: 7 days from start)
        accounts: Comma-separated account IDs
        calendars: Comma-separated calendar IDs
        view: 'day', 'week', 'month' (affects default date range)

    Returns:
        JSON object with events list and metadata
    """
    try:
        # Parse query parameters
        view = request.args.get('view', 'week')
        accounts = request.args.get('accounts', '').split(',') if request.args.get('accounts') else None
        calendars = request.args.get('calendars', '').split(',') if request.args.get('calendars') else None

        # Parse dates or use defaults based on view
        start_date = None
        end_date = None

        if request.args.get('start_date'):
            start_date = datetime.fromisoformat(request.args.get('start_date'))
        if request.args.get('end_date'):
            end_date = datetime.fromisoformat(request.args.get('end_date'))

        # Set default date ranges based on view
        if not start_date:
            from datetime import timezone
            start_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        if not end_date:
            if view == 'day':
                end_date = start_date + timedelta(days=1)
            elif view == 'week':
                end_date = start_date + timedelta(days=7)
            elif view == 'month':
                end_date = start_date + timedelta(days=30)
            else:
                end_date = start_date + timedelta(days=7)  # Default to week

        # Get events from sync engine
        events = sync_engine.get_events(
            start_date=start_date,
            end_date=end_date,
            account_ids=accounts,
            calendar_ids=calendars
        )

        # Convert events to JSON-serializable format
        events_data = []
        for event in events:
            event_data = {
                'id': event.id,
                'title': event.title,
                'description': event.description,
                'start_time': event.start_time.isoformat(),
                'end_time': event.end_time.isoformat(),
                'all_day': event.all_day,
                'location': event.location,
                'calendar_id': event.calendar_id,
                'account_id': event.account_id,
                'color': event.color,
                'attendees': event.attendees
            }
            events_data.append(event_data)

        # Get account display names for context
        account_info = {}
        all_accounts = config.list_accounts()
        for acc_type in ['google', 'apple']:
            for acc in all_accounts[acc_type]:
                account_info[acc['id']] = {
                    'display_name': acc['display_name'],
                    'type': acc_type,
                    'color': acc.get('color', '#4285f4')
                }

        return jsonify({
            'events': events_data,
            'metadata': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'view': view,
                'total_events': len(events_data),
                'account_info': account_info
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/events/today')
def get_today_events():
    """Get today's events (convenience endpoint)"""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)

    return get_events_internal(today, tomorrow)


@api_bp.route('/events/week')
def get_week_events():
    """Get this week's events (convenience endpoint)"""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = today + timedelta(days=7)

    return get_events_internal(today, week_end)


def get_events_internal(start_date: datetime, end_date: datetime):
    """Internal helper for getting events"""
    try:
        events = sync_engine.get_events(start_date=start_date, end_date=end_date)

        events_data = []
        for event in events:
            events_data.append({
                'id': event.id,
                'title': event.title,
                'description': event.description,
                'start_time': event.start_time.isoformat(),
                'end_time': event.end_time.isoformat(),
                'all_day': event.all_day,
                'location': event.location,
                'calendar_id': event.calendar_id,
                'account_id': event.account_id,
                'color': event.color,
                'attendees': event.attendees
            })

        return jsonify({
            'events': events_data,
            'metadata': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'total_events': len(events_data)
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/calendars')
def get_calendars():
    """Get list of all calendars with account information

    Query Parameters:
        account_id: Specific account ID (optional)

    Returns:
        JSON object with calendars grouped by account
    """
    try:
        account_id = request.args.get('account_id')

        # Get calendars from cache
        calendars_data = sync_engine.get_calendars(account_id)

        # Get account display names
        all_accounts = config.list_accounts()
        account_info = {}
        for acc_type in ['google', 'apple']:
            for acc in all_accounts[acc_type]:
                account_info[acc['id']] = {
                    'display_name': acc['display_name'],
                    'type': acc_type,
                    'color': acc.get('color', '#4285f4'),
                    'enabled': acc.get('enabled', True)
                }

        # Enhance calendar data with account info
        result = {}
        for acc_id, calendars in calendars_data.items():
            result[acc_id] = {
                'account_info': account_info.get(acc_id, {
                    'display_name': acc_id,
                    'type': 'unknown',
                    'color': '#666666',
                    'enabled': True
                }),
                'calendars': calendars
            }

        return jsonify({
            'calendars': result,
            'metadata': {
                'total_accounts': len(result),
                'total_calendars': sum(len(acc['calendars']) for acc in result.values())
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ===============================
# STATUS AND HEALTH ENDPOINTS
# ===============================

@api_bp.route('/status')
def get_status():
    """Get sync engine status and health information"""
    try:
        status = sync_engine.get_sync_status()

        # Add cache statistics
        cache_stats = sync_engine.cache_manager.get_cache_stats()
        status['cache_stats'] = cache_stats

        # Add server info
        status['server_info'] = {
            'running': sync_engine.is_running,
            'version': '1.0.0',
            'api_version': 'v1'
        }

        return jsonify(status)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/health')
def health_check():
    """Simple health check endpoint for Pi Zero clients"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'sync_engine_running': sync_engine.is_running
    })


@api_bp.route('/sync', methods=['POST'])
def trigger_sync():
    """Trigger immediate synchronization"""
    try:
        if sync_engine.force_sync():
            return jsonify({
                'status': 'success',
                'message': 'Sync started',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Sync already in progress'
            }), 409

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ===============================
# CONFIGURATION ENDPOINTS
# ===============================

@api_bp.route('/config')
def get_config():
    """Get display configuration for Pi Zero clients"""
    try:
        display_config = {
            'timezone': config.get('display.timezone', 'UTC'),
            'date_format': config.get('display.date_format', '%Y-%m-%d'),
            'time_format': config.get('display.time_format', '%H:%M'),
            'default_view': config.get('display.default_view', 'week'),
            'sync_interval': config.get('sync.interval_minutes', 15),
            'colors': {
                'google': '#4285f4',
                'apple': '#000000',
                'default': '#666666'
            }
        }

        return jsonify({
            'config': display_config,
            'accounts': config.list_accounts()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ===============================
# UTILITY ENDPOINTS
# ===============================

@api_bp.route('/time')
def get_server_time():
    """Get current server time (useful for Pi Zero clock sync)"""
    now = datetime.now()

    return jsonify({
        'timestamp': now.isoformat(),
        'unix_timestamp': int(now.timestamp()),
        'timezone': str(now.astimezone().tzinfo),
        'formatted': {
            'date': now.strftime('%Y-%m-%d'),
            'time': now.strftime('%H:%M:%S'),
            'display': now.strftime('%A, %B %d, %Y at %I:%M %p')
        }
    })


@api_bp.route('/accounts')
def get_accounts():
    """Get list of configured accounts"""
    try:
        accounts = config.list_accounts()

        # Add status information
        sync_status = sync_engine.get_sync_status()
        sources = sync_status.get('sources', {})

        result = {}
        for acc_type in ['google', 'apple']:
            result[acc_type] = []
            for acc in accounts[acc_type]:
                acc_info = acc.copy()
                acc_id = acc['id']

                # Add sync status
                if acc_id in sources:
                    acc_info['authenticated'] = sources[acc_id].get('authenticated', False)
                    acc_info['sync_status'] = 'authenticated' if sources[acc_id].get(
                        'authenticated') else 'not_authenticated'
                else:
                    acc_info['authenticated'] = False
                    acc_info['sync_status'] = 'not_configured'

                result[acc_type].append(acc_info)

        return jsonify({
            'accounts': result,
            'metadata': {
                'total_google': len(result['google']),
                'total_apple': len(result['apple']),
                'total_all': len(result['google']) + len(result['apple'])
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ===============================
# WEBSOCKET SUPPORT (Future)
# ===============================

# Note: WebSocket support could be added here for real-time updates
# This would allow Pi Zero displays to receive instant updates when
# calendar data changes, rather than polling every few minutes.

# from flask_socketio import SocketIO, emit
#
# @api_bp.route('/ws')
# def websocket_info():
#     """WebSocket connection information"""
#     return jsonify({
#         'websocket_available': False,
#         'websocket_url': 'ws://localhost:5000/socket.io',
#         'events': ['calendar_update', 'sync_status', 'health_check']
#     })


# ===============================
# ERROR HANDLERS
# ===============================

@api_bp.errorhandler(400)
def bad_request(error):
    """Handle 400 Bad Request errors"""
    return jsonify({
        'error': 'Bad request',
        'message': 'Invalid request parameters'
    }), 400


@api_bp.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors"""
    return jsonify({
        'error': 'Not found',
        'message': 'API endpoint not found'
    }), 404


@api_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server Error"""
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500
