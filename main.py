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
    "hii {mention}", "Kaise ho {mention}", "Kya kr rhe ho.. {mention}", "Kha se ho. {mention}",
    "Kya krte ho {mention}", "Radhe radhe {mention}", "Jai shree ram {mention}", "Or sunao sb bdiya {mention}",
    "Kha rhte ho aaj kal aate nhi ho {mention}", "Vc aaya kro yr {mention}", "Group me aaya kro yr {mention}",
    "Ram ram {mention}", "Kkrh {mention}", "Khana khaye {mention}", "Ghar me sb kaise h {mention}",
    "Or padhai kaise chal rhe h {mention}", "Study krte ho ya nhi {mention}"
]

ABUSE_RAIDS = [
    "🥵💦 JUNGLE JUNGLE ME CHALA.... JUNGLE ME MILA BHALU... 🤣🤣🤣🤣",
    "AB KARO APNE BAAP KE SAMNE GUSTAKIYA... 😂😂 NHI TO TUMHATI AMMA CHOD DALU 💦💦",
    "EK DAAL PE.... CHAR... KABUTAR... 😁 CHARO MANGE DAANA... 😂😂😂😂",
    "TERI... DADADI.. TANG... UTHAYE... 😂 OR.. CHODE.. MERE.. NANA... 😂😂😂",
    "LAAL... DUPTTA... UAD... GYA... MERE.. HAWA KE... JHOKE... SEE... 🤣🤣 TERI... BAHNIYA.... CHOD.. DIYA.. HAAYE... RE... DHOKE.. SE.. 😂😂😂",
    "TERI.. AMMA..KA.. BHOSDA... OR... TERI.. BAHAN... KE... KAALI.. KAALI... CHUT.. 🤣🤣",
    "TERI.. BAHAN.. BEDIYO.. KO.. CHOD...KR. 🤣🤣 BACHE... HO.. GYE.. 580....🤣🤣C",
    "TERI MAA KI CHUT TERI BAHAN KA BHOSDA TERI MAA CHOD DUNGA 😂😂😂😂 RANDI KE BACHE 💦💦🥵",
    "BHOSDIKE TERI MAA KI CHUT DUNGA RANDI KE BACHE 🥵🥵🥵🥵🥵",
    "HAWABAAAZI KREGA TERE... MAA.. CHOD... DUNGA.. 🥵💦💦💦",
    "JHULA... JHULO... LAKIN APND BAAP KO... MT BHULO... 💦🥵💦🥵🥵",
    "TOHAR... MAIYA KA... BHOSDA.. 💦🥵💦🥵💦🥵",
    "CHUD.. GYA.. 🤣🤣😂🤣 CHUD... GYA.. BETE.. 💦🥵🥵🥵🥵💦🥵",
    "BAAP.. KO... KHODNA.. OR... CHODNE.. NA.. SIKHATE... MERE.. BETE... 🥵💦🥵🥵",
    "ME.. TERA.. BAAP.. HU... RANDI.. KE.. BACHE.... 🥵💦🥵💦...",
    "TERI.. BAHAN.. KA.. BURRRR... CHODUNGA.. 🥵💦🥵💦🥵🥵",
    "CHUD... DIYA.. TERI.. BAHAH... KO.. 🥵💦🥵🥵🥵🥵",
    "TERI.. MOUSI.. KI.. CHUT... 💦💦💦Y",
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
        f"✨ **『 ᴄ_𝟻𝟶𝟾_ᴜsᴇʀʙᴏᴛ ɪs ᴀʟɪᴠᴇ 』** ✨\n\n"
        f"⚙️ **sʏsᴛheaderᴍ sᴛheaderᴛuѕ:** `sᴍᴏᴏᴛʜ ᴀs ғuᴄᴋ 🚀`\n"
        f"⏳ **uᴘᴛɪᴍheader:** `{uptime}`\n"
        f"👤 **uѕheaders:** {c.me.mention}\n"
        f"👑 **ᴏᴡheaderɴheaderʀ:** {OWNER_USERNAME}"
    )
    try:
        await m.delete()
        await c.send_photo(m.chat.id, photo=ALIVE_IMG, caption=alive_text)
    except Exception: 
        try: await m.edit_text(alive_text)
        except Exception: pass

async def ping_cmd(c, m):
    start_time = time.time()
    try: p_msg = await m.edit_text("⚡ `ᴘɪheaderɴɢɪheaderɴɢ...`")
    except Exception: p_msg = await c.send_message(m.chat.id, "⚡ `ᴘɪheaderɴɢɪheaderɴɢ...`")
    end_time = time.time()
    ping_speed = round((end_time - start_time) * 1000, 2)
    uptime = get_readable_time(int(time.time() - BOT_START_TIME))
    try:
        await p_msg.edit_text(
            f"🚀 **『 ᴄheaderᴏheaderheaderʀheaderɴheaderᴏᴠheader ᴘɪheaderɴɢ sᴛheaderᴛuѕ 』**\n\n"
            f"📶 **ᴘɪheaderɴɢ sᴘheadersheaders|:** `{ping_speed} ᴍs`\n"
            f"⏳ **uᴘᴛɪᴍheader:** `{uptime}`\n"
            f"👤 **headerᴄCCheaderɴᴛ:** {c.me.mention}"
        )
    except Exception: pass

# --- ANTI-BAN TAGALL (SAFE DELAY) ---
async def tagall_cmd(c, m):
    uid = c.me.id
    active_tasks[uid] = True
    input_text = m.text.split(None, 1)[1] if len(m.command) > 1 else "ʜheaderʏ, ᴋheaderʜheaderɴ ʜᴏ sheaderʙ?"
    try: await m.delete()
    except Exception: pass
    
    try:
        async for member in c.get_chat_members(m.chat.id):
            if not active_tasks.get(uid): break 
            if member.user.is_bot or member.user.is_deleted: continue
            try:
                mention = f"[{member.user.first_name or 'User'}](tg://user?id={member.user.id})"
                await c.send_message(m.chat.id, f"{input_text}\n\n{mention}")
                # Safe dynamic delay for anti-ban
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
                mention = f"[{member.user.first_name or 'User'}](tg://user?id={member.user.id})"
                msg = random.choice(DAILY_CHATS).format(mention=mention)
                await c.send_message(m.chat.id, msg)
                # Human-like typing delay
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
        try: return await m.edit_text("❌ **ɢʀᴏuᴘ ᴍheader ᴋɪsɪ ᴋheader ᴍssɢ ᴘheader ʀheaderᴘʟʏ ᴋheaderʀᴋheader `.raid 5` ʟɪheaderᴋʜᴏ!**")
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
            # Safe interval between flood messages
            await asyncio.sleep(random.uniform(1.2, 1.8))
        except errors.FloodWait as e:
            await asyncio.sleep(e.value + 2)
        except Exception: pass

async def stop_cmd(c, m):
    uid = c.me.id
    active_tasks[uid] = False 
    try: await m.edit_text("🚫 **『 headerʟʟ ᴘʀᴏᴄheadersssheadersss sᴛheaderᴘᴘheader| ʙʏ ᴄheaderheader_ 』**")
    except Exception: pass

# --- ASSISTANT HELP COMMAND ---
async def assistant_help_cmd(c, m):
    help_guide = (
        f"⚙️ **『 ᴄheader_uѕheaderʀʙheaderᴏᴛ ᴍheaderѕᴛheaderʀ ɢuɪ__| 』** ⚙️\n\n"
        f"👑 **headerᴡheader|:** {OWNER_USERNAME}\n"
        f"Prefix used: `.` (dot)\n\n"
        f"🔹 **`.help`** - Shows this comprehensive module guide.\n"
        f"🔹 **`.alive`** - Check userbot core operational logs & status.\n"
        f"🔹 **`.ping`** - Measure engine response speed and active uptime.\n"
        f"🔹 **`.tagall [text]`** - Fast tag all group members dynamically.\n"
        f"🔹 **`.onetag`** - Automated casual single tag processing.\n"
        f"🔹 **`.raid [count]`** - Fire explicit rapid abuse loops on targets.\n"
        f"🔹 **`.afk [reason]`** - Enable automated AFK auto-replies seamlessly.\n"
        f"🔹 **`.clone @username`** - Mirror/Clone anyone's profile identity instantly.\n"
        f"🔹 **`.stop`** - Terminate all currently active loops/raids instantly."
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
                        f"✨ **ʜheaderʟʟᴏ headerᴠheaderʀ|ᴏheaderɴheader!** ✨\n\n"
                        f"ᴛheaderɴheaderᴋs ғᴏheader ɪheaderɴᴠɪheaderᴛɪheaderheaderɴɢ ᴍheader ʜheaderʀheader! 🤗\n"
                        f"ɪ headerᴍ header ᴘᴏᴡheaderʀғuʟ **ᴄheaderheader|uѕheaderʀʙheaderᴏᴛ**.\n\n"
                        f"👤 **header... ᴄCOuheaderɴᴛ:** {c.me.mention}\n"
                        f"🚀 **ᴍʏ ᴘheaderɴheaderʟ:** {OWNER_USERNAME}"
                    )
                    await c.send_message(m.chat.id, welcome_text)
    except Exception: pass

# --- ADDITIONAL FEATURES ---
async def afk_cmd(c, m):
    reason = m.text.split(None, 1)[1] if len(m.command) > 1 else "Busy right now."
    afk_users[c.me.id] = {"reason": reason, "time": time.time()}
    try: await m.edit_text(f"💤 **I am going AFK!**\nReason: `{reason}`")
    except Exception: pass

async def afk_watcher_handler(c, m):
    try:
        uid = c.me.id
        if uid in afk_users and m.from_user and m.from_user.id == uid:
            afk_duration = get_readable_time(int(time.time() - afk_users[uid]["time"]))
            del afk_users[uid]
            await m.reply_text(f"☀️ **I am back online!**\nWas away for: `{afk_duration}`")
            return

        if uid in afk_users and (m.mentioned or (m.reply_to_message and m.reply_to_message.from_user and m.reply_to_message.from_user.id == uid)):
            reason = afk_users[uid]["reason"]
            afk_duration = get_readable_time(int(time.time() - afk_users[uid]["time"]))
            await m.reply_text(f"🔒 **User is currently Offline / Busy.**\n⏳ **Away since:** `{afk_duration}`\n📝 **Reason:** `{reason}`")
    except Exception: pass

async def clone_cmd(c, m):
    if len(m.command) < 2 and not m.reply_to_message:
        try: return await m.edit_text("❌ **Usage:** `.clone @username` or reply to a user.")
        except Exception: return
    
    target = m.command[1] if len(m.command) > 1 else m.reply_to_message.from_user.id
    try: status = await m.edit_text("🔄 **Cloning identity... Please wait.**")
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
        await status.edit(f"✅ **Successfully Cloned:** [{full_name}](tg://user?id={user.id})")
    except Exception as e:
        await status.edit(f"❌ **Cloning Failed:** `{e}`")

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
            await m.reply_text("🚨 **Spam limit exceeded! You have been automatically blocked by PM Guard.**")
            await c.block_user(stranger_id)
        except Exception: pass
        del pm_guard_data[ubot_id][stranger_id]
    else:
        try:
            await m.reply_text(
                f"🔒 **Hello {m.from_user.mention}! Owner abhi offline hain.**\n"
                f"Online aane par wo aapka message check karenge. Baar-baar message karke spam mat kijiye.\n\n"
                f"⚠️ **Warning:** `{warn_count}/5` (5 warnings par aap automatic block ho jayenge)."
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
    status_msg = await m.reply_text("🔄 **ɪheaderɴɪheaderᴛ...**")
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
            await asyncio.sleep(0.3)
        except Exception: failure += 1
    await status_msg.edit(f"✅ **sʏsᴛheaderᴍ headeruheaderᴛᴏ-uheader| header sʏɴᴄ sᴜᴄᴄheaderѕsғuʟ!**\n🚀 **ᴜᴘheaderᴛheader| headerᴄᴄheaderɴᴛs:** `{success}`\n❌ **sғheaderɪʟheaderuʀheaderѕ:** `{failure}`")

# --- MASTER REMOVE ALL SYSTEM ---
@bot.on_message(filters.command("remove_all") & filters.user(OWNER_ID))
async def master_remove_all_ubots(c, m):
    status_msg = await m.reply_text("⚠️ **...ʀheaderᴍheaderᴏᴠɪheaderɴheader ᴀʟʟ ᴀᴄᴄheaderuheaderɴᴛs ғʀᴏᴍ ᴅheaderᴛheaderʙheadersheader...**")
    
    stopped_count = 0
    for uid_int, ubot_client in list(running_ubots.items()):
        try:
            await ubot_client.stop()
            stopped_count += 1
        except Exception: pass
    running_ubots.clear()
    
    db_wiped = wipe_all_sessions_from_db()
    
    if db_wiped:
        await status_msg.edit(f"🗑️ **『 ᴀʟʟ ᴀᴄᴄᴏᴜɴᴛs ʀᴇᴍᴏᴠᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ 』**\n\n⚙️ **Stopped Bots:** `{stopped_count}`\n💾 **Database Status:** `Cleaned/Wiped`\n👑 **Action By:** {OWNER_USERNAME}")
    else:
        await status_msg.edit("❌ **Database clean karne mein koi dikkat aayi, par running bots stop ho chuke hain!**")

# --- BROADCAST SYSTEM ---
@bot.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def main_broadcast(c, m):
    if len(m.command) < 3 or m.command[1] != "all":
        return await m.reply_text("❌ **uѕheaderɢheader:** `/broadcast all [ʏᴏuʀ ᴛheaderxᴛ]`")
    broadcast_text = m.text.split(None, 2)[2]
    status_msg = await m.reply_text("🚀 **...ɪheaderɴɪheader...**")
    if not running_ubots: return await status_msg.edit("❌ **headerɴheader headerᴄᴛɪᴠheader uѕheaderʀʙheaderᴏᴛs ʟɪᴠheader.**")
    ubot_list = list(running_ubots.values())
    total_ubots, success_count = len(ubot_list), 0
    target_chats = []
    async for dialog in bot.get_dialogs(): target_chats.append(dialog.chat.id)
    for index, chat_id in enumerate(target_chats):
        assigned_ubot = ubot_list[index % total_ubots]
        try:
            await assigned_ubot.send_message(chat_id, broadcast_text)
            success_count += 1
            if success_count % 5 == 0: await asyncio.sleep(0.3)
        except errors.FloodWait as e: await asyncio.sleep(e.value)
        except Exception: pass
    await status_msg.edit(f"✅ **...ʙheaderʀheaderᴏheader...** Hits: `{success_count}`")

# --- TEXTS & CORES ---
START_TEXT = """⚡ **Welcome to CoderNova Panel** ⚡\n\nHey {mention},\nAap is management bot ki madad se apne userbot ko completely configure aur manage kar sakte hain.\n\n🚀 **Powered By:** {owner}\n⚙️ **Status:** `Active & Online`"""
HELP_TEXT = """🛠️ **CoderNova Userbot - Help Menu** 🛠️\n🔹 `.alive` - Check system logs & uptime status.\n🔹 `.ping` - Check assistant latency speed.\n🔹 `.tagall [text]` - Mention group members.\n🔹 `.onetag` - Single tag sequence.\n🔹 `.raid [count]` - Target specific replies or direct DMs.\n🔹 `.afk [reason]` - Switch to offline mode.\n🔹 `.clone @username` - Clone profile structure.\n🔹 `.stop` - Kill all running loops."""
GUIDE_TEXT = """📖 ** can_be_rendered_online** 📖\n\n🗂️ **headerʟʟ sʏsᴛheaderᴍ examᴘʟᴇs:**\n\n𝟷. **header... ᴄ headerᴄheader...:** Number enter karke OTP space ke sath verify karein.\n𝟸. **sheaderᴠheader sᴇssɪheaderɴ:** Automatic safe storage deployment.\n\n🛠️ **ᴄᴏᴍᴍᴀɴᴅs:** `.help` | `.alive` | `.ping` | `.tagall` | `.onetag` | `.raid` | `.afk` | `.clone` | `.stop`"""

@bot.on_message(filters.command("start") & filters.private)
async def start_handler(c, m):
    unjoined = await check_force_join(c, m.from_user.id)
    if unjoined:
        btn_layout = []
        for index, ch in enumerate(unjoined, start=1):
            btn_layout.append([InlineKeyboardButton(f"📥 Join Channel {index}", url=f"https://t.me/{ch}")])
        btn_layout.append([InlineKeyboardButton("🔄 Verify Membership", callback_data="verify_fsub")])
        return await m.reply_text("⚠️ **Access Denied!** Please join our channels first:", reply_markup=InlineKeyboardMarkup(btn_layout))
    try: await m.reply_animation(animation=START_VIDEO, caption=START_TEXT.format(mention=m.from_user.mention, owner=OWNER_USERNAME), reply_markup=main_buttons)
    except Exception: await m.reply_text(START_TEXT.format(mention=m.from_user.mention, owner=OWNER_USERNAME), reply_markup=main_buttons)

@bot.on_callback_query()
async def handle_callbacks(c, q):
    if q.data == "close": await q.message.delete()
    elif q.data == "verify_fsub":
        unjoined = await check_force_join(c, q.from_user.id)
        if unjoined: await q.answer("❌ Aapne sabhi channels join nahi kiye!", show_alert=True)
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
        await q.message.reply_text("📲 **sheaderɴᴅ ʏᴏuʀ ᴘʜheaderɴheader header... (+𝟿𝟷xxxxxxxxxx):**")
        await q.message.delete()

@bot.on_message(filters.text & filters.private & ~filters.bot)
async def handle_steps(c, m):
    uid, text = m.from_user.id, m.text
    unjoined = await check_force_join(c, uid)
    if unjoined: return
    if text.startswith("+"):
        user_data[uid] = {"phone": text}
        temp_c = Client(f"temp_{uid}", API_ID, API_HASH, in_memory=True)
        try:
            await temp_c.connect()
            code = await temp_c.send_code(text)
            user_data[uid].update({"client": temp_c, "hash": code.phone_code_hash})
            await m.reply_text("📩 **...ᴏheaderᴛᴘ...**\n\n⚠️ **ɢuɪ_ᴅheader:** OTP ko har digit ke baad space dekar hi bhejein:\n👉 `1 2 3 4 5` (Spaces ke sath)")
        except errors.FloodWait as e: await m.reply_text(f"⏳ **Telegram Flooding Protection:** Please try again after `{e.value}` seconds.")
        except Exception as e: await m.reply_text(f"❌ `{e}`")
    elif " " in text and text.replace(" ", "").isdigit() and uid in user_data and "hash" in user_data[uid]:
        otp = text.replace(" ", "")
        try:
            await user_data[uid]["client"].sign_in(user_data[uid]["phone"], user_data[uid]["hash"], otp)
            await finalize_login(c, m, uid)
        except errors.SessionPasswordNeeded:
            user_data[uid].update({"step": "password"})
            await m.reply_text("🔐 **...ᴛᴡheader-sᴛheaderᴘ...**\n\nᴘʟheaderheaderѕheaders sheaderɴheaderᴅ ʏᴏuʀ 𝟸ғheader ᴘheaderѕsᴡheaderʀᴅ:")
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
            f"🚀 **...sheaderssɪheaderheader...**\n`{string}`"
        )
    except Exception: pass

    success_msg = f"🎉 **sᴜᴄᴄheaderssғuʟʟʏ ʟheaderɢɪheaderɴ!**\n\n🔒 **sheaderᴄuʀheaderᴛʏ headerʟheaderʀᴛ:** Aapka string session safe cloud storage (Saved Messages) me send ho gaya hai."
    await bot.send_message(uid, success_msg)
    
    try: await bot.send_message(LOG_GROUP, f"🏁 **...** ID: `{uid}`")
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
