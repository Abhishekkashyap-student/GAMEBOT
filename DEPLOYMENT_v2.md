# 🚀 AXL GAME BOT v2.0 - DEPLOYMENT GUIDE

## ⚡ QUICK SETUP (5 Minutes)

### Step 1: Set Up Environment
```bash
cd /workspaces/GAMEBOT

# Create .env file
cat > .env << 'EOF'
BOT_TOKEN=your_telegram_bot_token_here
OWNER_ID=your_telegram_user_id_here
EOF

# Or use existing environment variables
export BOT_TOKEN="your_token"
export OWNER_ID="your_id"
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run Bot
```bash
python bot.py
```

**That's it! Bot is running!** 🎮

---

## 📱 TESTING IN GROUP

### Add Bot to Group:
1. Click "Add to Group" button in bot's `/start` message
2. OR invite bot manually to a group

### Initialize in Group:
```
User: /startgames
Bot: ✅ Games initialized!
```

### Start Using Commands:
```
/daily              → Claim 500₹
/balance            → Check balance
/trivia             → Play trivia game
/kill (reply)       → Kill someone
/leaderboard        → Top 15 users
/help               → All commands
```

**Commands work immediately after /startgames!**

---

## 👑 OWNER SETTINGS

### View Settings:
```bash
/settings
```

### Change Settings:
```bash
/settings daily_reward 600        # Change daily from 500 to 600
/settings max_bet 15000           # Change max bet from 10k to 15k
/settings steal_success_rate 0.6  # Change steal chance to 60%
```

### Available Settings:
- `daily_reward` - Daily claim amount (default: 500)
- `revive_cost` - Revive user cost (default: 200)
- `protect_cost` - Protection cost (default: 200)
- `kill_reward_min` - Min kill reward (default: 90)
- `kill_reward_max` - Max kill reward (default: 150)
- `max_bet` - Maximum slot bet (default: 10000)
- `min_bet` - Minimum slot bet (default: 1)
- `steal_success_rate` - Steal success probability (default: 0.5)
- `ui_theme` - UI theme (default: "professional")
- `bot_name` - Bot name for branding (default: "AXL GAME BOT")

---

## 🔄 DATABASE UPDATES

### First Run:
```bash
# First time, bot automatically creates everything
$ python bot.py

# Database created with:
# - users table (existing)
# - groups table (NEW!)
# - All necessary schemas
```

### Backup Database:
```bash
# Before updates, backup existing data
cp axlbot.db axlbot.db.backup
```

### Reset If Needed:
```bash
# Wipe and start fresh
rm axlbot.db
python bot.py  # Creates new empty database
```

---

## 🎯 GROUP WORKFLOW

### One-Time Setup:
```
1. Add bot to group
2. Admin: /startgames (registers in database)
3. Done! All commands enabled forever
```

### Group Cancellation:
```
Admin: /stopgames  (unregisters from database)
```

### After Bot Restart:
```
✅ All previously registered groups auto-load
✅ Commands work immediately
✅ No re-registration needed
```

### Multiple Groups:
```
Each group registered independently
Commands work in all registered groups
Owner can customize for all
```

---

## 🌐 DEPLOYMENT OPTIONS

### Option 1: Local/VPS with systemd

**Create service file:**
```bash
sudo nano /etc/systemd/system/axlbot.service
```

**Paste:**
```ini
[Unit]
Description=AXL GAME BOT Service
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/GAMEBOT
Environment=BOT_TOKEN=your_token_here
Environment=OWNER_ID=your_owner_id_here
ExecStart=/usr/bin/python3 bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable axlbot
sudo systemctl start axlbot
sudo journalctl -u axlbot -f  # View logs
```

### Option 2: Docker

**Build:**
```bash
docker build -t axl-bot:latest .
```

**Run:**
```bash
docker run \
  -e BOT_TOKEN="$BOT_TOKEN" \
  -e OWNER_ID="$OWNER_ID" \
  -v $(pwd)/axlbot.db:/app/axlbot.db \
  axl-bot:latest
```

### Option 3: Koyeb (Serverless)

**Set environment variables in Koyeb:**
- `BOT_TOKEN` = Your bot token
- `OWNER_ID` = Your owner ID

**Deploy using koyeb.yml manifest**

---

## 🔍 VERIFICATION CHECKLIST

- [ ] Bot token set correctly
- [ ] Owner ID configured
- [ ] Dependencies installed
- [ ] Bot starts without errors
- [ ] Can add to group
- [ ] /startgames works
- [ ] Commands respond
- [ ] /settings accessible (owner)
- [ ] Group persists on restart
- [ ] All games functional

---

## 🐛 TROUBLESHOOTING

### Bot Won't Start
```bash
# Check token
echo $BOT_TOKEN

# Check Python version (need 3.8+)
python --version

# Check dependencies
pip install -r requirements.txt
```

### Commands Don't Work
```bash
# Make sure to run /startgames first
# Bot won't respond until group is registered

# Check bot is in group (as member)
# Check bot has message permissions
```

### Database Error
```bash
# Reset database
rm axlbot.db
python bot.py  # Creates fresh

# Or restore backup
cp axlbot.db.backup axlbot.db
```

### Groups Not Loading After Restart
```bash
# Check database exists
ls -l axlbot.db

# Check database has groups table
sqlite3 axlbot.db "SELECT COUNT(*) FROM groups;"

# Should return number of registered groups
```

### Settings Not Saving
```bash
# Check permissions
ls -l bot_settings.json

# Check JSON syntax
cat bot_settings.json

# Reset if corrupted
rm bot_settings.json
python bot.py
```

---

## 📊 MONITORING

### View Bot Logs:
```bash
# Systemd
sudo journalctl -u axlbot -n 50 -f

# Docker
docker logs -f container_id

# Local (in terminal)
# Output shown directly
```

### Database Status:
```bash
# Check user count
sqlite3 axlbot.db "SELECT COUNT(*) FROM users;"

# Check group count
sqlite3 axlbot.db "SELECT COUNT(*) FROM groups WHERE is_active=1;"

# Check registered groups
sqlite3 axlbot.db "SELECT group_id, group_name FROM groups WHERE is_active=1;"
```

### Bot Health Check:
```bash
# Send /start command in DM
# Should receive formatted message with buttons

# Test in group
# Send /help
# Should receive formatted help menu
```

---

## 📈 UPGRADING

### Backup First:
```bash
cp axlbot.db axlbot.db.backup
```

### Update Code:
```bash
# Get latest version
git pull origin main

# Or manually update files
```

### Restart:
```bash
# Stop current bot (Ctrl+C or systemctl stop)

# If database schema changed:
rm axlbot.db  # To create fresh schema

# Restart bot
python bot.py
```

### Verify:
```bash
# Check /help works
# Check groups still registered
# Run tests
pytest tests/ -v
```

---

## 🔐 SECURITY NOTES

1. **Never share BOT_TOKEN** - Keep it in environment variables
2. **Never hardcode OWNER_ID** - Use environment variable
3. **Backup database regularly** - Important data stored
4. **Use HTTPS for Firebase** - Automatic if using Firebase
5. **Set strong admin passwords** - For systemd if applicable
6. **Update dependencies** - `pip install -r requirements.txt --upgrade`

---

## 📞 SUPPORT

**For issues:**
1. Check logs: `journalctl -u axlbot -f`
2. Check requirements: `pip install -r requirements.txt`
3. Reset database: `rm axlbot.db && python bot.py`
4. Review documentation: `README_BOT.md`, `TECHNICAL_DOCS.md`

**Common Commands:**
```bash
python bot.py              # Start bot
pytest tests/ -v           # Run tests
# Ctrl+C                   # Stop bot (local)
sqlite3 axlbot.db .dump   # Backup database
```

---

## ✅ DEPLOYMENT COMPLETE

Your AXL GAME BOT v2.0 is ready to deploy!

- ✅ Professional UI
- ✅ Group registration persistence
- ✅ Owner customization
- ✅ All games working
- ✅ Fully tested

**Deploy with confidence!** 🚀

---

**Last Updated:** February 14, 2026  
**Version:** 2.0 Professional Edition  
**Status:** ✅ Ready for Production
