from telethon import TelegramClient
from telethon.sessions import StringSession
import asyncio

API_ID = 1234567  # Replace with your API ID (int)
API_HASH = "your_api_hash"  # Replace with your API Hash (str)

async def main():
    async with TelegramClient(StringSession(), API_ID, API_HASH) as client:
        print("\n✅ Your session string (copy EXACTLY):\n")
        print(client.session.save())

asyncio.run(main())