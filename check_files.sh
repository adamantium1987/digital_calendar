#!/bin/bash
# Helper script to check which files still need to be copied

PROJECT_DIR="/Users/adamfurrer/PycharmProjects/digital_calendar"

echo "🔍 Checking Pi Calendar System File Status"
echo "==========================================="
echo ""

check_file() {
    local file=$1
    local artifact=$2
    
    if [ -f "$PROJECT_DIR/$file" ]; then
        lines=$(wc -l < "$PROJECT_DIR/$file")
        if [ "$lines" -gt 50 ]; then
            echo "✅ $file ($lines lines) - COMPLETE"
        else
            echo "⚠️  $file ($lines lines) - NEEDS CODE from $artifact"
        fi
    else
        echo "❌ $file - MISSING (copy from $artifact)"
    fi
}

echo "Server Files:"
check_file "server/sync/sync_engine.py" "fixed_sync_engine"
check_file "server/sync/cache_manager.py" "fixed_cache_manager"
check_file "server/app.py" "fixed_flask_app"
check_file "server/api/routes.py" "fixed_api_routes"
check_file "server/calendar_sources/base.py" "google_calendar (part 1)"
check_file "server/calendar_sources/google_cal.py" "google_calendar"
check_file "server/calendar_sources/apple_cal.py" "apple_caldav"
check_file "server/config/settings.py" "settings (in conversation)"

echo ""
echo "Client Files:"
check_file "client/display_app.py" "fixed_display_app"
check_file "client/utils/api_client.py" "fixed_api_client"
check_file "client/ui/calendar_view.py" "calendar_view"
check_file "client/ui/touch_handler.py" "calendar_view (part 2)"

echo ""
echo "==========================================="
echo ""
echo "To copy a file from Claude:"
echo "1. Find the artifact in the conversation"
echo "2. Copy the code"
echo "3. Paste into the file using your IDE"
echo ""
echo "Or create the file manually:"
echo "  nano $PROJECT_DIR/server/sync/sync_engine.py"
echo ""
