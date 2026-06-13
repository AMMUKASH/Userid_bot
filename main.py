import os
import asyncio
from pyrogram import Client, filters
from flask import Flask
from threading import Thread

# --- CONFIGURATION ---
API_ID = 31980984
API_HASH = "a61358dd3cd8c3a56cd53d9ddd8a0c67"
BOT_TOKEN = "8709782891:AAEZPLJQOOJ6b-9WEMXsYWJSNu2YUu14fbI"

# --- WEB SERVER FOR RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "Test Bot Server Online! ✨"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- BOT INITIALIZATION ---
bot = Client("TestBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.command("start") & filters.private)
async def start_handler(c, m):
    print(f"[LOG] Received /start from {m.from_user.id}")
    await m.reply_text("✨ **Test Successful! Main online hoon aur chal raha hoon.**")

async def main():
    print("[INFO] Starting Pyrogram Bot Client...")
    await bot.start()
    print("[SUCCESS] Bot started completely and listing for messages.")
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    Thread(target=run_web, daemon=True).start()
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("[INFO] Bot Stopped.")
