# VPS deployment (systemd)

1. Build and run inside a Python virtualenv or Docker.

Systemd unit example (create `/etc/systemd/system/axlbot.service`):

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

Then enable and start:
```
sudo systemctl daemon-reload
sudo systemctl enable --now axlbot.service
sudo journalctl -u axlbot -f
```

For Docker, build and run:
```
docker build -t axl-bot:latest .
docker run -e BOT_TOKEN="$BOT_TOKEN" -e OWNER_ID="$OWNER_ID" axl-bot:latest
```
