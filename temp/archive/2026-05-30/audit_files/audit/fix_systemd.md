# Systemd Service Files - Fix Report

**Date:** 2026-05-28 12:41:08 UTC
**VPS:** 5.223.81.16

## Results

### psvibe-api-server
- **File:** `/etc/systemd/system/psvibe-api-server.service`
- **Existed before:** Yes
- **Write:** ✅ Success
- **Enable:** ✅ Success
- **Enable Error:** `Created symlink /etc/systemd/system/multi-user.target.wants/psvibe-api-server.service → /etc/systemd/system/psvibe-api-server.service.`
- **Start:** ✅ Success
- **Active Status:** active

### psvibe-sale-bot
- **File:** `/etc/systemd/system/psvibe-sale-bot.service`
- **Existed before:** Yes
- **Write:** ✅ Success
- **Enable:** ✅ Success
- **Start:** ✅ Success
- **Active Status:** active

### psvibe-customer
- **File:** `/etc/systemd/system/psvibe-customer.service`
- **Existed before:** Yes
- **Write:** ✅ Success
- **Enable:** ✅ Success
- **Enable Error:** `Created symlink /etc/systemd/system/multi-user.target.wants/psvibe-customer.service → /etc/systemd/system/psvibe-customer.service.`
- **Start:** ✅ Success
- **Active Status:** active

## Service Contents

### psvibe-api-server
```ini
[Unit]
Description=PS VIBE API Server
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/psvibe_api_server
ExecStart=/root/psvibe_api_server/venv/bin/uvicorn app:app --host 127.0.0.1 --port 8000
EnvironmentFile=/etc/psvibe/secrets.env
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### psvibe-sale-bot
```ini
[Unit]
Description=PS VIBE Sales Bot
After=network.target psvibe-api-server.service
Requires=psvibe-api-server.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/psvibe-sale-bot
ExecStart=/root/venv/bin/python3 main.py
EnvironmentFile=/etc/psvibe/secrets.env
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### psvibe-customer
```ini
[Unit]
Description=PS VIBE Customer Bot
After=network.target psvibe-api-server.service
Requires=psvibe-api-server.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/psvibe-sale-bot/customer_bot
ExecStart=/root/venv/bin/python3 main.py
EnvironmentFile=/etc/psvibe/secrets.env
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

