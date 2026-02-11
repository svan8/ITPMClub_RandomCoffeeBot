# AWS Deployment Guide for Random Coffee Bot

## Prerequisites

Before starting, ensure you have:
- AWS Account with appropriate permissions
- Telegram Bot Token (from @BotFather)
- Telegram Chat ID for your group
- SSH client installed locally

---

## Step 1: Create and Configure EC2 Instance

### 1.1 Launch EC2 Instance

1. Go to [AWS EC2 Console](https://console.aws.amazon.com/ec2/)
2. Click **Launch Instance**
3. **Select AMI**: Choose **Ubuntu Server 24.04 LTS** (Free Tier eligible)
4. **Instance Type**: Select `t2.micro` (Free Tier eligible) or `t2.small` for better performance
5. **Network Settings**:
   - Create or select a VPC
   - Enable auto-assign public IP
6. **Storage**: 20 GB gp3 (default is fine)
7. **Security Group**:
   - Create a new security group
   - Allow SSH (port 22) from your IP
   - Outbound: Allow all (bot needs internet for Telegram)
8. **Key Pair**: Create or use existing `.pem` file
9. **Launch Instance**

### 1.2 Get Instance Details

- Copy the **Public IPv4 address** of your instance
- Ensure your `.pem` file has correct permissions: `chmod 400 your-key.pem`

---

## Step 2: Connect to Instance via SSH

```bash
ssh -i your-key.pem ubuntu@<PUBLIC_IPV4_ADDRESS>
```

Once connected, you're in the instance terminal. Continue with the following steps there.

---

## Step 3: Setup Bot Environment

### 3.1 Update System

```bash
sudo apt update
sudo apt upgrade -y
```

### 3.2 Install Python 3.10+

```bash
sudo apt install -y python3.10 python3.10-venv python3-pip git
```

### 3.3 Create Application Directory

```bash
sudo mkdir -p /opt/random-coffee-bot
sudo chown ubuntu:ubuntu /opt/random-coffee-bot
cd /opt/random-coffee-bot
```

### 3.4 Clone Repository

```bash
git clone https://github.com/svan8/ITPMClub_RandomCoffeeBot.git .
# Or upload your files via SCP
```

If using SCP from your local machine:
```bash
scp -i your-key.pem -r /path/to/RandomCoffeBot.py ubuntu@<PUBLIC_IPV4_ADDRESS>:/opt/random-coffee-bot/
```

### 3.5 Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3.6 Install Python Dependencies

```bash
pip install --upgrade pip
pip install python-telegram-bot==13.15 schedule
```

---

## Step 4: Configure Environment Variables

### 4.1 Create Environment File

```bash
sudo tee /opt/random-coffee-bot/.env > /dev/null <<EOF
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
POLL_DAY=monday
POLL_TIME=10:00
PAIRING_DAY=wednesday
PAIRING_TIME=10:00
DATA_DIR=/opt/random-coffee-bot/data
EOF
```

Replace the values with your actual credentials.

### 4.2 Secure the File

```bash
chmod 600 /opt/random-coffee-bot/.env
```

### 4.3 Test the Bot Manually

```bash
source venv/bin/activate
set -a
source .env
set +a
python RandomCoffeBot.py
```

If it runs without errors, press `Ctrl+C` to stop.

---

## Step 5: Setup Systemd Service

### 5.1 Create Service File

```bash
sudo tee /etc/systemd/system/random-coffee-bot.service > /dev/null <<EOF
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

# Standard output/error logging
StandardOutput=append:/opt/random-coffee-bot/logs/bot.log
StandardError=append:/opt/random-coffee-bot/logs/bot.log

[Install]
WantedBy=multi-user.target
EOF
```

### 5.2 Create Logs Directory

```bash
mkdir -p /opt/random-coffee-bot/logs
```

### 5.3 Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable random-coffee-bot.service
sudo systemctl start random-coffee-bot.service
```

### 5.4 Check Status

```bash
sudo systemctl status random-coffee-bot.service
```

View logs:
```bash
tail -f /opt/random-coffee-bot/logs/bot.log
```

---

## Step 6: Verify Deployment

1. **Check bot is running**:
   ```bash
   sudo systemctl status random-coffee-bot.service
   ```

2. **Send a test message** to your Telegram group to verify the bot responds

3. **Check logs** for any errors:
   ```bash
   tail -30 /opt/random-coffee-bot/logs/bot.log
   ```

---

## Step 7: Useful Commands for Managing the Bot

### View Logs
```bash
tail -f /opt/random-coffee-bot/logs/bot.log
```

### Stop the Bot
```bash
sudo systemctl stop random-coffee-bot.service
```

### Start the Bot
```bash
sudo systemctl start random-coffee-bot.service
```

### Restart the Bot
```bash
sudo systemctl restart random-coffee-bot.service
```

### View Recent Logs
```bash
journalctl -u random-coffee-bot.service -n 50 --no-pager
```

### Full Service Logs
```bash
journalctl -u random-coffee-bot.service -f
```

---

## Step 8: (Optional) Setup Automated Updates

To keep your instance secure, enable automatic security updates:

```bash
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## Security Best Practices

1. **Restrict SSH Access**: Update security group to only allow SSH from your IP
2. **Use IAM Roles**: If accessing AWS services, use IAM roles instead of credentials
3. **Rotate Bot Token**: Periodically rotate your Telegram bot token
4. **Monitor Logs**: Regularly check logs for errors or unauthorized access
5. **Enable CloudWatch**: Set up AWS CloudWatch for monitoring and alerts
6. **Backup Data**: Regularly backup your `data/` directory containing participated users

---

## Troubleshooting

### Bot won't start
- Check credentials: `cat /opt/random-coffee-bot/.env`
- Check logs: `journalctl -u random-coffee-bot.service -n 20`
- Test manually: `source venv/bin/activate && python RandomCoffeBot.py`

### Bot keeps crashing
- Check for syntax errors in the bot code
- Ensure all dependencies are installed: `pip list`
- Check disk space: `df -h`
- Check memory: `free -h`

### Can't connect via SSH
- Verify security group allows port 22
- Check public IP is correct
- Ensure key permissions: `chmod 400 your-key.pem`

---

## Data Persistence

Your bot data (polls, participants) is stored in `/opt/random-coffee-bot/data/`:
- `current_poll_id.json`: Current poll information
- `participants.json`: Weekly participants

**Backup regularly**:
```bash
tar -czf ~/random-coffee-backup-$(date +%Y%m%d).tar.gz /opt/random-coffee-bot/data/
```

---

## Estimated AWS Costs

- **EC2 t2.micro**: FREE (12 months with Free Tier)
- **EC2 t2.small**: ~$10/month
- **Storage**: Minimal (included in Free Tier)
- **Data Transfer**: Minimal (included in Free Tier)

---

## Next Steps

1. Follow the deployment steps above
2. Monitor the bot for 24-48 hours
3. Verify the bot sends polls and pairings correctly
4. Set up monitoring/alerts (optional but recommended)
