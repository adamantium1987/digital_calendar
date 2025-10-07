# server/api/routes.py
"""
REST API endpoints for Pi Zero display clients
Provides clean JSON APIs for calendar data retrieval
"""

from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta

from ..sync.task_manager import TaskManager
from ..sync.sync_engine import sync_engine
from ..config.settings import config
from ..config.logger import get_logger
from ..config.constants import API_RATE_LIMIT_PER_HOUR

# Get logger for this module
logger = get_logger(__name__)

# Create API blueprint with versioning
api_bp = Blueprint('api', __name__)


def get_limiter():
    """
    Get the rate limiter instance from Flask app

    Returns:
        Limiter instance or None if not available
    """
    try:
        return None
    except (RuntimeError, AttributeError):
        logger.warning("Rate limiter not available in current context")
        return None


def rate_limit(limit_string: str):
    """
    Decorator for rate limiting individual endpoints

    Args:
        limit_string: Rate limit string (e.g., "100 per hour")

    Returns:
        Decorator function that applies rate limiting
    """

    def decorator(func):
        # Apply rate limit if limiter is available
        limiter = get_limiter()
        if limiter:
            return limiter.limit(limit_string)(func)
        else:
            logger.warning(f"Rate limiter not available for {func.__name__}")
            return func

    return decorator


# ===============================
# CALENDAR DATA ENDPOINTS
# ===============================
@api_bp.route('/events')
@rate_limit(f"{API_RATE_LIMIT_PER_HOUR} per hour")
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
        logger.info(f"Events request from {request.remote_addr}")

        # Add debug logging
        logger.info(f"Raw start_date param: {request.args.get('start_date')}")
        logger.info(f"Raw end_date param: {request.args.get('end_date')}")
        logger.info(f"Raw view param: {request.args.get('view')}")

        # Parse query parameters
        view = request.args.get('view', 'month')
        accounts = request.args.get('accounts', '').split(',') if request.args.get('accounts') else None
        calendars = request.args.get('calendars', '').split(',') if request.args.get('calendars') else None

        # Parse dates or use defaults based on view
        start_date = None
        end_date = None

        if request.args.get('start_date'):
            try:
                from urllib.parse import unquote
                start_date_str = unquote(request.args.get('start_date'))
                start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                logger.info(f"Parsed start_date: {start_date}")
            except ValueError:
                logger.warning(f"Invalid start_date format: {request.args.get('start_date')}")
                return jsonify({'error': 'Invalid start_date format. Use ISO format.'}), 400

        if request.args.get('end_date'):
            try:
                from urllib.parse import unquote
                end_date_str = unquote(request.args.get('end_date'))
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
                logger.info(f"Parsed end_date: {end_date}")
            except ValueError:
                logger.warning(f"Invalid end_date format: {request.args.get('end_date')}")
                return jsonify({'error': 'Invalid end_date format. Use ISO format.'}), 400

        # Set default date ranges based on view ONLY if no dates provided
        if not start_date:
            from datetime import timezone
            start_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            logger.info(f"Using default start_date: {start_date}")

        if not end_date:
            if view == 'day':
                end_date = start_date + timedelta(days=1)
            elif view == 'week':
                end_date = start_date + timedelta(days=7)
            elif view == 'month':
                end_date = start_date + timedelta(days=30)
            else:
                end_date = start_date + timedelta(days=7)  # Default to week
            logger.info(f"Using default end_date: {end_date}")

        logger.info(f"Final date range: {start_date} to {end_date}")

        # Get events from sync engine
        events = sync_engine.get_events(
            start_date=start_date,
            end_date=end_date,
            account_ids=accounts,
            calendar_ids=calendars
        )

        logger.info(f"Retrieved {len(events)} events from sync engine")

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

        logger.info(f"Returning {len(events_data)} events for view={view}")

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

    except ValueError as e:
        logger.error(f"Value error getting events: {e}")
        return jsonify({'error': f'Invalid parameter: {str(e)}'}), 400

    except Exception as e:
        logger.error(f"Error getting events: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@api_bp.route('/events/today')
@rate_limit(f"{API_RATE_LIMIT_PER_HOUR} per hour")
def get_today_events():
    """Get today's events (convenience endpoint)"""
    logger.info(f"Today's events request from {request.remote_addr}")
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)

    return get_events_internal(today, tomorrow)


@api_bp.route('/events/week')
@rate_limit(f"{API_RATE_LIMIT_PER_HOUR} per hour")
def get_week_events():
    """Get this week's events (convenience endpoint)"""
    logger.info(f"Week's events request from {request.remote_addr}")
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = today + timedelta(days=7)

    return get_events_internal(today, week_end)


def get_events_internal(start_date: datetime, end_date: datetime):
    """
    Internal helper for getting events

    Args:
        start_date: Start of date range
        end_date: End of date range

    Returns:
        Flask JSON response
    """
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
        logger.error(f"Error getting events (internal): {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@api_bp.route('/calendars')
@rate_limit(f"{API_RATE_LIMIT_PER_HOUR} per hour")
def get_calendars():
    """Get list of all calendars with account information

    Query Parameters:
        account_id: Specific account ID (optional)

    Returns:
        JSON object with calendars grouped by account
    """
    try:
        logger.info(f"Calendars request from {request.remote_addr}")
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

        logger.info(f"Returning {len(result)} accounts with calendars")

        return jsonify({
            'calendars': result,
            'metadata': {
                'total_accounts': len(result),
                'total_calendars': sum(len(acc['calendars']) for acc in result.values())
            }
        })

    except Exception as e:
        logger.error(f"Error getting calendars: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


# ===============================
# STATUS AND HEALTH ENDPOINTS
# ===============================

@api_bp.route('/status')
@rate_limit(f"{API_RATE_LIMIT_PER_HOUR} per hour")
def get_status():
    """Get sync engine status and health information"""
    try:
        logger.debug(f"Status request from {request.remote_addr}")

        if not sync_engine:
            logger.warning("Status requested but sync engine unavailable")
            return jsonify({'error': 'Sync engine not available'}), 503

        status = sync_engine.get_sync_status()

        # Add cache statistics
        cache_stats = sync_engine.cache_manager.get_cache_stats()
        status['cache_stats'] = cache_stats

        # Add server info
        from ..config.constants import API_VERSION
        status['server_info'] = {
            'running': sync_engine.is_running,
            'version': '1.0.0',
            'api_version': API_VERSION
        }

        return jsonify(status)

    except Exception as e:
        logger.error(f"Error getting status: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@api_bp.route('/health')
def health_check():
    """Enhanced health check endpoint for Pi Zero clients

    Performs deep health checks on:
    - Sync engine availability and status
    - Database connectivity
    - Configuration validity
    - Account authentication status
    """
    try:
        logger.debug(f"Health check from {request.remote_addr}")

        health = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }

        # Check sync engine
        if sync_engine:
            health['checks']['sync_engine'] = {
                'status': 'ok' if sync_engine.is_running else 'degraded',
                'running': sync_engine.is_running
            }
        else:
            health['checks']['sync_engine'] = {
                'status': 'unavailable',
                'running': False
            }
            health['status'] = 'degraded'

        # Check database connectivity
        try:
            cache_stats = sync_engine.cache_manager.get_cache_stats() if sync_engine else {}
            health['checks']['database'] = {
                'status': 'ok',
                'accessible': True,
                'events_cached': cache_stats.get('total_events', 0)
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            health['checks']['database'] = {
                'status': 'error',
                'accessible': False,
                'error': str(e)
            }
            health['status'] = 'unhealthy'

        # Check configuration
        try:
            accounts = config.list_accounts()
            total_accounts = len(accounts['google']) + len(accounts['apple'])
            health['checks']['configuration'] = {
                'status': 'ok',
                'valid': True,
                'accounts_configured': total_accounts
            }
        except Exception as e:
            logger.error(f"Configuration health check failed: {e}")
            health['checks']['configuration'] = {
                'status': 'error',
                'valid': False,
                'error': str(e)
            }
            health['status'] = 'unhealthy'

        # Check account authentication
        authenticated_accounts = 0
        total_accounts = 0
        if sync_engine:
            for source_id, source in sync_engine.sources.items():
                total_accounts += 1
                if source.is_authenticated:
                    authenticated_accounts += 1

        health['checks']['authentication'] = {
            'status': 'ok' if authenticated_accounts == total_accounts else 'degraded',
            'authenticated_accounts': authenticated_accounts,
            'total_accounts': total_accounts
        }

        if authenticated_accounts < total_accounts:
            health['status'] = 'degraded'

        # Set HTTP status code based on health
        status_code = 200
        if health['status'] == 'degraded':
            status_code = 200  # Still operational but not optimal
        elif health['status'] == 'unhealthy':
            status_code = 503  # Service unavailable

        return jsonify(health), status_code

    except Exception as e:
        logger.error(f"Health check error: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 500


@api_bp.route('/sync', methods=['POST'])
@rate_limit("10 per hour")  # Stricter limit for sync operations
def trigger_sync():
    """Trigger immediate synchronization"""
    try:
        logger.info(f"Manual sync triggered by {request.remote_addr}")

        if not sync_engine:
            logger.warning("Sync requested but sync engine unavailable")
            return jsonify({
                'status': 'error',
                'message': 'Sync engine not available'
            }), 503

        if sync_engine.force_sync():
            logger.info("✓ Manual sync started successfully")
            return jsonify({
                'status': 'success',
                'message': 'Sync started',
                'timestamp': datetime.now().isoformat()
            })
        else:
            logger.warning("Manual sync failed - already in progress")
            return jsonify({
                'status': 'error',
                'message': 'Sync already in progress'
            }), 409

    except Exception as e:
        logger.error(f"Error triggering sync: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


# ===============================
# CONFIGURATION ENDPOINTS
# ===============================

@api_bp.route('/config')
@rate_limit(f"{API_RATE_LIMIT_PER_HOUR} per hour")
def get_config():
    """Get display configuration for Pi Zero clients"""
    try:
        logger.debug(f"Config request from {request.remote_addr}")

        from ..config.constants import (
            DEFAULT_SYNC_INTERVAL_MINUTES,
            GOOGLE_CALENDAR_COLOR,
            APPLE_CALENDAR_COLOR,
            DEFAULT_EVENT_COLOR
        )

        display_config = {
            'timezone': config.get('display.timezone', 'UTC'),
            'date_format': config.get('display.date_format', '%Y-%m-%d'),
            'time_format': config.get('display.time_format', '%H:%M'),
            'default_view': config.get('display.default_view', 'week'),
            'sync_interval': config.get('sync.interval_minutes', DEFAULT_SYNC_INTERVAL_MINUTES),
            'colors': {
                'google': GOOGLE_CALENDAR_COLOR,
                'apple': APPLE_CALENDAR_COLOR,
                'default': DEFAULT_EVENT_COLOR
            }
        }

        return jsonify({
            'config': display_config,
            'accounts': config.list_accounts()
        })

    except Exception as e:
        logger.error(f"Error getting config: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


# ===============================
# UTILITY ENDPOINTS
# ===============================

@api_bp.route('/time')
def get_server_time():
    """Get current server time (useful for Pi Zero clock sync)"""
    logger.debug(f"Server time request from {request.remote_addr}")
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
@rate_limit(f"{API_RATE_LIMIT_PER_HOUR} per hour")
def get_accounts():
    """Get list of configured accounts"""
    try:
        logger.info(f"Accounts request from {request.remote_addr}")
        accounts = config.list_accounts()

        # Add status information
        sync_status = sync_engine.get_sync_status() if sync_engine else {}
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

        logger.info(f"Returning {len(result['google'])} Google and {len(result['apple'])} Apple accounts")

        return jsonify({
            'accounts': result,
            'metadata': {
                'total_google': len(result['google']),
                'total_apple': len(result['apple']),
                'total_all': len(result['google']) + len(result['apple'])
            }
        })

    except Exception as e:
        logger.error(f"Error getting accounts: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


# ===============================
# task CHART ENDPOINTS
# ===============================

@api_bp.route('/tasks')
@rate_limit(f"{API_RATE_LIMIT_PER_HOUR} per hour")
def get_tasks():
    """Get tasks with optional filtering

    Query Parameters:
        day: Day name (e.g., 'monday')
        name: name
        week: Week start date (ISO format)
        format: 'grouped' (default) or 'individual'

    Returns:
        JSON object with tasks list
    """
    try:
        logger.info(f"tasks request from {request.remote_addr}")

        if not sync_engine:
            return jsonify({'error': 'Sync engine not available'}), 503

        task_manager = TaskManager(sync_engine.cache_manager)

        # Parse query parameters
        day_name = request.args.get('day')
        name = request.args.get('name')
        week_start = request.args.get('week', task_manager.get_current_week_start())
        format_type = request.args.get('format', 'grouped')
        if format_type == 'individual':
            # Get individual day records
            task_days = task_manager.cache_manager.get_task_days(
                day_name=day_name,
                name=name,
                week_start=week_start
            )
            return jsonify({
                'task_days': task_days,
                'metadata': {
                    'total_records': len(task_days),
                    'week_start': week_start,
                    'format': 'individual'
                }
            })
        else:
            # Get grouped tasks (original format)
            tasks = task_manager.cache_manager.get_tasks(
                day_name=day_name,
                name=name,
                week_start=week_start
            )

            # Convert to JSON-serializable format
            tasks_data = []
            for task in tasks:

                task_data = {
                    'id': task.id,
                    'name': task.name,
                    'type': task.type,
                    'task': task.task,
                    'days': task.days,
                    'completed': task.completed,
                    'week_start': task.week_start
                }
                tasks_data.append(task_data)
            return jsonify({
                'tasks': tasks_data,
                'metadata': {
                    'total_tasks': len(tasks_data),
                    'week_start': week_start,
                    'format': 'grouped'
                }
            })

    except Exception as e:
        logger.error(f"Error getting tasks: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500
    # Grouped tasks:  /api/tasks
    # Individual day records:/api/tasks?format=individual
    # Specific day: /api/tasks?day=monday&format=individual


@api_bp.route('/tasks/<int:task_id>/<day_name>/complete', methods=['POST'])
@rate_limit(f"{API_RATE_LIMIT_PER_HOUR} per hour")
def complete_task(task_id: int, day_name: str):
    """Mark a task as complete for a specific day

    Request Body:
        completed: boolean (default: true)

    Returns:
        JSON success/error response
    """
    try:
        logger.info(f"task completion request from {request.remote_addr}: {task_id} on {day_name}")

        if not sync_engine:
            return jsonify({'error': 'Sync engine not available'}), 503

        # Validate day name
        valid_days = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
        if day_name.lower() not in valid_days:
            return jsonify({'error': 'Invalid day name'}), 400

        task_manager = TaskManager(sync_engine.cache_manager)

        # Parse request body
        data = request.get_json() or {}
        completed = data.get('completed', True)

        if not isinstance(completed, bool):
            return jsonify({'error': 'completed must be boolean'}), 400

        # Update task for specific day
        success = task_manager.cache_manager.update_task_completion(
            task_id=task_id,
            day_name=day_name.lower(),
            completed=completed,
            week_start=task_manager.get_current_week_start()
        )

        if success:
            logger.info(f"task {task_id} on {day_name} marked as {'complete' if completed else 'incomplete'}")
            return jsonify({
                'status': 'success',
                'message': f'task marked as {"complete" if completed else "incomplete"}',
                'task_id': task_id,
                'day_name': day_name,
                'completed': completed
            })
        else:
            logger.warning(f"Failed to update task: {task_id} on {day_name}")
            return jsonify({'error': 'task not found or update failed'}), 404

    except Exception as e:
        logger.error(f"Error completing task: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@api_bp.route('/tasks/sync', methods=['POST'])
@rate_limit("10 per hour")
def sync_tasks():
    """Trigger task synchronization from CSV"""
    try:
        logger.info(f"task sync triggered by {request.remote_addr}")

        if not sync_engine:
            return jsonify({'error': 'Sync engine not available'}), 503

        task_manager = TaskManager(sync_engine.cache_manager)

        if task_manager.sync_tasks():
            logger.info("task sync completed successfully")
            return jsonify({
                'status': 'success',
                'message': 'tasks synced from CSV',
                'timestamp': datetime.now().isoformat()
            })
        else:
            logger.warning("task sync failed")
            return jsonify({
                'status': 'error',
                'message': 'task sync failed'
            }), 500

    except Exception as e:
        logger.error(f"Error syncing tasks: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


# Add after the sync_tasks endpoint

@api_bp.route('/tasks/load', methods=['POST'])
@rate_limit("10 per hour")
def load_tasks():
    """Load/reload tasks from CSV or create from JSON data

    Request Body (optional):
        tasks: Array of task objects with {name, task, days}
        If no body provided, loads from CSV file

    Returns:
        JSON response with loaded tasks
    """
    try:
        logger.info(f"task load request from {request.remote_addr}")

        if not sync_engine:
            return jsonify({'error': 'Sync engine not available'}), 503

        task_manager = TaskManager(sync_engine.cache_manager)

        # Check if JSON data provided
        data = request.get_json()

        if data and 'tasks' in data:
            # Create tasks from JSON data
            from ..task_chart.base import TaskItem
            import uuid

            tasks = []
            current_week = task_manager.get_current_week_start()

            for task_data in data['tasks']:
                try:
                    name = task_data.get('name', '').strip()
                    task = task_data.get('task', '').strip()
                    days_input = task_data.get('days', '')

                    if not all([name, task, days_input]):
                        continue

                    # Handle days as string or array
                    if isinstance(days_input, str):
                        days = [day.strip().lower() for day in days_input.split('|')]
                    else:
                        days = [str(day).strip().lower() for day in days_input]

                    # Validate days
                    valid_days = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
                    days = [day for day in days if day in valid_days]

                    if not days:
                        continue

                    # Create unique ID
                    task_id = f"{name}_{task}_{str(uuid.uuid4())[:8]}".replace(' ', '_').lower()

                    task = TaskItem(
                        id=task_id,
                        name=name,
                        task=task,
                        days=days,
                        week_start=current_week
                    )

                    tasks.append(task)

                except Exception as e:
                    logger.warning(f"Error parsing task data: {e}")
                    continue

            if tasks:
                task_manager.cache_manager.store_tasks(tasks)
                logger.info(f"Created {len(tasks)} tasks from JSON data")

        else:
            # Load from CSV
            if task_manager.sync_tasks():
                logger.info("tasks loaded from CSV")
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to load tasks from CSV'
                }), 500

        # Get current tasks to return
        current_tasks = task_manager.cache_manager.get_tasks(
            week_start=task_manager.get_current_week_start()
        )

        tasks_data = []
        for task in current_tasks:
            tasks_data.append({
                'id': task.id,
                'name': task.name,
                'task': task.task,
                'days': task.days,
                'completed': task.completed,
                'week_start': task.week_start
            })

        return jsonify({
            'status': 'success',
            'message': f'Loaded {len(tasks_data)} tasks',
            'tasks': tasks_data,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error loading tasks: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@api_bp.route('/tasks/debug', methods=['GET'])
@rate_limit(f"{API_RATE_LIMIT_PER_HOUR} per hour")
def debug_tasks():
    """Debug endpoint to check CSV file and task loading"""
    try:
        if not sync_engine:
            return jsonify({'error': 'Sync engine not available'}), 503

        task_manager = TaskManager(sync_engine.cache_manager)

        debug_info = {
            'csv_path': str(task_manager.csv_path),
            'csv_exists': task_manager.csv_path.exists(),
            'current_week': task_manager.get_current_week_start()
        }

        # Try to read CSV
        if task_manager.csv_path.exists():
            try:
                with open(task_manager.csv_path, 'r') as f:
                    content = f.read()
                debug_info['csv_content'] = content[:500]  # First 500 chars
                debug_info['csv_lines'] = len(content.split('\n'))
            except Exception as e:
                debug_info['csv_read_error'] = str(e)

        # Try to load tasks
        try:
            tasks = task_manager.load_tasks_from_csv()
            debug_info['parsed_tasks'] = len(tasks)
            debug_info['sample_tasks'] = [
                {
                    'id': task.id,
                    'name': task.name,
                    'task': task.task,
                    'days': task.days
                } for task in tasks[:3]  # First 3 tasks
            ]
        except Exception as e:
            debug_info['parse_error'] = str(e)

        # Check database
        try:
            db_tasks = task_manager.cache_manager.get_tasks(
                week_start=task_manager.get_current_week_start()
            )
            debug_info['db_tasks'] = len(db_tasks)
        except Exception as e:
            debug_info['db_error'] = str(e)

        return jsonify(debug_info)

    except Exception as e:
        logger.error(f"Error in tasks debug: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# Add this to server/api/routes.py after the existing get_tasks function

@api_bp.route('/tasks/summary')
@rate_limit(f"{API_RATE_LIMIT_PER_HOUR} per hour")
def get_tasks_summary():
    """Get task summary statistics for dashboard display"""
    try:
        if not sync_engine:
            return jsonify({'error': 'Sync engine not available'}), 503

        task_manager = TaskManager(sync_engine.cache_manager)
        week_start = task_manager.get_current_week_start()

        # Get all task days for current week
        task_days = task_manager.cache_manager.get_task_days(week_start=week_start)

        # Calculate statistics
        total_tasks = len(task_days)
        completed_tasks = len([c for c in task_days if c['completed']])
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # Group by name
        people_stats = {}
        for task_day in task_days:
            name = task_day['name']
            if name not in people_stats:
                people_stats[name] = {'total': 0, 'completed': 0}

            people_stats[name]['total'] += 1
            if task_day['completed']:
                people_stats[name]['completed'] += 1

        # Add completion rates
        for people_stats in people_stats.values():
            people_stats['completion_rate'] = (
                people_stats['completed'] / people_stats['total'] * 100
                if people_stats['total'] > 0 else 0
            )

        return jsonify({
            'summary': {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'completion_rate': round(completion_rate, 1),
                'week_start': week_start
            },
            'people': people_stats,
            'metadata': {
                'updated_at': datetime.now().isoformat()
            }
        })

    except Exception as e:
        logger.error(f"Error getting task summary: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

# ===============================
# API INFORMATION ENDPOINT
# ===============================

@api_bp.route('/')
def api_info():
    """API information and available endpoints"""
    logger.debug(f"API info request from {request.remote_addr}")

    from ..config.constants import API_VERSION

    return jsonify({
        'name': 'Pi Calendar API',
        'version': API_VERSION,
        'description': 'REST API for Pi Calendar Server',
        'endpoints': {
            'events': {
                'GET /events': 'Get calendar events with filtering',
                'GET /events/today': 'Get today\'s events',
                'GET /events/week': 'Get this week\'s events'
            },
            'calendars': {
                'GET /calendars': 'Get list of calendars'
            },
            'status': {
                'GET /status': 'Get sync engine status',
                'GET /health': 'Health check with deep checks',
                'POST /sync': 'Trigger manual sync'
            },
            'configuration': {
                'GET /config': 'Get display configuration',
                'GET /accounts': 'Get configured accounts'
            },
            'utility': {
                'GET /time': 'Get server time'
            }
        },
        'rate_limits': {
            'default': f'{API_RATE_LIMIT_PER_HOUR} requests per hour',
            'sync': '10 requests per hour'
        },
        'documentation': 'https://github.com/yourusername/pi-calendar'
    })


# ===============================
# ERROR HANDLERS
# ===============================

@api_bp.errorhandler(400)
def bad_request(error):
    """Handle 400 Bad Request errors"""
    logger.warning(f"400 Bad Request: {error}")
    return jsonify({
        'error': 'Bad request',
        'message': 'Invalid request parameters'
    }), 400


@api_bp.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors"""
    logger.warning(f"404 Not Found: {request.path} : {error}")
    return jsonify({
        'error': 'Not found',
        'message': 'API endpoint not found',
        'path': request.path
    }), 404


@api_bp.errorhandler(429)
def ratelimit_error(error):
    """Handle rate limit errors"""
    logger.warning(f"429 Rate Limit: {request.remote_addr} exceeded limit : {error}")
    return jsonify({
        'error': 'Too many requests',
        'message': 'Rate limit exceeded. Please try again later.',
        'retry_after': '3600'
    }), 429


@api_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server Error"""
    logger.error(f"500 Internal Server Error: {error}", exc_info=True)
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500


@api_bp.errorhandler(503)
def service_unavailable(error):
    """Handle 503 Service Unavailable"""
    logger.error(f"503 Service Unavailable: {error}")
    return jsonify({
        'error': 'Service unavailable',
        'message': 'The service is temporarily unavailable. Please try again later.'
    }), 503
