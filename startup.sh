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
BLUE='\033[0;34m'
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

# Function to log info
log_info() {
    echo -e "${BLUE}[INFO] $1${NC}" | tee -a "$LOG_FILE"
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

# Check and install Node.js and npm if missing
if ! command_exists node || ! command_exists npm; then
    log_warning "Node.js or npm is not installed. Installing now..."
    
    # Ask user for installation method
    echo -e "${YELLOW}Choose Node.js installation method:${NC}"
    echo "1) NodeSource (Latest LTS - Recommended)"
    echo "2) apt (Simpler but may be older version)"
    read -p "Enter choice [1-2]: " choice
    
    case $choice in
        1)
            log_info "Installing Node.js via NodeSource..."
            if command_exists curl; then
                if curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - >> "$LOG_FILE" 2>&1; then
                    if sudo apt install -y nodejs >> "$LOG_FILE" 2>&1; then
                        log_success "Node.js and npm installed successfully via NodeSource"
                    else
                        log_error "Failed to install Node.js via apt"
                        exit 1
                    fi
                else
                    log_error "Failed to add NodeSource repository"
                    exit 1
                fi
            else
                log_error "curl is not installed. Install it with: sudo apt install curl"
                exit 1
            fi
            ;;
        2)
            log_info "Installing Node.js via apt..."
            if sudo apt update >> "$LOG_FILE" 2>&1; then
                if sudo apt install -y nodejs npm >> "$LOG_FILE" 2>&1; then
                    log_success "Node.js and npm installed successfully via apt"
                else
                    log_error "Failed to install Node.js and npm"
                    exit 1
                fi
            else
                log_error "Failed to update apt"
                exit 1
            fi
            ;;
        *)
            log_error "Invalid choice. Exiting."
            exit 1
            ;;
    esac
    
    # Verify installation
    if command_exists node && command_exists npm; then
        log_success "Node.js version: $(node --version)"
        log_success "npm version: $(npm --version)"
    else
        log_error "Node.js or npm installation verification failed"
        exit 1
    fi
else
    log_info "Node.js version: $(node --version)"
    log_info "npm version: $(npm --version)"
fi

# Check and install screen if missing
if ! command_exists screen; then
    log_warning "screen is not installed. Installing now..."
    if sudo apt update >> "$LOG_FILE" 2>&1 && sudo apt install -y screen >> "$LOG_FILE" 2>&1; then
        log_success "screen installed successfully"
    else
        log_error "Failed to install screen"
        exit 1
    fi
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

# Step 3: Upgrade pip
log "Upgrading pip..."
if pip install --upgrade pip >> "$LOG_FILE" 2>&1; then
    log_success "pip upgraded successfully"
else
    log_warning "Failed to upgrade pip, continuing anyway..."
fi

# Step 4: Install Python requirements
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

# Step 5: Install npm packages
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

# Step 6: Check if backend module exists
log "Checking backend module..."
if [ ! -d "backend" ] || [ ! -f "backend/app.py" ]; then
    log_warning "backend/app.py not found. Backend screen session may fail."
fi

# Step 7: Kill existing screen sessions if they exist
log "Checking for existing screen sessions..."
if screen -list | grep -q "digital_calendar_backend"; then
    log_warning "Killing existing digital_calendar_backend session"
    screen -S digital_calendar_backend -X quit
fi

if screen -list | grep -q "digital_calendar_frontend"; then
    log_warning "Killing existing digital_calendar_frontend session"
    screen -S digital_calendar_frontend -X quit
fi

# Give a moment for sessions to fully terminate
sleep 1

# Step 8: Start backend in screen session
log "Starting backend in screen session..."
if screen -dmS digital_calendar_backend bash -c "source $VENV_DIR/bin/activate && python -m backend.app"; then
    log_success "Backend screen session started"
else
    log_error "Failed to start backend screen session"
    exit 1
fi

# Give backend a moment to start
sleep 2

# Step 9: Start frontend in screen session
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
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          Setup completed successfully!                 ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Installed Versions:${NC}"
echo "  Node.js: $(node --version)"
echo "  npm: $(npm --version)"
echo "  Python: $(python3 --version)"
echo ""
echo -e "${BLUE}Screen Sessions:${NC}"
echo "  To view running sessions:"
echo "    screen -ls"
echo ""
echo "  To attach to backend:"
echo "    screen -r digital_calendar_backend"
echo ""
echo "  To attach to frontend:"
echo "    screen -r digital_calendar_frontend"
echo ""
echo "  To detach from a session: ${YELLOW}Ctrl+A, then D${NC}"
echo ""
echo -e "${BLUE}Log file:${NC} $LOG_FILE"
echo ""
