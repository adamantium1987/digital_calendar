#!/bin/bash
# setup/install_server.sh
# Pi 4 Calendar Server Installation Script

set -e

echo "=========================================="
echo "Pi Calendar Server Installation (Pi 4)"
echo "=========================================="

# Check if running on Pi 4
if ! grep -q "Raspberry Pi 4" /proc/cpuinfo; then
    echo "Warning: This script is designed for Raspberry Pi 4"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required system packages
echo "Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    sqlite3 \
    curl \
    nginx \
    supervisor

# Create application directory
APP_DIR="/opt/pi-calendar"
echo "Creating application directory: $APP_DIR"
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# Copy application files
echo "Installing application files..."
cp -r server/ $APP_DIR/
cp -r shared/ $APP_DIR/
cp setup/requirements.txt $APP_DIR/

# Create Python virtual environment
echo "Creating Python virtual environment..."
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create configuration directory
echo "Setting up configuration..."
CONFIG_DIR="$HOME/.pi_calendar"
mkdir -p $CONFIG_DIR
chmod 700 $CONFIG_DIR

# Create systemd service
echo "Creating systemd service..."
sudo tee /etc/systemd/system/pi-calendar-server.service > /dev/null <<EOF
[Unit]
Description=Pi Calendar Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/python -m server.app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
echo "Enabling Pi Calendar service..."
sudo systemctl daemon-reload
sudo systemctl enable pi-calendar-server
sudo systemctl start pi-calendar-server

# Configure nginx (optional reverse proxy)
echo "Configuring nginx..."
sudo tee /etc/nginx/sites-available/pi-calendar > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/pi-calendar /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl restart nginx

# Get IP address
IP_ADDRESS=$(hostname -I | awk '{print $1}')

echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
echo "Pi Calendar Server is running on:"
echo "  Web Interface: http://$IP_ADDRESS"
echo "  API Endpoint:  http://$IP_ADDRESS/api"
echo ""
echo "Next steps:"
echo "1. Open web interface to configure accounts"
echo "2. Install client on Pi Zero displays"
echo "3. Configure Pi Zero clients with server IP: $IP_ADDRESS"
echo ""
echo "Service management:"
echo "  Status: sudo systemctl status pi-calendar-server"
echo "  Logs:   sudo journalctl -u pi-calendar-server -f"
echo "  Stop:   sudo systemctl stop pi-calendar-server"
echo "  Start:  sudo systemctl start pi-calendar-server"
echo "=========================================="

# Create client configuration template
echo "Creating client configuration template..."
mkdir -p $CONFIG_DIR/client-configs
cat > $CONFIG_DIR/client-configs/pi-zero-config.json <<EOF
{
  "server_host": "$IP_ADDRESS",
  "server_port": 5000,
  "refresh_interval": 300,
  "connection_timeout": 10,
  "fullscreen": true,
  "development_mode": false
}
EOF

#!/bin/bash
# setup/install_client.sh
# Pi Zero Calendar Display Client Installation Script

set -e

echo "=========================================="
echo "Pi Calendar Display Client (Pi Zero)"
echo "=========================================="

# Check if running on Pi Zero
if grep -q "Raspberry Pi Zero" /proc/cpuinfo; then
    echo "✓ Detected Raspberry Pi Zero"
else
    echo "Warning: This script is designed for Raspberry Pi Zero"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Get server IP from user
echo "Enter the IP address of your Pi 4 Calendar Server:"
read -p "Server IP: " SERVER_IP

if [[ ! $SERVER_IP =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: Invalid IP address format"
    exit 1
fi

# Test connection to server
echo "Testing connection to server..."
if ! curl -s --connect-timeout 5 "http://$SERVER_IP:5000/api/health" > /dev/null; then
    echo "Warning: Cannot connect to server at $SERVER_IP:5000"
    echo "Make sure the server is running and accessible"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages for Pi Zero
echo "Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-tk \
    git \
    curl \
    xinit \
    xserver-xorg \
    matchbox-window-manager \
    chromium-browser \
    unclutter

# Create application directory
APP_DIR="/opt/pi-calendar-client"
echo "Creating application directory: $APP_DIR"
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# Copy application files
echo "Installing application files..."
cp -r client/ $APP_DIR/
cp -r shared/ $APP_DIR/

# Create Python virtual environment
echo "Creating Python virtual environment..."
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies (minimal for Pi Zero)
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install requests

# Create configuration
echo "Setting up configuration..."
CONFIG_DIR="$HOME/.pi_calendar_client"
mkdir -p $CONFIG_DIR

cat > $CONFIG_DIR/config.json <<EOF
{
  "server_host": "$SERVER_IP",
  "server_port": 5000,
  "refresh_interval": 300,
  "connection_timeout": 10,
  "fullscreen": true,
  "development_mode": false
}
EOF

# Create startup script
echo "Creating startup script..."
cat > $APP_DIR/start_display.sh <<EOF
#!/bin/bash
cd $APP_DIR
source venv/bin/activate

# Wait for network
echo "Waiting for network..."
while ! ping -c 1 $SERVER_IP &> /dev/null; do
    sleep 5
done

echo "Starting Pi Calendar Display..."
python -m client.display_app
EOF

chmod +x $APP_DIR/start_display.sh

# Create systemd service for auto-start
echo "Creating systemd service..."
sudo tee /etc/systemd/system/pi-calendar-display.service > /dev/null <<EOF
[Unit]
Description=Pi Calendar Display
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
User=$USER
Environment=DISPLAY=:0
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/start_display.sh
Restart=always
RestartSec=10

[Install]
WantedBy=graphical-session.target
EOF

# Configure auto-login and X11 startup
echo "Configuring auto-login..."
sudo systemctl set-default graphical.target

# Configure .xinitrc for automatic display startup
cat > $HOME/.xinitrc <<EOF
#!/bin/bash
# Hide cursor
unclutter -idle 0 &

# Start window manager
matchbox-window-manager &

# Wait a moment
sleep 2

# Start calendar display
$APP_DIR/start_display.sh
EOF

chmod +x $HOME/.xinitrc

# Configure auto-login
sudo tee /etc/systemd/system/getty@tty1.service.d/autologin.conf > /dev/null <<EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin $USER --noclear %I \$TERM
EOF

# Enable display service
echo "Enabling display service..."
sudo systemctl daemon-reload
sudo systemctl enable pi-calendar-display

# Configure display rotation (optional)
echo "Do you need to rotate the display?"
echo "1) No rotation (0°)"
echo "2) 90° clockwise"
echo "3) 180° (upside down)"
echo "4) 270° clockwise (90° counter-clockwise)"
read -p "Select option [1-4]: " ROTATION

case $ROTATION in
    2) DISPLAY_ROTATE=1 ;;
    3) DISPLAY_ROTATE=2 ;;
    4) DISPLAY_ROTATE=3 ;;
    *) DISPLAY_ROTATE=0 ;;
esac

if [[ $DISPLAY_ROTATE -ne 0 ]]; then
    echo "display_rotate=$DISPLAY_ROTATE" | sudo tee -a /boot/config.txt
    echo "Display rotation configured. Reboot required to take effect."
fi

echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
echo "Pi Calendar Display Client is configured."
echo ""
echo "Configuration:"
echo "  Server: $SERVER_IP:5000"
echo "  Config: $CONFIG_DIR/config.json"
echo "  App Dir: $APP_DIR"
echo ""
echo "The display will start automatically on boot."
echo ""
echo "Manual control:"
echo "  Test now: $APP_DIR/start_display.sh"
echo "  Status:   sudo systemctl status pi-calendar-display"
echo "  Logs:     sudo journalctl -u pi-calendar-display -f"
echo ""
echo "Reboot now to start the display:"
echo "  sudo reboot"
echo "=========================================="

# Test display connection
echo ""
echo "Testing connection to calendar server..."
if python3 -c "
import sys
sys.path.append('$APP_DIR')
from client.utils.api_client import test_server_connection
if test_server_connection('$SERVER_IP', 5000):
    print('✓ Successfully connected to calendar server')
else:
    print('✗ Could not connect to calendar server')
    print('Please check server is running and network connection')
"; then
    echo "Connection test completed."
else
    echo "Note: Install client dependencies first with: cd $APP_DIR && source venv/bin/activate && pip install requests"
fi $CONFIG_DIR/client-configs/pi-zero-config.json"


