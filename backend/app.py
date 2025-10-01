# backend/server/app.py
"""
Main Flask application for Pi Calendar Server
Provides REST API for Pi Zero clients and web interface for configuration
"""

import os
from pathlib import Path

from flask import Flask, jsonify, request, redirect, url_for, session, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS

# Allow OAuth over HTTP for local development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Import configuration and logging FIRST
from .config.settings import config
from .config.logger import setup_logging, get_logger
from .config.constants import (
    DEFAULT_SERVER_HOST,
    DEFAULT_SERVER_PORT,
    DEFAULT_SERVER_DEBUG,
    API_RATE_LIMIT_PER_HOUR,
    API_VERSION
)

# Setup logging before anything else
log_dir = Path(config.config_dir) / "logs"
setup_logging(
    log_dir=log_dir,
    log_level=config.get('logging.level', 'INFO'),
    console_output=True
)
logger = get_logger(__name__)

logger.info("=" * 70)
logger.info("Pi Calendar Server Initializing")
logger.info("=" * 70)
logger.info(f"Config directory: {config.config_dir}")
logger.info(f"Config file: {config.config_file}")
logger.info(f"Log directory: {log_dir}")

from .api.routes import api_bp


def create_app() -> Flask:
    """Create and configure Flask application"""
    logger.info("Creating Flask application...")

    # Point to React build directory
    static_folder = Path(__file__).parent.parent.parent / 'frontend' / 'build'

    app = Flask(__name__,
                static_folder=str(static_folder),
                static_url_path='')

    # Enable CORS for development
    if config.get('server.debug', DEFAULT_SERVER_DEBUG):
        CORS(app, resources={
            r"/api/*": {"origins": "http://localhost:3000"},
            r"/setup/*": {"origins": "http://localhost:3000"},
            r"/oauth/*": {"origins": "http://localhost:3000"},
            r"/accounts/*": {"origins": "http://localhost:3000"},
            r"/sync": {"origins": "http://localhost:3000"},
            r"/status": {"origins": "http://localhost:3000"}
        })
        logger.info("CORS enabled for development")

    # Generate random secret key if not set
    secret_key = config.get('server.secret_key')
    if not secret_key:
        import secrets
        secret_key = secrets.token_hex(32)
        config.set('server.secret_key', secret_key)
        logger.info("Generated new secret key for Flask sessions")

    app.secret_key = secret_key

    # Initialize rate limiter
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=[f"{API_RATE_LIMIT_PER_HOUR} per hour"],
        storage_uri="memory://",
        strategy="fixed-window"
    )
    logger.info(f"Rate limiter initialized: {API_RATE_LIMIT_PER_HOUR} requests/hour")

    # Register API blueprint
    app.register_blueprint(api_bp, url_prefix='/api')
    logger.info("API blueprint registered at /api")

    # Store limiter in app config for use in routes
    app.limiter = limiter

    logger.info("Flask application created successfully")
    return app


# Create Flask app
app = create_app()

# Import sync engine after app creation to avoid circular imports
try:
    from .sync.sync_engine import sync_engine

    logger.info("Sync engine imported successfully")
except ImportError as e:
    sync_engine = None
    logger.error(f"Failed to import sync engine: {e}")


# ===============================
# BACKEND ROUTES (Keep all of these!)
# ===============================

@app.route('/setup/google', methods=['GET', 'POST'])
def setup_google():
    """Google account setup with proper error handling"""
    if request.method == 'POST':
        try:
            display_name = request.form.get('display_name', '').strip()
            client_id = request.form.get('client_id', '').strip()
            client_secret = request.form.get('client_secret', '').strip()

            if not all([display_name, client_id, client_secret]):
                logger.warning("Google account setup failed: missing required fields")
                return jsonify({'error': 'All fields are required'}), 400

            # Import here to avoid circular imports
            from .calendar_sources.google_cal import GoogleCalendarSetup

            # Create account and store OAuth client credentials
            account_id = GoogleCalendarSetup.setup_google_account(
                display_name, client_id, client_secret
            )
            logger.info(f"Google account created: {display_name} (ID: {account_id})")

            # Add to sync engine if available
            if sync_engine:
                account_config = {
                    'id': account_id,
                    'display_name': display_name
                }
                sync_engine.add_account('google', account_config)
                logger.info(f"Added Google account to sync engine: {display_name}")

            # Redirect to OAuth flow to authenticate
            return redirect(url_for('start_google_oauth', account_id=account_id))

        except Exception as e:
            logger.error(f"Error setting up Google account: {e}", exc_info=True)
            return jsonify({'error': f'Setup failed: {str(e)}'}), 500

    # GET request - React handles the form
    return jsonify({'message': 'Use React frontend for setup form'}), 200


@app.route('/oauth/google/start/<account_id>')
def start_google_oauth(account_id: str):
    """Initiate Google OAuth flow for an account"""
    try:
        logger.info(f"Starting Google OAuth flow for account: {account_id}")

        # Get account info
        accounts = config.list_accounts()
        account = None
        for acc in accounts['google']:
            if acc['id'] == account_id:
                account = acc
                break

        if not account:
            logger.error(f"Account not found: {account_id}")
            return jsonify({'error': 'Account not found'}), 404

        # Get stored credentials (client_id, client_secret)
        stored_creds = config.get_credentials(account_id)
        if not stored_creds or 'client_id' not in stored_creds:
            logger.error(f"OAuth credentials not found for account: {account_id}")
            return jsonify({'error': 'OAuth credentials not found'}), 400

        # Create OAuth flow
        from google_auth_oauthlib.flow import Flow

        client_config = {
            "web": {
                "client_id": stored_creds['client_id'],
                "client_secret": stored_creds['client_secret'],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [f"http://{request.host}/oauth/google/callback"]
            }
        }

        flow = Flow.from_client_config(
            client_config,
            scopes=['https://www.googleapis.com/auth/calendar.readonly'],
            redirect_uri=f"http://{request.host}/oauth/google/callback"
        )

        # Store account_id in session for callback
        session['oauth_account_id'] = account_id

        # Generate authorization URL
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )

        # Store state in session for verification
        session['oauth_state'] = state

        logger.info(f"OAuth flow initiated for {account.get('display_name')}")

        # Redirect user to Google
        return redirect(auth_url)

    except Exception as e:
        logger.error(f"Error starting OAuth flow: {e}", exc_info=True)
        return jsonify({'error': f'Failed to start OAuth: {str(e)}'}), 500


@app.route('/oauth/google/callback')
def google_oauth_callback():
    """Handle Google OAuth callback"""
    try:
        logger.info("Processing Google OAuth callback")

        # Verify state to prevent CSRF
        state = session.get('oauth_state')
        if not state:
            logger.error("Invalid OAuth state - possible CSRF attack")
            return jsonify({'error': 'Invalid OAuth state'}), 400

        # Get account_id from session
        account_id = session.get('oauth_account_id')
        if not account_id:
            logger.error("OAuth session expired")
            return jsonify({'error': 'OAuth session expired'}), 400

        # Get stored credentials
        stored_creds = config.get_credentials(account_id)
        if not stored_creds:
            logger.error(f"Account credentials not found: {account_id}")
            return jsonify({'error': 'Account credentials not found'}), 400

        # Recreate flow
        from google_auth_oauthlib.flow import Flow

        client_config = {
            "web": {
                "client_id": stored_creds['client_id'],
                "client_secret": stored_creds['client_secret'],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [f"http://{request.host}/oauth/google/callback"]
            }
        }

        flow = Flow.from_client_config(
            client_config,
            scopes=['https://www.googleapis.com/auth/calendar.readonly'],
            redirect_uri=f"http://{request.host}/oauth/google/callback",
            state=state
        )

        # Exchange authorization code for credentials
        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials

        # Save credentials
        creds_data = {
            'client_id': stored_creds['client_id'],
            'client_secret': stored_creds['client_secret'],
            'google_token': {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes
            }
        }

        config.store_credentials(account_id, creds_data)
        logger.info(f"OAuth credentials saved for account: {account_id}")

        # Reload the source in sync engine if available
        if sync_engine:
            if account_id in sync_engine.sources:
                del sync_engine.sources[account_id]

            # Get account info
            accounts = config.list_accounts()
            account_info = None
            for acc in accounts['google']:
                if acc['id'] == account_id:
                    account_info = acc
                    break

            if account_info:
                from .calendar_sources.google_cal import GoogleCalendarSource
                source = GoogleCalendarSource(account_id, account_info)
                source.set_oauth_credentials(
                    stored_creds['client_id'],
                    stored_creds['client_secret']
                )
                source.set_token(creds_data['google_token'])
                sync_engine.sources[account_id] = source
                logger.info(f"Reloaded source for {account_info.get('display_name', account_id)}")

        # Clear session data
        session.pop('oauth_account_id', None)
        session.pop('oauth_state', None)

        logger.info(f"Successfully authenticated Google account: {account_id}")

        # Redirect back to setup page
        return redirect('/setup')

    except Exception as e:
        logger.error(f"Error in OAuth callback: {e}", exc_info=True)
        return jsonify({'error': f'OAuth authentication failed: {str(e)}'}), 500


@app.route('/setup/apple', methods=['GET', 'POST'])
def setup_apple():
    """Apple account setup with proper error handling"""
    if request.method == 'POST':
        try:
            display_name = request.form.get('display_name', '').strip()
            username = request.form.get('username', '').strip()

            if not all([display_name, username]):
                logger.warning("Apple account setup failed: missing required fields")
                return jsonify({'error': 'All fields are required'}), 400

            # Import here to avoid circular imports
            from .calendar_sources.apple_cal import AppleCalendarSetup

            if not AppleCalendarSetup.validate_username(username):
                logger.warning(f"Invalid email format: {username}")
                return jsonify({'error': 'Invalid email format'}), 400

            account_id = AppleCalendarSetup.setup_apple_account(
                display_name, username
            )
            logger.info(f"Apple account created: {display_name} (ID: {account_id})")

            # Add to sync engine if available
            if sync_engine:
                account_config = {
                    'id': account_id,
                    'display_name': display_name,
                    'username': username
                }
                sync_engine.add_account('apple', account_config)
                logger.info(f"Added Apple account to sync engine: {display_name}")

            # Redirect to authentication page
            return redirect(url_for('authenticate_apple', account_id=account_id))

        except Exception as e:
            logger.error(f"Error setting up Apple account: {e}", exc_info=True)
            return jsonify({'error': f'Setup failed: {str(e)}'}), 500

    # GET request - React handles the form
    return jsonify({'message': 'Use React frontend for setup form'}), 200


@app.route('/setup/apple/<account_id>/authenticate', methods=['GET', 'POST'])
def authenticate_apple(account_id: str):
    """Apple app-specific password entry"""
    try:
        # Get account info
        accounts = config.list_accounts()
        account = None
        for acc in accounts['apple']:
            if acc['id'] == account_id:
                account = acc
                break

        if not account:
            logger.error(f"Account not found: {account_id}")
            return jsonify({'error': 'Account not found'}), 404

        if request.method == 'POST':
            app_password = request.form.get('app_password', '').strip()

            # Remove spaces and dashes
            app_password = app_password.replace(' ', '').replace('-', '')

            # Validate format (16 chars)
            from .config.constants import APPLE_APP_PASSWORD_LENGTH
            if len(app_password) != APPLE_APP_PASSWORD_LENGTH or not app_password.isalnum():
                logger.warning(f"Invalid app password format for account: {account_id}")
                return jsonify({'error': 'Invalid format. Should be 16 characters'}), 400

            # Store the password
            config.store_credentials(account_id, {'app_password': app_password})
            logger.info(f"App password stored for account: {account_id}")

            # Reload the source in sync engine AND authenticate it
            if sync_engine:
                if account_id in sync_engine.sources:
                    del sync_engine.sources[account_id]

                from .calendar_sources.apple_cal import AppleCalendarSource
                source = AppleCalendarSource(account_id, account)

                # Authenticate the source NOW
                try:
                    authenticated = source.authenticate()
                    if authenticated:
                        sync_engine.sources[account_id] = source
                        logger.info(
                            f"Successfully authenticated Apple source for {account.get('display_name', account_id)}")
                    else:
                        logger.error(f"Authentication failed for Apple account: {account_id}")
                        return jsonify({'error': 'Authentication failed'}), 400
                except Exception as e:
                    logger.error(f"Authentication error: {e}", exc_info=True)
                    return jsonify({'error': f'Authentication failed: {str(e)}'}), 500

            return redirect('/setup')

        # GET request - show password entry form (React handles this)
        return jsonify({'message': 'Use React frontend for authentication form'}), 200

    except Exception as e:
        logger.error(f"Error authenticating Apple account: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/sync')
def sync_now():
    """Trigger immediate sync"""
    try:
        if sync_engine and sync_engine.force_sync():
            logger.info("Manual sync triggered")
            return jsonify({'status': 'success', 'message': 'Sync started'})
        else:
            logger.warning("Manual sync failed - already in progress or engine unavailable")
            return jsonify({'status': 'error', 'message': 'Sync already in progress or sync engine unavailable'}), 409
    except Exception as e:
        logger.error(f"Error triggering sync: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/status')
def status():
    """Get detailed system status"""
    try:
        if sync_engine:
            return jsonify(sync_engine.get_sync_status())
        else:
            logger.warning("Status requested but sync engine unavailable")
            return jsonify({'error': 'Sync engine not available'}), 503
    except Exception as e:
        logger.error(f"Error getting status: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/accounts/<account_id>/remove', methods=['POST'])
def remove_account(account_id: str):
    """Remove an account with proper error handling"""
    try:
        # Get account info for display
        accounts = config.list_accounts()
        account_info = None
        account_type = None

        for acc_type in ['google', 'apple']:
            for acc in accounts[acc_type]:
                if acc['id'] == account_id:
                    account_info = acc
                    account_type = acc_type
                    break
            if account_info:
                break

        if not account_info:
            logger.error(f"Account not found for removal: {account_id}")
            return jsonify({'error': 'Account not found'}), 404

        # Remove from config
        config.remove_account(account_type, account_id)
        logger.info(f"Removed account: {account_info.get('display_name')} (ID: {account_id})")

        # Remove from sync engine if available
        if sync_engine:
            sync_engine.remove_account(account_id)
            logger.info(f"Removed account from sync engine: {account_id}")

        return jsonify({'status': 'success', 'message': 'Account removed'})

    except Exception as e:
        logger.error(f"Error removing account: {e}", exc_info=True)
        return jsonify({'error': f'Failed to remove account: {str(e)}'}), 500


@app.route('/debug/config')
def debug_config():
    """Debug route to see current config"""
    return jsonify({
        'config_dir': str(config.config_dir),
        'config_file': str(config.config_file),
        'config_exists': config.config_file.exists(),
        'accounts': config.list_accounts(),
        'sync_sources': list(sync_engine.sources.keys()) if sync_engine else []
    })


# ===============================
# REACT APP SERVING (Add this at the end)
# ===============================

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    """Serve React app for all non-API routes"""
    # Check if it's a static file request (js, css, images, etc.)
    if path and (Path(app.static_folder) / path).exists():
        return send_from_directory(app.static_folder, path)

    # Serve index.html for React Router routes
    index_path = Path(app.static_folder) / 'index.html'
    if index_path.exists():
        return send_from_directory(app.static_folder, 'index.html')
    else:
        # Development mode - React not built yet
        return jsonify({
            'error': 'React app not built',
            'message': 'Run "cd frontend && npm run build" to build the React app, or run "npm start" in development mode'
        }), 503


# ===============================
# API ERROR HANDLERS
# ===============================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    if request.path.startswith('/api/'):
        logger.warning(f"404 - API endpoint not found: {request.path}")
        return jsonify({
            'error': 'Not found',
            'message': 'API endpoint not found',
            'path': request.path
        }), 404
    else:
        # Let React Router handle frontend 404s
        return serve_react(request.path)


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"500 - Internal server error: {error}", exc_info=True)
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500


@app.errorhandler(429)
def ratelimit_handler(error):
    """Handle rate limit errors"""
    logger.warning(f"Rate limit exceeded for {get_remote_address()}")
    return jsonify({
        'error': 'Too many requests',
        'message': 'Rate limit exceeded. Please try again later.'
    }), 429


# ===============================
# APPLICATION STARTUP
# ===============================

def start_server():
    """Start the Flask server and sync engine"""
    logger.info("=" * 70)
    logger.info("Starting Pi Calendar Server")
    logger.info("=" * 70)

    # Start sync engine if available
    if sync_engine:
        try:
            sync_engine.start()
            logger.info("Sync engine started successfully")
        except Exception as e:
            logger.error(f"Error starting sync engine: {e}", exc_info=True)
    else:
        logger.warning("Sync engine not available")

    # Get server configuration
    host = config.get('server.host', DEFAULT_SERVER_HOST)
    port = config.get('server.port', DEFAULT_SERVER_PORT)
    debug = config.get('server.debug', DEFAULT_SERVER_DEBUG)

    logger.info(f"Server configuration:")
    logger.info(f"  Host: {host}")
    logger.info(f"  Port: {port}")
    logger.info(f"  Debug: {debug}")
    logger.info(f"  API Version: {API_VERSION}")
    logger.info(f"  Rate Limit: {API_RATE_LIMIT_PER_HOUR} requests/hour")
    logger.info("=" * 70)
    logger.info(f"Server starting on http://{host}:{port}")
    logger.info(f"Web interface: http://localhost:{port}")
    logger.info(f"API endpoint: http://{host}:{port}/api")
    logger.info("=" * 70)

    # Run Flask app
    try:
        app.run(host=host, port=port, debug=debug, threaded=True)
    except Exception as e:
        logger.critical(f"Error starting Flask server: {e}", exc_info=True)
        raise


def stop_server():
    """Stop the server and sync engine"""
    logger.info("=" * 70)
    logger.info("Stopping Pi Calendar Server")
    logger.info("=" * 70)

    if sync_engine:
        try:
            sync_engine.stop()
            logger.info("Sync engine stopped")
        except Exception as e:
            logger.error(f"Error stopping sync engine: {e}", exc_info=True)

    logger.info("Server stopped")
    logger.info("=" * 70)


if __name__ == '__main__':
    start_server()