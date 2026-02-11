#!/bin/bash

# Random Coffee Bot - AWS Deployment Script
# This script automates the deployment of the bot to an EC2 instance
# Run on a freshly created Ubuntu 24.04 LTS EC2 instance using:
# curl -fsSL https://raw.github.com/svan8/ITPMClub_RandomCoffeeBot/main/deploy.sh | bash

set -e

echo "================================"
echo "Random Coffee Bot - AWS Setup"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${GREEN}▶ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check if running as ubuntu user
if [ "$USER" != "ubuntu" ]; then
    print_error "This script must be run as the ubuntu user"
    exit 1
fi

# Step 1: Update system
print_step "Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Step 2: Install dependencies
print_step "Installing Python and dependencies..."
sudo apt install -y python3.10 python3.10-venv python3-pip git curl

# Step 3: Setup application directory
print_step "Creating application directory..."
sudo mkdir -p /opt/random-coffee-bot
sudo chown ubuntu:ubuntu /opt/random-coffee-bot
cd /opt/random-coffee-bot

# Step 4: Clone or setup repository
if [ -d ".git" ]; then
    print_step "Pulling latest code..."
    git pull origin main
else
    print_step "Cloning repository..."
    git clone https://github.com/svan8/ITPMClub_RandomCoffeeBot.git . || print_warning "Could not clone repo"
fi

# Step 5: Create virtual environment
print_step "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Step 6: Install Python packages
print_step "Installing Python dependencies..."
pip install --upgrade pip
pip install python-telegram-bot==13.15 schedule

# Step 7: Create directories
print_step "Creating data and logs directories..."
mkdir -p /opt/random-coffee-bot/data
mkdir -p /opt/random-coffee-bot/logs

# Step 8: Create environment file
print_step "Creating environment configuration file..."
if [ ! -f "/opt/random-coffee-bot/.env" ]; then
    sudo tee /opt/random-coffee-bot/.env > /dev/null <<'EOF'
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Schedule Configuration (24-hour format)
POLL_DAY=monday
POLL_TIME=10:00
PAIRING_DAY=wednesday
PAIRING_TIME=10:00

# Data Directory
DATA_DIR=/opt/random-coffee-bot/data
EOF
    sudo chmod 600 /opt/random-coffee-bot/.env
    print_warning "Configuration file created at /opt/random-coffee-bot/.env"
    print_warning "⚠️  IMPORTANT: Edit the .env file with your actual credentials:"
    print_warning "   sudo nano /opt/random-coffee-bot/.env"
else
    print_warning ".env file already exists, skipping..."
fi

# Step 9: Create systemd service
print_step "Creating systemd service..."
sudo tee /etc/systemd/system/random-coffee-bot.service > /dev/null <<'EOF'
[Unit]
Description=Random Coffee Bot Telegram Service
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/random-coffee-bot
Environment="PATH=/opt/random-coffee-bot/venv/bin"
EnvironmentFile=/opt/random-coffee-bot/.env
ExecStart=/opt/random-coffee-bot/venv/bin/python /opt/random-coffee-bot/RandomCoffeBot.py
Restart=always
RestartSec=10
StandardOutput=append:/opt/random-coffee-bot/logs/bot.log
StandardError=append:/opt/random-coffee-bot/logs/bot.log

[Install]
WantedBy=multi-user.target
EOF

# Step 10: Enable and start service
print_step "Enabling and starting the service..."
sudo systemctl daemon-reload
sudo systemctl enable random-coffee-bot.service

# Don't start yet - user needs to configure credentials first
print_warning "Service created but NOT started (credentials needed first)"

# Step 11: Setup automatic security updates
print_step "Configuring automatic security updates..."
sudo apt install -y unattended-upgrades
echo 'Unattended-Upgrade::Allowed-Origins "${distro_id}:${distro_codename}-security";' | sudo tee -a /etc/apt/apt.conf.d/50unattended-upgrades > /dev/null

echo ""
echo "================================"
echo -e "${GREEN}Setup Complete!${NC}"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Edit configuration file:"
echo "   ${YELLOW}sudo nano /opt/random-coffee-bot/.env${NC}"
echo "2. Start the bot service:"
echo "   ${YELLOW}sudo systemctl start random-coffee-bot.service${NC}"
echo "3. Check status:"
echo "   ${YELLOW}sudo systemctl status random-coffee-bot.service${NC}"
echo "4. View logs:"
echo "   ${YELLOW}tail -f /opt/random-coffee-bot/logs/bot.log${NC}"
echo ""
