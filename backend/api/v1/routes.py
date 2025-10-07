"""
API v1 Routes

This module contains all v1 API endpoints with Pydantic validation.
"""

from __future__ import annotations

from flask import jsonify, request
from datetime import datetime
from typing import Any, Dict

from . import api_v1
from ..schemas import (
    EventQueryParams,
    GoogleAccountCreate,
    AppleAccountCreate,
    TaskComplete,
    SuccessResponse,
    ApiErrorResponse,
)
from ...utils.security import apply_security_headers, csrf_protect, InputSanitizer
from ...config.logger import get_logger

logger = get_logger(__name__)


@api_v1.route('/health')
@apply_security_headers
def health_check() -> tuple[Dict[str, Any], int]:
    """
    Health check endpoint

    Returns:
        Health status
    """
    return jsonify({
        'status': 'healthy',
        'version': 'v1',
        'timestamp': datetime.now().isoformat()
    }), 200


@api_v1.route('/events')
@apply_security_headers
def get_events() -> tuple[Dict[str, Any], int]:
    """
    Get calendar events with validation

    Query Parameters:
        - start_date: ISO datetime
        - end_date: ISO datetime
        - view: day|week|month
        - accounts: comma-separated account IDs
        - calendars: comma-separated calendar IDs

    Returns:
        List of events with metadata
    """
    try:
        # Validate query parameters using Pydantic
        params = EventQueryParams(
            start_date=request.args.get('start_date'),
            end_date=request.args.get('end_date'),
            view=request.args.get('view', 'month'),
            accounts=request.args.get('accounts'),
            calendars=request.args.get('calendars')
        )

        logger.info(
            "Events request",
            view=params.view,
            has_start_date=params.start_date is not None,
            has_end_date=params.end_date is not None
        )

        # Import here to avoid circular imports
        from ...sync.sync_engine import sync_engine

        # Get events
        events = sync_engine.get_events(
            start_date=params.start_date,
            end_date=params.end_date,
            account_ids=params.accounts,
            calendar_ids=params.calendars
        )

        # Convert to dict
        events_data = [
            {
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
            for event in events
        ]

        return jsonify({
            'events': events_data,
            'metadata': {
                'total': len(events_data),
                'view': params.view,
                'start_date': params.start_date.isoformat() if params.start_date else None,
                'end_date': params.end_date.isoformat() if params.end_date else None,
            }
        }), 200

    except ValueError as e:
        logger.warning("Invalid event query parameters", error=str(e))
        return jsonify(ApiErrorResponse(
            error='validation_error',
            message=str(e)
        ).dict()), 400
    except Exception as e:
        logger.error("Error getting events", error=str(e), exc_info=True)
        return jsonify(ApiErrorResponse(
            error='internal_error',
            message='Failed to retrieve events'
        ).dict()), 500


@api_v1.route('/accounts', methods=['GET'])
@apply_security_headers
def get_accounts() -> tuple[Dict[str, Any], int]:
    """
    Get configured accounts

    Returns:
        List of accounts
    """
    try:
        from ...config.settings import config
        from ...sync.sync_engine import sync_engine

        accounts = config.list_accounts()
        sync_status = sync_engine.get_sync_status() if sync_engine else {}
        sources = sync_status.get('sources', {})

        # Enhance with status
        result = {}
        for acc_type in ['google', 'apple']:
            result[acc_type] = []
            for acc in accounts.get(acc_type, []):
                acc_info = acc.copy()
                acc_id = acc['id']

                if acc_id in sources:
                    acc_info['authenticated'] = sources[acc_id].get('authenticated', False)
                    acc_info['sync_status'] = 'authenticated' if sources[acc_id].get('authenticated') else 'not_authenticated'
                else:
                    acc_info['authenticated'] = False
                    acc_info['sync_status'] = 'not_configured'

                result[acc_type].append(acc_info)

        return jsonify({
            'accounts': result,
            'metadata': {
                'total_google': len(result.get('google', [])),
                'total_apple': len(result.get('apple', [])),
                'version': 'v1'
            }
        }), 200

    except Exception as e:
        logger.error("Error getting accounts", error=str(e), exc_info=True)
        return jsonify(ApiErrorResponse(
            error='internal_error',
            message='Failed to retrieve accounts'
        ).dict()), 500


@api_v1.route('/sync', methods=['POST'])
@apply_security_headers
@csrf_protect
def trigger_sync() -> tuple[Dict[str, Any], int]:
    """
    Trigger manual sync (CSRF protected)

    Returns:
        Success response
    """
    try:
        from ...sync.sync_engine import sync_engine

        if not sync_engine:
            return jsonify(ApiErrorResponse(
                error='service_unavailable',
                message='Sync engine not available'
            ).dict()), 503

        if sync_engine.force_sync():
            logger.info("Manual sync triggered")
            return jsonify(SuccessResponse(
                message='Sync started successfully',
                timestamp=datetime.now()
            ).dict()), 200
        else:
            return jsonify(ApiErrorResponse(
                error='conflict',
                message='Sync already in progress'
            ).dict()), 409

    except Exception as e:
        logger.error("Error triggering sync", error=str(e), exc_info=True)
        return jsonify(ApiErrorResponse(
            error='internal_error',
            message='Failed to trigger sync'
        ).dict()), 500


@api_v1.route('/')
def api_info() -> Dict[str, Any]:
    """
    API information endpoint

    Returns:
        API version and available endpoints
    """
    return jsonify({
        'version': 'v1',
        'name': 'Digital Calendar API',
        'endpoints': {
            'GET /health': 'Health check',
            'GET /events': 'List calendar events',
            'GET /accounts': 'List accounts',
            'POST /sync': 'Trigger sync (requires CSRF token)',
            'GET /calendars': 'List calendars',
            'GET /status': 'Get sync status',
        },
        'documentation': '/api/v1/docs',
        'csrf_token_header': 'X-CSRF-Token',
    })
