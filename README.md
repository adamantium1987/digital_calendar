# Digital Calendar System

A comprehensive calendar synchronization system that aggregates events from Google Calendar and Apple iCloud, with a modern React frontend and Flask backend. Perfect for Raspberry Pi deployments and family calendar management.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![React](https://img.shields.io/badge/react-18.2-blue)
![TypeScript](https://img.shields.io/badge/typescript-4.9-blue)

## Features

### 📅 Calendar Sync
- **Multi-source support**: Google Calendar and Apple iCloud (CalDAV)
- **Automatic synchronization**: Configurable sync intervals
- **Event caching**: SQLite-based local storage for fast access
- **Date range control**: Sync past and future events

### 🎯 Task Management
- **Task chart system**: CSV-based task tracking
- **Family members**: Track tasks by person
- **Weekly tracking**: Completion status per day
- **Progress visualization**: Dashboard with completion rates

### 🌐 Modern Web Interface
- **Responsive design**: Works on desktop, tablet, and mobile
- **Multiple views**: Day, week, and month calendar displays
- **Account management**: Easy setup for Google and Apple accounts
- **Real-time updates**: Auto-refresh and manual sync options
- **Dark mode support**: (Optional feature)

### 🔒 Security
- **Encrypted credentials**: Fernet encryption for sensitive data
- **OAuth2 flow**: Secure Google Calendar authentication
- **Rate limiting**: API protection against abuse
- **Secure permissions**: Proper file system permissions

### 🚀 Performance
- **Background sync**: Non-blocking calendar updates
- **Caching layer**: Fast event retrieval
- **Optimized queries**: Efficient database operations
- **Retry logic**: Robust error handling

## Architecture

```
digital-calendar/
├── frontend/          # React/TypeScript frontend
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── hooks/        # Custom React hooks
│   │   ├── pages/        # Page components
│   │   ├── types/        # TypeScript type definitions
│   │   └── utils/        # Utility functions
│   └── build/         # Production build
│
├── backend/           # Python/Flask backend
│   ├── api/           # REST API routes
│   ├── calendar_sources/  # Calendar integrations
│   ├── config/        # Configuration management
│   ├── sync/          # Synchronization engine
│   └── utils/         # Helper functions
│
├── Dockerfile         # Container configuration
├── docker-compose.yml # Docker Compose setup
└── pyproject.toml     # Python project configuration
```

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 16+ and npm
- Google Cloud Project (for Google Calendar)
- Apple ID with app-specific password (for iCloud)

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/digital-calendar.git
cd digital-calendar

# Build and run with Docker Compose
docker-compose up -d

# Access the web interface
open http://localhost:5000
```

### Option 2: Manual Installation

#### Backend Setup

```bash
# Install Python dependencies
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run the backend server
python -m backend.app
```

#### Frontend Setup

```bash
# Install Node dependencies
cd frontend
npm install

# For development
npm start

# For production
npm run build
```

## Configuration

### Google Calendar Setup

1. Go to [Google Cloud Console](https://console.developers.google.com/)
2. Create a new project
3. Enable Google Calendar API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `http://localhost:5000/oauth/google/callback`
6. Download client ID and secret

### Apple iCloud Setup

1. Go to [Apple ID Account](https://appleid.apple.com/)
2. Sign in with your Apple ID
3. Navigate to Security → App-Specific Passwords
4. Generate a new app-specific password
5. Save the 16-character password (format: xxxx-xxxx-xxxx-xxxx)

### Adding Accounts

1. Navigate to `http://localhost:5000/setup`
2. Click "Add Google Account" or "Add Apple Account"
3. Follow the on-screen instructions
4. Complete OAuth flow (Google) or enter app password (Apple)

## API Documentation

### Base URL
```
http://localhost:5000/api
```

### Endpoints

#### Calendar Events
- `GET /api/events` - Get calendar events
  - Query params: `start_date`, `end_date`, `view` (day/week/month)
- `GET /api/events/today` - Get today's events
- `GET /api/events/week` - Get this week's events

#### Calendars
- `GET /api/calendars` - List all calendars
- `GET /api/calendars?account_id={id}` - Get calendars for specific account

#### Accounts
- `GET /api/accounts` - List configured accounts
- `POST /accounts/{id}/remove` - Remove an account

#### Sync
- `POST /api/sync` - Trigger manual sync
- `GET /api/status` - Get sync status

#### Tasks
- `GET /api/tasks` - Get tasks
- `POST /api/tasks/{id}/{day}/complete` - Mark task complete
- `POST /api/tasks/sync` - Sync tasks from CSV
- `POST /api/tasks/load` - Load tasks

#### System
- `GET /api/health` - Health check
- `GET /api/time` - Server time
- `GET /api/config` - Display configuration

## Development

### Frontend Development

```bash
cd frontend
npm start  # Runs on http://localhost:3000
```

The frontend will proxy API requests to `http://localhost:5000`.

### Backend Development

```bash
cd backend
python -m backend.app
```

Enable debug mode in `~/.pi_calendar/config.json`:
```json
{
  "server": {
    "debug": true
  }
}
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# With coverage
pytest --cov=backend --cov-report=html

# Frontend tests
cd frontend
npm test
```

### Code Quality

```bash
# Format code
black backend/
prettier --write frontend/src/

# Type checking
mypy backend/
npm run type-check  # Frontend

# Linting
flake8 backend/
npm run lint  # Frontend
```

## Deployment

### Production Configuration

1. Update `~/.pi_calendar/config.json`:
```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": false
  },
  "sync": {
    "interval_minutes": 30
  }
}
```

2. Build frontend:
```bash
cd frontend
npm run build
```

3. Run with production server:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 backend.app:app
```

### Raspberry Pi Deployment

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install python3-pip nodejs npm

# Clone and setup
git clone https://github.com/yourusername/digital-calendar.git
cd digital-calendar

# Use Docker (easier)
docker-compose up -d

# Or manual setup
# ... follow manual installation steps
```

### Systemd Service

Create `/etc/systemd/system/digital-calendar.service`:

```ini
[Unit]
Description=Digital Calendar Service
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/digital-calendar
ExecStart=/home/pi/digital-calendar/backend/.venv/bin/python -m backend.app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable digital-calendar
sudo systemctl start digital-calendar
```

## Troubleshooting

### Common Issues

**OAuth redirect errors**
- Ensure redirect URI matches exactly in Google Cloud Console
- Check that Flask is running on the correct host/port

**Apple calendar not syncing**
- Verify app-specific password is correct (16 characters)
- Check that two-factor authentication is enabled on Apple ID

**Events not showing**
- Check sync status: `GET /api/status`
- Trigger manual sync: `POST /api/sync`
- Verify date ranges in API requests

**Frontend not loading**
- Rebuild frontend: `cd frontend && npm run build`
- Check static files are in `frontend/build/`
- Verify Flask static folder configuration

### Logs

Logs are stored in `~/.pi_calendar/logs/`:
- `server.log` - Main application log
- `sync.log` - Synchronization events
- `error.log` - Error messages

View logs:
```bash
tail -f ~/.pi_calendar/logs/server.log
```

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Style

- **Python**: Follow PEP 8, use Black formatter
- **TypeScript**: Follow Airbnb style guide, use Prettier
- **Commits**: Use conventional commit messages

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Google Calendar API
- Apple CalDAV Protocol
- Flask web framework
- React frontend library
- All open source contributors

## Support

For support, please:
- Open an issue on GitHub
- Check existing issues for solutions
- Review documentation

## Roadmap

- [ ] Google Tasks integration
- [ ] Apple Reminders support
- [ ] Mobile app (React Native)
- [ ] Calendar sharing features
- [ ] Advanced filtering and search
- [ ] Recurring event editor
- [ ] Export to various formats (ICS, PDF)
- [ ] Email notifications
- [ ] Calendar analytics dashboard

---

Made with ❤️ by Adam Furrer
