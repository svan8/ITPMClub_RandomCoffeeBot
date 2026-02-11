# Quick Reference - Bot Management Commands

## After SSH into your EC2 instance (ubuntu@<IP>)

### View Bot Status
```bash
sudo systemctl status random-coffee-bot.service
```

### View Live Logs
```bash
tail -f /opt/random-coffee-bot/logs/bot.log
```

### View Last 50 Log Lines
```bash
tail -50 /opt/random-coffee-bot/logs/bot.log
```

### Restart the Bot
```bash
sudo systemctl restart random-coffee-bot.service
```

### Stop the Bot
```bash
sudo systemctl stop random-coffee-bot.service
```

### Start the Bot
```bash
sudo systemctl start random-coffee-bot.service
```

### View Full System Logs
```bash
journalctl -u random-coffee-bot.service -n 100 --no-pager
```

### Follow System Logs in Real-time
```bash
journalctl -u random-coffee-bot.service -f
```

### Edit Configuration
```bash
sudo nano /opt/random-coffee-bot/.env
# After editing, restart the bot:
sudo systemctl restart random-coffee-bot.service
```

### View Environment Variables
```bash
cat /opt/random-coffee-bot/.env
```

### Backup Data
```bash
tar -czf ~/backup-$(date +%Y%m%d-%H%M%S).tar.gz /opt/random-coffee-bot/data/
ls -lah ~/backup-*.tar.gz
```

### Check System Resources
```bash
free -h              # Memory
df -h               # Disk space
top -b -n 1 | head -20  # CPU usage
```

### Uninstall/Remove Service
```bash
sudo systemctl stop random-coffee-bot.service
sudo systemctl disable random-coffee-bot.service
sudo rm /etc/systemd/system/random-coffee-bot.service
sudo systemctl daemon-reload
```

---

## From Your Local Machine

### SSH to EC2 Instance
```bash
ssh -i your-key.pem ubuntu@<PUBLIC_IP>
```

### Copy Files to EC2
```bash
scp -i your-key.pem /path/to/file ubuntu@<PUBLIC_IP>:/opt/random-coffee-bot/
```

### Download Backup from EC2
```bash
scp -i your-key.pem ubuntu@<PUBLIC_IP>:/opt/random-coffee-bot/data/* ./
```

### Execute Command on EC2 without SSH Shell
```bash
ssh -i your-key.pem ubuntu@<PUBLIC_IP> "sudo systemctl status random-coffee-bot.service"
```

---

## Troubleshooting

### Bot keeps restarting?
Check logs for errors: `tail -50 /opt/random-coffee-bot/logs/bot.log`

### Module not found error?
Activate venv and reinstall: 
```bash
cd /opt/random-coffee-bot
source venv/bin/activate
pip install -r requirements.txt
```

### Running out of disk space?
```bash
df -h
sudo apt autoremove -y
```

### Service won't start?
```bash
sudo systemctl start random-coffee-bot.service
sudo systemctl status random-coffee-bot.service
journalctl -u random-coffee-bot.service -n 20
```
