#!/bin/bash

# Script to set up and run digital calendar application
# Created: $(date +%Y-%m-%d)

# Configuration
LOG_FILE="setup_$(date +%Y%m%d_%H%M%S).log"
VENV_DIR="venv"
REQUIREMENTS_FILE="requirements.txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to log errors
log_error() {
    echo -e "${RED}[ERROR] $1${NC}" | tee -a "$LOG_FILE"
}

# Function to log success
log_success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}" | tee -a "$LOG_FILE"
}

# Function to log warnings
log_warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}" | tee -a "$LOG_FILE"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Start script
log "=== Starting Digital Calendar Setup ==="

# Check if Python3 is installed
if ! command_exists python3; then
    log_error "Python3 is not installed. Please install Python3 first."
    exit 1
fi

# Check if npm is installed
if ! command_exists npm; then
    log_error "npm is not installed. Please install Node.js and npm first."
    exit 1
fi

# Check if screen is installed
if ! command_exists screen; then
    log_error "screen is not installed. Please install screen first (sudo apt install screen)."
    exit 1
fi

# Step 1: Create Python virtual environment
log "Creating Python virtual environment..."
if python3 -m venv "$VENV_DIR" 2>> "$LOG_FILE"; then
    log_success "Virtual environment created successfully"
else
    log_error "Failed to create virtual environment"
    exit 1
fi

# Step 2: Activate virtual environment
log "Activating virtual environment..."
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
    log_success "Virtual environment activated"
else
    log_error "Failed to find activation script"
    exit 1
fi

# Step 3: Install Python requirements
log "Installing Python requirements..."
if [ -f "$REQUIREMENTS_FILE" ]; then
    if pip install -r "$REQUIREMENTS_FILE" >> "$LOG_FILE" 2>&1; then
        log_success "Python requirements installed successfully"
    else
        log_error "Failed to install Python requirements"
        exit 1
    fi
else
    log_warning "requirements.txt not found, skipping Python package installation"
fi

# Step 4: Install npm packages
log "Installing npm packages..."
if [ -f "package.json" ]; then
    if npm install >> "$LOG_FILE" 2>&1; then
        log_success "npm packages installed successfully"
    else
        log_error "Failed to install npm packages"
        exit 1
    fi
else
    log_warning "package.json not found, skipping npm installation"
fi

# Step 5: Check if backend module exists
log "Checking backend module..."
if [ ! -d "backend" ] || [ ! -f "backend/app.py" ]; then
    log_warning "backend/app.py not found. Backend screen session may fail."
fi

# Step 6: Kill existing screen sessions if they exist
log "Checking for existing screen sessions..."
if screen -list | grep -q "digital_calendar_backend"; then
    log_warning "Killing existing digital_calendar_backend session"
    screen -S digital_calendar_backend -X quit
fi

if screen -list | grep -q "digital_calendar_frontend"; then
    log_warning "Killing existing digital_calendar_frontend session"
    screen -S digital_calendar_frontend -X quit
fi

# Step 7: Start backend in screen session
log "Starting backend in screen session..."
if screen -dmS digital_calendar_backend bash -c "source $VENV_DIR/bin/activate && python -m backend.app"; then
    log_success "Backend screen session started"
else
    log_error "Failed to start backend screen session"
    exit 1
fi

# Give backend a moment to start
sleep 2

# Step 8: Start frontend in screen session
log "Starting frontend in screen session..."
if screen -dmS digital_calendar_frontend bash -c "npm start"; then
    log_success "Frontend screen session started"
else
    log_error "Failed to start frontend screen session"
    exit 1
fi

# Final status
log "=== Setup Complete ==="
log_success "Both services are running in screen sessions"
echo ""
echo -e "${GREEN}Setup completed successfully!${NC}"
echo ""
echo "To view running sessions:"
echo "  screen -ls"
echo ""
echo "To attach to backend:"
echo "  screen -r digital_calendar_backend"
echo ""
echo "To attach to frontend:"
echo "  screen -r digital_calendar_frontend"
echo ""
echo "To detach from a session: Ctrl+A, then D"
echo ""
echo "Log file: $LOG_FILE"