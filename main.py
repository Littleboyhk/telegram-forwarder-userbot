import os
import sys
import logging
import asyncio
import re
import base64
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Try to load local environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Loaded environment variables from .env file (if present).")
except ImportError:
    logger.info("python-dotenv not installed; relying on system environment variables.")

# Retrieve environment variables
API_ID_RAW = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
SOURCE_CHAT_IDS_RAW = os.getenv("SOURCE_CHAT_IDS", "")
DEST_CHAT_ID_RAW = os.getenv("DEST_CHAT_ID")

# Sanitize SESSION_STRING by stripping whitespaces and potential surrounding quotes
if SESSION_STRING:
    SESSION_STRING = SESSION_STRING.strip().strip('"').strip("'")

# Check for missing required variables
missing_vars = []
if not API_ID_RAW:
    missing_vars.append("API_ID")
if not API_HASH:
    missing_vars.append("API_HASH")
if not SESSION_STRING:
    missing_vars.append("SESSION_STRING")
if not SOURCE_CHAT_IDS_RAW:
    missing_vars.append("SOURCE_CHAT_IDS")
if not DEST_CHAT_ID_RAW:
    missing_vars.append("DEST_CHAT_ID")

if missing_vars:
    logger.critical(f"Missing required environment variables: {', '.join(missing_vars)}")
    sys.exit(1)

# Parse API_ID
try:
    API_ID = int(API_ID_RAW)
except ValueError:
    logger.critical("API_ID must be a valid integer.")
    sys.exit(1)

# Parse SOURCE_CHAT_IDS (comma-separated, can contain integers or usernames)
SOURCE_CHAT_IDS = []
for cid in SOURCE_CHAT_IDS_RAW.split(","):
    cid = cid.strip()
    if not cid:
        continue
    # If it represents an integer, convert it (handles negative chat/channel IDs)
    if cid.startswith("-") or cid.isdigit():
        try:
            SOURCE_CHAT_IDS.append(int(cid))
        except ValueError:
            SOURCE_CHAT_IDS.append(cid)
    else:
        SOURCE_CHAT_IDS.append(cid)

# Parse DEST_CHAT_ID
if DEST_CHAT_ID_RAW.startswith("-") or DEST_CHAT_ID_RAW.isdigit():
    try:
        DEST_CHAT_ID = int(DEST_CHAT_ID_RAW)
    except ValueError:
        DEST_CHAT_ID = DEST_CHAT_ID_RAW
else:
    DEST_CHAT_ID = DEST_CHAT_ID_RAW

logger.info(f"Targeting source chats: {SOURCE_CHAT_IDS}")
logger.info(f"Targeting destination chat: {DEST_CHAT_ID}")


async def main():
    logger.info("Initializing Telegram Client with StringSession...")
    
    # Debug SESSION_STRING details safely (without printing the full secret)
    if SESSION_STRING:
        safe_str = f"{SESSION_STRING[:10]}...{SESSION_STRING[-10:]}" if len(SESSION_STRING) > 20 else "TOO_SHORT"
        logger.info(f"SESSION_STRING environment variable details: length={len(SESSION_STRING)}, value={safe_str}")
        try:
            # Try to decode locally first to log the length
            decoded_test = base64.urlsafe_b64decode(SESSION_STRING[1:])
            logger.info(f"Decoded session string length: {len(decoded_test)} bytes")
        except Exception as e:
            logger.error(f"Failed to base64 decode SESSION_STRING: {e}")
    else:
        logger.warning("SESSION_STRING is empty!")

    # Initialize the Telethon Client
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

    # Event handler for incoming messages in source chats
    @client.on(events.NewMessage(chats=SOURCE_CHAT_IDS))
    async def handler(event):
        chat_id = event.chat_id
        msg_id = event.message.id
        logger.info(f"Received new message {msg_id} from source chat {chat_id}")
        
        try:
            # Extract and clean message text (remove URLs and links)
            raw_text = event.message.text or ""
            # Match http, https, www, and t.me links
            url_pattern = r'(https?://\S+|www\.\S+|t\.me/\S+)'
            cleaned_text = re.sub(url_pattern, '', raw_text)
            cleaned_text = re.sub(r' +', ' ', cleaned_text)
            cleaned_text = re.sub(r'\n\s*\n', '\n', cleaned_text).strip()

            # Send as new message to prevent "Forwarded from" header
            if event.message.media:
                # Send the media file with the cleaned caption text
                await client.send_message(DEST_CHAT_ID, cleaned_text, file=event.message.media)
                logger.info(f"Successfully sent media from message {msg_id} (links removed, not marked as forwarded).")
            else:
                # If it's a text-only message, send it only if there is text left after cleaning
                if cleaned_text:
                    await client.send_message(DEST_CHAT_ID, cleaned_text)
                    logger.info(f"Successfully sent text from message {msg_id} (links removed, not marked as forwarded).")
                else:
                    logger.info(f"Skipped empty message {msg_id} after stripping links.")
        except Exception as e:
            logger.error(f"Failed to process/send message {msg_id} from chat {chat_id}. Error: {e}")

    # Start the client and run until disconnected
    await client.start()
    logger.info("Telegram Client started successfully and is listening for messages...")
    await client.run_until_disconnected()


# ---------------------------------------------------------------------------
# Minimal HTTP health-check server (keeps Render free Web Service alive)
# ---------------------------------------------------------------------------
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

    def log_message(self, format, *args):
        pass  # suppress noisy HTTP logs


def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    logger.info(f"Health-check HTTP server listening on port {port}")
    server.serve_forever()


if __name__ == "__main__":
    # Start the health-check server in a background daemon thread
    threading.Thread(target=run_health_server, daemon=True).start()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Userbot stopped by user.")
    except Exception as e:
        logger.critical(f"Userbot encountered a fatal error: {e}")
        sys.exit(1)
