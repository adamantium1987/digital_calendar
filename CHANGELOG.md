# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive TypeScript configuration with strict type checking
- ESLint and Prettier configuration for code quality
- Improved API utilities with retry logic and timeout handling
- Custom React hooks for data fetching (`useApiGet`, `useApiPost`, `useApiPolling`)
- Environment variable management with `.env` files
- Docker and Docker Compose configuration
- GitHub Actions CI/CD pipeline
- Comprehensive test suite (Python and TypeScript)
- Pre-commit hooks for code quality
- Pyproject.toml for Python project configuration
- Comprehensive README with setup instructions
- MIT License

### Changed
- Fixed OAuthError import issue in Google Calendar integration
- Replaced bare except clauses with specific exception types
- Improved requirements.txt with comments
- Enhanced error handling throughout the codebase

### Fixed
- Bare exception handling in utility functions
- Missing type imports in Python files

## [1.0.0] - 2025-01-XX

### Added
- Initial release
- Google Calendar integration via OAuth2
- Apple iCloud Calendar integration via CalDAV
- Task chart management system
- React frontend with multiple calendar views
- Flask REST API backend
- SQLite-based caching layer
- Automatic synchronization with configurable intervals
- Web-based account setup and management
- Responsive design for mobile and desktop

### Features
- Multi-account support for Google and Apple calendars
- Day, week, and month calendar views
- Task tracking with completion status
- Real-time sync status monitoring
- Encrypted credential storage
- Rate limiting for API protection
- Background sync engine
- Event color coding by account

[Unreleased]: https://github.com/yourusername/digital-calendar/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/yourusername/digital-calendar/releases/tag/v1.0.0
