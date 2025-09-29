#!/bin/bash
# Quick setup script to create all project files

PROJECT_DIR="/Users/adamfurrer/PycharmProjects/digital_calendar"

echo "Setting up Pi Calendar System in $PROJECT_DIR"
cd "$PROJECT_DIR"

# Create requirements.txt
cat > setup/requirements.txt << 'EOF'
# Server Dependencies (Pi 4)
flask==2.3.3
google-auth==2.23.3
google-auth-oauthlib==1.1.0
google-api-python-client==2.103.0
caldav==1.3.6
requests==2.31.0
cryptography==41.0.4
apscheduler==3.10.4
vobject==0.9.6.1

# Client Dependencies (Pi Zero)
# requests already included above
# tkinter is built into Python
EOF

# Create .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Config and credentials
.pi_calendar/
.pi_calendar_client/
*.enc
.key

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Database
*.db
*.sqlite
*.sqlite3
EOF

echo "✓ Setup files created"
echo "✓ Project structure ready"
echo ""
echo "Next steps:"
echo "1. Install dependencies: pip install -r setup/requirements.txt"
echo "2. Run server: python -m server.app"
echo "3. Run client: python -m client.display_app --server YOUR_SERVER_IP"
