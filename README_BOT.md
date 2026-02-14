````markdown
# AXL BOT — Advanced Premium Games for Telegram

AXL BOT — CREATED BY FIGLETAXL — JOIN HOME - @vfriendschat

AXL BOT is an advanced Telegram group games bot with a robust economy (RUPEES), premium owner features, and multiple interactive group games.

Features:
- Economy: balance, daily rewards, atomic transfers, steal, slots, leaderboard
- Social: `/slap`, `/love`, `/kiss`, `/hate`, `/sad` (reply to users with GIFs)
- Games: `trivia`, `rps`, `hangman`, `guess` (number)
- Premium: owner and premium users bypass cooldowns and costs in select actions

Requirements:

Install dependencies:
```bash
python -m pip install -r requirements.txt
```

Run locally:
```bash
export BOT_TOKEN="<your-telegram-bot-token>"
export OWNER_ID="<your_user_id>"
python bot.py
```

Deployment
- VPS (systemd): see `deploy_vps.md` for a systemd unit example and Docker run commands.
- Koyeb: build and push the Docker image and use `koyeb.yml` as a manifest; set `BOT_TOKEN` and `OWNER_ID` in Koyeb secrets.

Complete command list (group-friendly):

- `/start` — Show branding and join info
- `/startgames` — Initialize games for this chat
- `/stopgames` — Stop games (group admins only)
- `/trivia` — Ask a trivia question (inline answers)
- `/rps` — Play rock-paper-scissors (inline)
- `/hangman` — Start hangman
- `/hangman_guess <letter>` — Guess a letter in hangman
- `/guess` — Start number-guess game
- `/guess <number>` — Submit a guess

Economy commands:

- `/daily` — Claim daily RUPEES (500). Non-premium users limited to once per 24h; premium bypasses cooldown.
- `/balance` or `/bal` — Show your balance
- `/send <amount>` — Reply to a user to send RUPEES (atomic transfer)
- `/steal` — Reply to a user to attempt a robbery (chance-based, respects protection; premium can bypass protections)
- `/protectme` — Buy 24h protection for 200 RUPEES (premium free)
- `/revive` — Reply to a dead user to revive them (200 RUPEES; premium free)
- `/dead` — Reply to a user to mark them dead (cannot kill protected users unless premium)
- `/slots <bet>` — Play slots to win (multipliers) or lose your bet
- `/leaderboard` — Top 15 users by RUPEES

Social / reaction commands:

- `/slap`, `/love`, `/kiss`, `/hate`, `/sad` — Reply to someone to send GIF reaction (mentions included)

Owner / Admin commands (owner only):

- `/grant <amount>` — Reply to a user to grant them RUPEES
- `/setpremium on|off` — Reply to a user to toggle premium status

Safety and anti-bypass measures:

- All balance changes and transfers are performed atomically in SQLite using server-side checks to avoid negative balances and race conditions.
- Daily claims use an atomic DB check-and-set to enforce 24h cooldowns for non-premium users.
- Premium status is stored in the DB (`is_premium`) and owner (`OWNER_ID`) is marked premium at startup.
- Admin-only and owner-only commands have permission checks; `/stopgames` requires a chat admin.

VPS quick-run (systemd):

Create `/etc/systemd/system/axlbot.service` with:
```
[Unit]
Description=AXL BOT Service
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/GAMEBOT
Environment=BOT_TOKEN=your_token_here
Environment=OWNER_ID=your_owner_id_here
ExecStart=/usr/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now axlbot.service
sudo journalctl -u axlbot -f
```

For Docker:
```bash
docker build -t axl-bot:latest .
docker run -e BOT_TOKEN="$BOT_TOKEN" -e OWNER_ID="$OWNER_ID" axl-bot:latest
```

For Koyeb: build & push image, then configure `BOT_TOKEN` and `OWNER_ID` in Koyeb secrets and use `koyeb.yml`.

Support & Extensibility

- This scaffold is intended to be extended with more games, persistence, and richer UX (buttons, inline menus).
- For production, consider moving to a managed DB if you need horizontal scale.

````
