# 🎮 GAMEBOT v4.0 - Pyrogram Version

**Production-ready Telegram bot with 10 games, economy system, Hinata AI, and premium UI.**

## 🚀 Quick Deploy on Koyeb (2 minutes)

### Step 1: Get Credentials
- **API_ID & API_HASH**: https://my.telegram.org → API Development Tools
- **BOT_TOKEN**: Message @BotFather on Telegram
- **OWNER_ID**: Message @userinfobot on Telegram
- **GROQ_KEYS** (optional): https://console.groq.com/keys

### Step 2: Deploy
1. Go to https://app.koyeb.com
2. Click **Create Service** → **GitHub**
3. Select **GAMEBOT** repository
4. Set Dockerfile: `Dockerfile_pyrogram`
5. Add environment variables:
   ```
   API_ID=YOUR_API_ID
   API_HASH=YOUR_API_HASH
   BOT_TOKEN=YOUR_BOT_TOKEN
   OWNER_ID=YOUR_USER_ID
   GROQ_KEYS=key1,key2 (optional)
   ```
6. Click **Deploy**
7. ✅ **Bot is LIVE in 2-3 minutes!**

---

## 🎮 Features

### 10 Games
- **Trivia** - Answer questions
- **RPS** - Rock Paper Scissors
- **Hangman** - Guess the word
- **Guess** - Number 1-50
- **Slots** - Spin reels (🎰)
- **Roulette** - Pick 0-36 (🎡)
- **Blackjack** - Get to 21 (♠️)
- **Dice** - Roll 2 dice
- **Lucky Draw** - Pick 1-10
- **Memory** - Match pairs (coming soon)

### 💰 Economy
- `/daily` - 500 coins every 24 hours
- `/balance` - Check your wealth
- `/leaderboard` - Top 15 richest users
- `/send [amount]` - Transfer coins
- `/kill [user]` - Attack for 90-150 coins
- `/steal [user]` - Rob coins (50% success)
- `/protect` - 24h protection shield
- `/revive [user]` - Bring back dead player

### 🤖 AI Chat (Hinata Hyuga Persona)
- Responds in **private chats**
- Responds when **mentioned in groups**
- Uses Groq API (with g4f fallback)
- Shy, caring, supportive personality
- Sends stickers randomly

### ✨ Premium Features
- 👑 No cooldowns on `/daily`
- 👑 Free `/protect` and `/revive`
- 👑 Bypass death mechanics
- 👑 Special badge on leaderboard

---

## 📋 Bot Commands

```
/start     - Welcome & menu
/help      - All commands
/daily     - Claim 500 coins
/balance   - Check wealth
/leaderboard - Top 15
/trivia    - Play trivia
/rps       - Rock Paper Scissors
/hangman   - Guess word
/guess     - Guess 1-50
/slots [bet]     - Spin reels
/roulette [bet]  - European roulette
/blackjack [bet] - Play blackjack
/dice [bet]      - Roll dice
/lucky [bet]     - Lucky draw
/dev       - Show credits
.help or !help - Prefix commands
```

---

## 🛠️ Local Testing

```bash
# Install dependencies
pip install -r requirements_pyrogram.txt

# Set environment variables
export API_ID=YOUR_API_ID
export API_HASH=YOUR_API_HASH
export BOT_TOKEN=YOUR_BOT_TOKEN
export OWNER_ID=YOUR_USER_ID
export GROQ_KEYS=key1,key2  # optional

# Run bot
python bot_complete_pyrogram.py
```

---

## 📁 Project Structure

```
GAMEBOT/
├── bot_complete_pyrogram.py      ← Main bot
├── requirements_pyrogram.txt     ← Dependencies
├── Dockerfile_pyrogram           ← Docker config
├── koyeb.yml                     ← Koyeb config
├── README.md                     ← This file
│
├── games/
│   ├── trivia.py
│   ├── rps.py
│   ├── hangman.py
│   ├── guess_number.py
│   ├── slots_pyrogram.py
│   ├── roulette_pyrogram.py
│   ├── blackjack_pyrogram.py
│   ├── dice_pyrogram.py
│   └── lucky_draw_pyrogram.py
│
└── utils/
    ├── firebase_db.py            ← Database
    └── motor_db.py               ← MongoDB (optional)
```

---

## ⚙️ Configuration

### Environment Variables (Required)
- `API_ID` - Telegram API ID
- `API_HASH` - Telegram API Hash
- `BOT_TOKEN` - Telegram Bot Token
- `OWNER_ID` - Your Telegram User ID

### Environment Variables (Optional)
- `GROQ_KEYS` - Comma-separated Groq API keys for AI
- `MONGO_URI` - MongoDB connection string
- `MONGO_DBNAME` - MongoDB database name

---

## 🔍 Health Check

Bot includes HTTP health check on port 8000:
```bash
curl https://your-bot-domain.koyeb.app/health
```

Response:
```json
{
  "status": "healthy",
  "bot": "GAMEBOT v4.0",
  "games": 10,
  "version": "4.0.0",
  "timestamp": "2026-02-14T22:30:00"
}
```

---

## 🐛 Troubleshooting

### Bot not responding
- Check all environment variables are set correctly
- Verify API_ID, API_HASH, and BOT_TOKEN
- Check Koyeb logs for errors

### "GROQ_KEYS not set" warning
- This is optional - bot uses g4f fallback
- For better AI responses, get keys from https://console.groq.com/keys

### Group commands not working
- Add bot to group
- Make bot admin (for /ban, /kick)
- Mention bot or reply to bot message

---

## 📝 Credits

**Created by**: FIGLETAXL

**Community**: @vfriendschat

**Framework**: Pyrogram 2.0+

**AI**: Groq (llama3-8b) + g4f fallback

---

## 📄 License

Open source - Free to use and modify

