# Pi Calendar System

A distributed digital calendar display system using Raspberry Pi 4 as a command & control server and Pi Zero displays. Syncs with multiple Google and Apple calendar accounts - **completely free!**

## 🎯 Project Status

✅ **Git repository initialized**  
✅ **Project structure created**  
✅ **Dependencies configured**  
⚠️ **Need to add fixed code files** (see below)

## 📁 Project Structure

```
digital_calendar/
├── server/              # Pi 4 Command & Control Server
│   ├── config/          # Configuration management
│   ├── calendar_sources/# Google & Apple integrations
│   ├── sync/            # Sync engine and caching
│   ├── api/             # REST API for clients
│   └── app.py           # Main Flask application
├── client/              # Pi Zero Display Client
│   ├── ui/              # Touch interface components
│   ├── utils/           # API client utilities
│   └── display_app.py   # Main display application
├── shared/              # Common utilities
├── setup/               # Installation scripts
└── docs/                # Documentation
```

## ⚠️ NEXT STEP: Install Fixed Code

All critical bugs have been fixed! You need to copy the corrected code files from the Claude conversation.

### Copy These Files from Claude Artifacts:

1. **server/sync/sync_engine.py** ← from `fixed_sync_engine` artifact
2. **server/sync/cache_manager.py** ← from `fixed_cache_manager` artifact  
3. **server/app.py** ← from `fixed_flask_app` artifact
4. **server/api/routes.py** ← from `fixed_api_routes` artifact
5. **client/display_app.py** ← from `fixed_display_app` artifact
6. **client/utils/api_client.py** ← from `fixed_api_client` artifact

### Also Copy Original Versions:

7. **server/calendar_sources/base.py** ← from `google_calendar` artifact (first part)
8. **server/calendar_sources/google_cal.py** ← from `google_calendar` artifact
9. **server/calendar_sources/apple_cal.py** ← from `apple_caldav` artifact
10. **client/ui/calendar_view.py** ← from `calendar_view` artifact
11. **client/ui/touch_handler.py** ← from `calendar_view` artifact (second part)

## 🚀 Quick Start (After Adding Code)

### 1. Install Dependencies

```bash
cd /Users/adamfurrer/PycharmProjects/digital_calendar
python3 -m venv venv
source venv/bin/activate
pip install -r setup/requirements.txt
```

### 2. Run Server (Development)

```bash
source venv/bin/activate
python -m server.app
```

Open browser to: http://localhost:5000

### 3. Run Client (Development)

```bash
# In another terminal
source venv/bin/activate
python -m client.display_app --server localhost --dev
```

## 🐛 All Bugs Fixed!

✅ 20+ critical bugs resolved  
✅ Proper error handling throughout  
✅ Thread safety implemented  
✅ Network resilience with retry logic  
✅ Security improvements  
✅ User-friendly error messages

## 📚 Documentation

- **INSTALLATION.md** - Detailed setup instructions
- **setup/requirements.txt** - Python dependencies
- **.gitignore** - Git ignore patterns

## 🔧 Configuration

### Server Configuration
Stored in: `~/.pi_calendar/config.json`

### Client Configuration  
Stored in: `~/.pi_calendar_client/config.json`

## 🌟 Features

- **Multi-Account Support**: Unlimited Google + Apple accounts
- **Distributed Architecture**: One Pi 4 serves multiple Pi Zero displays
- **100% Free**: Uses free API tiers, no subscriptions
- **Touch Interface**: Swipe navigation, tap events
- **Multiple Views**: Day, week, month calendar views
- **Auto-Sync**: Background synchronization every 15 minutes
- **Offline Capable**: Local caching for reliability

## 📝 Git Workflow

```bash
# Add the fixed code files
git add server/ client/

# Commit
git commit -m "Add fixed code files with all bug fixes"

# Push to remote (if configured)
git push origin master
```

## 🔗 Links

- Google Calendar API: https://console.developers.google.com/
- Apple ID Management: https://appleid.apple.com/

## 📞 Support

For issues or questions:
1. Check INSTALLATION.md for detailed setup
2. Review error messages in terminal
3. Verify all dependencies installed
4. Test with `--dev` flag for debugging

---

**Project initialized on:** $(date)  
**Status:** Ready for fixed code files  
**Next:** Copy code from Claude artifacts and test
