# Telegram Message Forwarder Userbot

A lightweight, production-ready Python script built with [Telethon](https://github.com/LonamiWebs/Telethon) to automatically forward messages from multiple source chats/channels to a single destination chat/channel in real-time.

## Features

- **Real-Time Forwarding**: Relays text messages, photos, videos, voice notes, documents, and other media instantly.
- **Multiple Source Support**: Listen to one or many channels/chats simultaneously.
- **Zero Local Database Required**: Uses Telethon `StringSession` to handle authentication, making it completely stateless and ideal for serverless or ephemeral cloud environments.
- **Easy Configuration**: Fully configured using environment variables.

---

## Prerequisites

1. **Python 3.10+** installed on your system.
2. **API ID** & **API Hash**: Get them by creating an application at [my.telegram.org](https://my.telegram.org).
3. **Session String**: A Telethon authentication string to run headless (see below on how to generate it).
4. **Source & Destination Chat IDs**: Numerical IDs or usernames (e.g., `-100123456789` or `username`).

---

## Setup & Local Usage

### 1. Clone the Repository
```bash
git clone https://github.com/Littleboyhk/telegram-forwarder-userbot.git
cd telegram-forwarder-userbot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Generate a Telethon String Session
Since this bot runs headlessly on cloud servers, you must generate a `SESSION_STRING` on your local computer first.

Create a temporary script named `session_generator.py` and run it:
```python
from telethon import TelegramClient
from telethon.sessions import StringSession

api_id = 1234567  # Replace with your API ID (int)
api_hash = "your_api_hash"  # Replace with your API Hash (str)

with TelegramClient(StringSession(), api_id, api_hash) as client:
    print("\nCopy the long session string below:")
    print(client.session.save())
    print("\nKeep this string secret! Anyone with this string can access your account.")
```
Run the generator, follow the prompts on your terminal, and copy the printed string.

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and fill in the values:
```env
API_ID=your_api_id_here
API_HASH=your_api_hash_here
SESSION_STRING=your_generated_session_string
SOURCE_CHAT_IDS=-100xxxxxxxxxx,-100xxxxxxxxxx
DEST_CHAT_ID=-100xxxxxxxxxx
```

### 5. Run the Userbot
```bash
python main.py
```

---

## Cloud Deployment

This script includes a built-in HTTP health-check server, making it compatible with **Render's free Web Service** tier (no paid Background Worker needed).

### Deployment Steps (Render — Free Tier)
1. Fork or push this repository to your GitHub account.
2. Create a new **Web Service** on Render (free tier works).
3. Link your repository.
4. Set the **Start Command** to:
   ```bash
   python main.py
   ```
5. Add the following **Environment Variables** in the dashboard settings:
   - `API_ID`
   - `API_HASH`
   - `SESSION_STRING`
   - `SOURCE_CHAT_IDS`
   - `DEST_CHAT_ID`
6. Deploy! The health server will bind to `PORT` (auto-set by Render), keeping the service alive while the forwarder runs in the main thread.

### ⚠️ Preventing Idle Spin-Down

Render's free Web Services spin down after ~15 minutes of no incoming HTTP traffic. To keep the bot awake 24/7, use a free external pinger like [UptimeRobot](https://uptimerobot.com/) to ping your Render URL every 5–10 minutes.

---

## Disclaimer

> [!WARNING]
> This is a userbot. Using userbots is technically against Telegram's Terms of Service and might result in account limitations or bans if abused. Use responsibly, avoid spamming, and do not forward copyrighted or malicious content.

