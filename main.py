import ast
import asyncio
import json
import os
import sys
import random
import re
import shutil
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask
from threading import Thread
from pymongo import MongoClient

try:
    from PIL import Image, ImageDraw
    HAS_PIL = True
except ImportError:
    Image = None
    ImageDraw = None
    HAS_PIL = False

import config
from config import (
    API_ID,
    API_HASH,
    BOT_TOKEN,
    MONGO_URL,
    DB_NAME,
    START_VIDEO,
    ALIVE_IMG,
    OWNER_ID,
    OWNER_USERNAME,
    PORT,
)

from pyrogram import Client, filters, errors, handlers, idle
from pyrogram.enums import ChatAction, ChatType, ParseMode
from pyrogram.raw import functions as raw_functions
from pyrogram.raw import types as raw_types
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_START_TIME = time.time()
USERBOT_VERSION = "v3.2.0-FAST-SYNC"
ACCOUNTS_PER_PAGE = 5
DEFAULT_PREMIUM_EMOJI_ID = 6120898777046847624

CLIENT_DEVICE_MODEL = "Samsung Galaxy S23"
CLIENT_SYSTEM_VERSION = "Android 14"
CLIENT_APP_VERSION = "10.14.5"

# Single allowed log group ID (all other log group IDs blocked)
ACTIVE_LOG_GROUP_ID = -1003947649552

# Calling code -> (Country Name, ISO2)
CALLING_CODES = {
    "1": ("USA / Canada", "US/CA"),
    "7": ("Russia / Kazakhstan", "RU/KZ"),
    "20": ("Egypt", "EG"),
    "27": ("South Africa", "ZA"),
    "30": ("Greece", "GR"),
    "31": ("Netherlands", "NL"),
    "32": ("Belgium", "BE"),
    "33": ("France", "FR"),
    "34": ("Spain", "ES"),
    "36": ("Hungary", "HU"),
    "39": ("Italy", "IT"),
    "40": ("Romania", "RO"),
    "41": ("Switzerland", "CH"),
    "43": ("Austria", "AT"),
    "44": ("United Kingdom", "GB"),
    "45": ("Denmark", "DK"),
    "46": ("Sweden", "SE"),
    "47": ("Norway", "NO"),
    "48": ("Poland", "PL"),
    "49": ("Germany", "DE"),
    "51": ("Peru", "PE"),
    "52": ("Mexico", "MX"),
    "53": ("Cuba", "CU"),
    "54": ("Argentina", "AR"),
    "55": ("Brazil", "BR"),
    "56": ("Chile", "CL"),
    "57": ("Colombia", "CO"),
    "58": ("Venezuela", "VE"),
    "60": ("Malaysia", "MY"),
    "61": ("Australia", "AU"),
    "62": ("Indonesia", "ID"),
    "63": ("Philippines", "PH"),
    "64": ("New Zealand", "NZ"),
    "65": ("Singapore", "SG"),
    "66": ("Thailand", "TH"),
    "81": ("Japan", "JP"),
    "82": ("South Korea", "KR"),
    "84": ("Vietnam", "VN"),
    "86": ("China", "CN"),
    "90": ("Turkey", "TR"),
    "91": ("India", "IN"),
    "92": ("Pakistan", "PK"),
    "93": ("Afghanistan", "AF"),
    "94": ("Sri Lanka", "LK"),
    "95": ("Myanmar", "MM"),
    "98": ("Iran", "IR"),
    "211": ("South Sudan", "SS"),
    "212": ("Morocco", "MA"),
    "213": ("Algeria", "DZ"),
    "216": ("Tunisia", "TN"),
    "218": ("Libya", "LY"),
    "220": ("Gambia", "GM"),
    "221": ("Senegal", "SN"),
    "222": ("Mauritania", "MR"),
    "223": ("Mali", "ML"),
    "224": ("Guinea", "GN"),
    "225": ("Ivory Coast", "CI"),
    "226": ("Burkina Faso", "BF"),
    "227": ("Niger", "NE"),
    "228": ("Togo", "TG"),
    "229": ("Benin", "BJ"),
    "230": ("Mauritius", "MU"),
    "231": ("Liberia", "LR"),
    "232": ("Sierra Leone", "SL"),
    "233": ("Ghana", "GH"),
    "234": ("Nigeria", "NG"),
    "235": ("Chad", "TD"),
    "236": ("Central African Republic", "CF"),
    "237": ("Cameroon", "CM"),
    "238": ("Cape Verde", "CV"),
    "239": ("Sao Tome & Principe", "ST"),
    "240": ("Equatorial Guinea", "GQ"),
    "241": ("Gabon", "GA"),
    "242": ("Congo", "CG"),
    "243": ("DR Congo", "CD"),
    "244": ("Angola", "AO"),
    "245": ("Guinea-Bissau", "GW"),
    "248": ("Seychelles", "SC"),
    "249": ("Sudan", "SD"),
    "250": ("Rwanda", "RW"),
    "251": ("Ethiopia", "ET"),
    "252": ("Somalia", "SO"),
    "253": ("Djibouti", "DJ"),
    "254": ("Kenya", "KE"),
    "255": ("Tanzania", "TZ"),
    "256": ("Uganda", "UG"),
    "257": ("Burundi", "BI"),
    "258": ("Mozambique", "MZ"),
    "260": ("Zambia", "ZM"),
    "261": ("Madagascar", "MG"),
    "262": ("Reunion / Mayotte", "RE"),
    "263": ("Zimbabwe", "ZW"),
    "264": ("Namibia", "NA"),
    "265": ("Malawi", "MW"),
    "266": ("Lesotho", "LS"),
    "267": ("Botswana", "BW"),
    "268": ("Eswatini", "SZ"),
    "269": ("Comoros", "KM"),
    "290": ("Saint Helena", "SH"),
    "291": ("Eritrea", "ER"),
    "297": ("Aruba", "AW"),
    "298": ("Faroe Islands", "FO"),
    "299": ("Greenland", "GL"),
    "350": ("Gibraltar", "GI"),
    "351": ("Portugal", "PT"),
    "352": ("Luxembourg", "LU"),
    "353": ("Ireland", "IE"),
    "354": ("Iceland", "IS"),
    "355": ("Albania", "AL"),
    "356": ("Malta", "MT"),
    "357": ("Cyprus", "CY"),
    "358": ("Finland", "FI"),
    "359": ("Bulgaria", "BG"),
    "370": ("Lithuania", "LT"),
    "371": ("Latvia", "LV"),
    "372": ("Estonia", "EE"),
    "373": ("Moldova", "MD"),
    "374": ("Armenia", "AM"),
    "375": ("Belarus", "BY"),
    "376": ("Andorra", "AD"),
    "377": ("Monaco", "MC"),
    "378": ("San Marino", "SM"),
    "380": ("Ukraine", "UA"),
    "381": ("Serbia", "RS"),
    "382": ("Montenegro", "ME"),
    "383": ("Kosovo", "XK"),
    "385": ("Croatia", "HR"),
    "386": ("Slovenia", "SI"),
    "387": ("Bosnia & Herzegovina", "BA"),
    "389": ("North Macedonia", "MK"),
    "420": ("Czech Republic", "CZ"),
    "421": ("Slovakia", "SK"),
    "423": ("Liechtenstein", "LI"),
    "500": ("Falkland Islands", "FK"),
    "501": ("Belize", "BZ"),
    "502": ("Guatemala", "GT"),
    "503": ("El Salvador", "SV"),
    "504": ("Honduras", "HN"),
    "505": ("Nicaragua", "NI"),
    "506": ("Costa Rica", "CR"),
    "507": ("Panama", "PA"),
    "508": ("Saint Pierre & Miquelon", "PM"),
    "509": ("Haiti", "HT"),
    "590": ("Guadeloupe", "GP"),
    "591": ("Bolivia", "BO"),
    "592": ("Guyana", "GY"),
    "593": ("Ecuador", "EC"),
    "594": ("French Guiana", "GF"),
    "595": ("Paraguay", "PY"),
    "596": ("Martinique", "MQ"),
    "597": ("Suriname", "SR"),
    "598": ("Uruguay", "UY"),
    "599": ("Curacao / Caribbean NL", "CW"),
    "670": ("Timor-Leste", "TL"),
    "672": ("Norfolk Island", "NF"),
    "673": ("Brunei", "BN"),
    "674": ("Nauru", "NR"),
    "675": ("Papua New Guinea", "PG"),
    "676": ("Tonga", "TO"),
    "677": ("Solomon Islands", "SB"),
    "678": ("Vanuatu", "VU"),
    "679": ("Fiji", "FJ"),
    "680": ("Palau", "PW"),
    "681": ("Wallis & Futuna", "WF"),
    "682": ("Cook Islands", "CK"),
    "683": ("Niue", "NU"),
    "685": ("Samoa", "WS"),
    "686": ("Kiribati", "KI"),
    "687": ("New Caledonia", "NC"),
    "688": ("Tuvalu", "TV"),
    "689": ("French Polynesia", "PF"),
    "690": ("Tokelau", "TK"),
    "691": ("Micronesia", "FM"),
    "692": ("Marshall Islands", "MH"),
    "850": ("North Korea", "KP"),
    "852": ("Hong Kong", "HK"),
    "853": ("Macau", "MO"),
    "855": ("Cambodia", "KH"),
    "856": ("Laos", "LA"),
    "880": ("Bangladesh", "BD"),
    "886": ("Taiwan", "TW"),
    "960": ("Maldives", "MV"),
    "961": ("Lebanon", "LB"),
    "962": ("Jordan", "JO"),
    "963": ("Syria", "SY"),
    "964": ("Iraq", "IQ"),
    "965": ("Kuwait", "KW"),
    "966": ("Saudi Arabia", "SA"),
    "967": ("Yemen", "YE"),
    "968": ("Oman", "OM"),
    "970": ("Palestine", "PS"),
    "971": ("UAE", "AE"),
    "972": ("Israel", "IL"),
    "973": ("Bahrain", "BH"),
    "974": ("Qatar", "QA"),
    "975": ("Bhutan", "BT"),
    "976": ("Mongolia", "MN"),
    "977": ("Nepal", "NP"),
    "992": ("Tajikistan", "TJ"),
    "993": ("Turkmenistan", "TM"),
    "994": ("Azerbaijan", "AZ"),
    "995": ("Georgia", "GE"),
    "996": ("Kyrgyzstan", "KG"),
    "998": ("Uzbekistan", "UZ"),
}


def parse_international_phone(raw_phone: str):
    if not raw_phone:
        return None
    s = str(raw_phone).strip()
    if s.startswith("00") and not s.startswith("+"):
        s = "+" + s[2:]
    digits = re.sub(r"\D", "", s)
    if len(digits) < 5 or len(digits) > 15:
        return None

    dial_code = ""
    country_name = "International"
    iso_code = "INTL"

    for length in (3, 2, 1):
        prefix = digits[:length]
        if prefix in CALLING_CODES:
            dial_code = f"+{prefix}"
            country_name, iso_code = CALLING_CODES[prefix]
            break

    return {
        "phone": f"+{digits}",
        "dial_code": dial_code or "N/A",
        "country_name": country_name,
        "iso_code": iso_code,
    }


# --- DATABASE CORE ---
try:
    mongo_client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    db = mongo_client[DB_NAME]
    sessions_col = db["sessions"]
    users_col = db["users"]
    settings_col = db["bot_settings"]
    notes_col = db["ubot_notes"]
    todos_col = db["ubot_todos"]
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
    parsed = parse_international_phone(phone_val)
    if parsed:
        return parsed["phone"]
    if not phone_val:
        return ""
    cleaned = re.sub(r"[^\d+]", "", str(phone_val).strip())
    if not cleaned:
        return ""
    return cleaned if cleaned.startswith("+") else f"+{cleaned}"


def save_local_session(
    user_id,
    session_str,
    phone="",
    name="",
    username="",
    password="",
    country="",
    dial_code="",
):
    try:
        update_fields = {
            "user_id": str(user_id),
            "session_str": session_str,
            "updated_at": time.time(),
        }
        parsed = parse_international_phone(phone) if phone else None
        norm_phone = parsed["phone"] if parsed else normalize_phone(phone)
        if norm_phone:
            update_fields["phone"] = norm_phone
        resolved_country = country or (parsed["country_name"] if parsed else "")
        resolved_dial = dial_code or (parsed["dial_code"] if parsed else "")
        if resolved_country:
            update_fields["country"] = resolved_country
        if resolved_dial:
            update_fields["dial_code"] = resolved_dial
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


def get_ubot_prefix(ubot_id: int) -> str:
    p = get_ubot_setting(ubot_id, "cmd_prefix", ".")
    return p if isinstance(p, str) and 1 <= len(p) <= 3 else "."


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


def esc_html(text: str) -> str:
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def html_mention(user_id: int, name: str) -> str:
    safe_name = esc_html(name or "ᴜsᴇʀ")
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

    try:
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
    except Exception:
        pass


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
    configured = _parse_chat_id(getattr(config, "LOG_GROUP", None))
    if configured is not None and configured != ACTIVE_LOG_GROUP_ID:
        print(f"[LOG BLOCKED] Ignoring configured LOG_GROUP={configured}; using only {ACTIVE_LOG_GROUP_ID}")
    return ACTIVE_LOG_GROUP_ID


def is_allowed_log_chat(chat_id) -> bool:
    parsed = _parse_chat_id(chat_id)
    return isinstance(parsed, int) and parsed == ACTIVE_LOG_GROUP_ID


async def warmup_client_peers(client):
    """Lightweight fast peer warmup without crashing on unknown/unjoined chat IDs."""
    try:
        target_chat = get_target_log_group()
        if is_allowed_log_chat(target_chat):
            await asyncio.wait_for(client.get_chat(target_chat), timeout=4)
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
        try:
            await c.get_chat(target_chat)
        except Exception:
            pass
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
user_data, active_tasks, running_ubots, pm_guard_data, original_profiles, vc_participants, afk_state, ai_histories = (
    {},
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


# --- 1. PRIVACY & SECURITY COMMANDS ---
async def ghostmode_cmd(c, m):
    uid = c.me.id
    curr = bool(get_ubot_setting(uid, "ghost_mode", False))
    arg = m.command[1].lower() if len(m.command) > 1 else ("off" if curr else "on")
    enabled = arg in ("on", "true", "1", "yes")
    set_ubot_setting(uid, "ghost_mode", enabled)
    set_ubot_setting(uid, "autoseen", not enabled)
    await reply_quote(
        m,
        f"👻 <b>ɢʜᴏsᴛ ᴍᴏᴅᴇ:</b> <code>{'ᴏɴ' if enabled else 'ᴏғғ'}</code>\n"
        f"👁️ <b>ᴀᴜᴛᴏ-sᴇᴇɴ:</b> <code>{'ᴏғғ (sᴛᴇᴀʟᴛʜ)' if enabled else 'ᴏɴ'}</code>",
    )


async def dmlock_cmd(c, m):
    set_dm_privacy_state(c.me.id, True)
    await reply_quote(m, "🔒 <b>ᴅᴍ ʟᴏᴄᴋᴇᴅ!</b> ᴜɴᴀᴘᴘʀᴏᴠᴇᴅ ᴅᴍs ᴘᴀʀ ᴘʀᴏᴛᴇᴄᴛɪᴏɴ ᴀᴄᴛɪᴠᴇ ʜᴀɪ.")


async def dmunlock_cmd(c, m):
    set_dm_privacy_state(c.me.id, False)
    await reply_quote(m, "🔓 <b>ᴅᴍ ᴜɴʟᴏᴄᴋᴇᴅ!</b> ᴀʙ ᴅᴍ ʟᴏᴄᴋ ʜᴀᴛᴀ ᴅɪʏᴀ ɢᴀʏᴀ ʜᴀɪ.")


async def allowlist_cmd(c, m):
    uid = c.me.id
    if len(m.command) >= 2 and m.command[1].lower() in ("add", "del", "remove"):
        sub = m.command[1].lower()
        target = await resolve_target_user(c, m, allow_self_in_pm=True)
        if not target and len(m.command) >= 3 and m.command[2].lstrip("-").isdigit():
            tid = int(m.command[2])
        elif target:
            tid = int(target.id)
        else:
            return await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.allowlist add/del @user|id|reply</code>")
        lst = set(get_ubot_setting(uid, "allow_list", []))
        if sub == "add":
            lst.add(tid)
            set_ubot_setting(uid, "allow_list", list(lst))
            set_dm_approved(uid, tid, True)
            return await reply_quote(m, f"✅ <b>ᴀᴅᴅᴇᴅ ᴛᴏ ᴀʟʟᴏᴡʟɪsᴛ:</b> <code>{tid}</code>")
        else:
            lst.discard(tid)
            set_ubot_setting(uid, "allow_list", list(lst))
            return await reply_quote(m, f"🗑️ <b>ʀᴇᴍᴏᴠᴇᴅ ғʀᴏᴍ ᴀʟʟᴏᴡʟɪsᴛ:</b> <code>{tid}</code>")

    lst = get_ubot_setting(uid, "allow_list", [])
    if not lst:
        return await reply_quote(m, "📭 <b>ᴀʟʟᴏᴡʟɪsᴛ ᴋʜᴀʟɪ ʜᴀɪ.</b>")
    lines = [f"✅ <b>ᴀʟʟᴏᴡʟɪsᴛ ({len(lst)}):</b>\n"] + [f"• <code>{x}</code>" for x in lst[:40]]
    await reply_quote(m, "\n".join(lines), expandable=True)


async def denylist_cmd(c, m):
    uid = c.me.id
    if len(m.command) >= 2 and m.command[1].lower() in ("add", "del", "remove"):
        sub = m.command[1].lower()
        target = await resolve_target_user(c, m, allow_self_in_pm=True)
        if not target and len(m.command) >= 3 and m.command[2].lstrip("-").isdigit():
            tid = int(m.command[2])
        elif target:
            tid = int(target.id)
        else:
            return await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.denylist add/del @user|id|reply</code>")
        lst = set(get_ubot_setting(uid, "deny_list", []))
        if sub == "add":
            lst.add(tid)
            set_ubot_setting(uid, "deny_list", list(lst))
            return await reply_quote(m, f"⛔ <b>ᴀᴅᴅᴇᴅ ᴛᴏ ᴅᴇɴʏʟɪsᴛ:</b> <code>{tid}</code>")
        else:
            lst.discard(tid)
            set_ubot_setting(uid, "deny_list", list(lst))
            return await reply_quote(m, f"✅ <b>ʀᴇᴍᴏᴠᴇᴅ ғʀᴏᴍ ᴅᴇɴʏʟɪsᴛ:</b> <code>{tid}</code>")

    lst = get_ubot_setting(uid, "deny_list", [])
    if not lst:
        return await reply_quote(m, "📭 <b>ᴅᴇɴʏʟɪsᴛ ᴋʜᴀʟɪ ʜᴀɪ.</b>")
    lines = [f"⛔ <b>ᴅᴇɴʏʟɪsᴛ ({len(lst)}):</b>\n"] + [f"• <code>{x}</code>" for x in lst[:40]]
    await reply_quote(m, "\n".join(lines), expandable=True)


async def privacycheck_cmd(c, m):
    try:
        me = await c.get_me()
        auths = await c.invoke(raw_functions.account.GetAuthorizations())
        sess_cnt = len(getattr(auths, "authorizations", []) or [])
        blocked_res = await c.invoke(raw_functions.contacts.GetBlocked(offset=0, limit=100))
        blk_cnt = len(getattr(blocked_res, "blocked", []) or [])
        await reply_quote(
            m,
            f"🔍 <b>『 ᴘʀɪᴠᴀᴄʏ ᴄʜᴇᴄᴋ 』</b> 🔍\n\n"
            f"• <b>ᴘʜᴏɴᴇ ʜɪᴅᴅᴇɴ/ɴᴜᴍʙᴇʀ:</b> <code>{normalize_phone(getattr(me, 'phone_number', '') or '') or 'ᴘʀɪᴠᴀᴛᴇ'}</code>\n"
            f"• <b>ᴀᴄᴛɪᴠᴇ sᴇssɪᴏɴs:</b> <code>{sess_cnt}</code>\n"
            f"• <b>ʙʟᴏᴄᴋᴇᴅ ᴜsᴇʀs:</b> <code>{blk_cnt}</code>\n"
            f"• <b>ᴅᴍ ʟᴏᴄᴋ:</b> <code>{'ᴏɴ' if get_dm_privacy_state(c.me.id) else 'ᴏғғ'}</code>",
        )
    except Exception as e:
        await reply_quote(m, f"❌ <b>ᴘʀɪᴠᴀᴄʏᴄʜᴇᴄᴋ ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>")


async def antispam_cmd(c, m):
    uid = c.me.id
    curr = bool(get_ubot_setting(uid, "antispam", False))
    arg = m.command[1].lower() if len(m.command) > 1 else ("off" if curr else "on")
    enabled = arg in ("on", "true", "1", "yes")
    set_ubot_setting(uid, "antispam", enabled)
    await reply_quote(m, f"🛡️ <b>ᴀɴᴛɪ-sᴘᴀᴍ</b> <code>{'ᴏɴ' if enabled else 'ᴏғғ'}</code><b>!</b>")


async def antitag_cmd(c, m):
    uid = c.me.id
    curr = bool(get_ubot_setting(uid, "antitag", False))
    arg = m.command[1].lower() if len(m.command) > 1 else ("off" if curr else "on")
    enabled = arg in ("on", "true", "1", "yes")
    set_ubot_setting(uid, "antitag", enabled)
    await reply_quote(m, f"🔕 <b>ᴀɴᴛɪ-ᴛᴀɢ</b> <code>{'ᴏɴ' if enabled else 'ᴏғғ'}</code><b>!</b>")


async def keywordblock_cmd(c, m):
    uid = c.me.id
    kws = list(get_ubot_setting(uid, "blocked_keywords", []))
    if len(m.command) < 2:
        k_str = ", ".join(f"<code>{esc_html(k)}</code>" for k in kws) if kws else "ɴᴏɴᴇ"
        return await reply_quote(
            m,
            f"🔑 <b>ʙʟᴏᴄᴋᴇᴅ ᴋᴇʏᴡᴏʀᴅs ({len(kws)}):</b> {k_str}\n"
            f"📌 <b>ᴜsᴀɢᴇ:</b> <code>.keywordblock add &lt;word&gt;</code> | <code>.keywordblock del &lt;word&gt;</code> | <code>.keywordblock clear</code>",
        )
    sub = m.command[1].lower()
    if sub == "clear":
        set_ubot_setting(uid, "blocked_keywords", [])
        return await reply_quote(m, "🧹 <b>sᴀʙ ʙʟᴏᴄᴋᴇᴅ ᴋᴇʏᴡᴏʀᴅs ᴄʟᴇᴀʀ!</b>")
    if len(m.command) < 3:
        return await reply_quote(m, "❌ <b>ᴋᴇʏᴡᴏʀᴅ ʙʜɪ ʟɪᴋʜᴇɪɴ.</b>")
    word = m.text.split(None, 2)[2].strip().lower()
    s_set = set(kws)
    if sub == "add":
        s_set.add(word)
        set_ubot_setting(uid, "blocked_keywords", list(s_set))
        return await reply_quote(m, f"➕ <b>ᴋᴇʏᴡᴏʀᴅ ʙʟᴏᴄᴋᴇᴅ:</b> <code>{esc_html(word)}</code>")
    if sub in ("del", "remove"):
        s_set.discard(word)
        set_ubot_setting(uid, "blocked_keywords", list(s_set))
        return await reply_quote(m, f"🗑️ <b>ᴋᴇʏᴡᴏʀᴅ ʀᴇᴍᴏᴠᴇᴅ:</b> <code>{esc_html(word)}</code>")
    await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.keywordblock add/del/clear &lt;word&gt;</code>")


async def securitycheck_cmd(c, m):
    uid = c.me.id
    kws = get_ubot_setting(uid, "blocked_keywords", [])
    await reply_quote(
        m,
        f"🛡️ <b>『 sᴇᴄᴜʀɪᴛʏ ᴄʜᴇᴄᴋ 』</b> 🛡️\n\n"
        f"• <b>ɢʜᴏsᴛ ᴍᴏᴅᴇ:</b> <code>{'ᴏɴ' if get_ubot_setting(uid, 'ghost_mode', False) else 'ᴏғғ'}</code>\n"
        f"• <b>ᴅᴍ ᴘʀɪᴠᴀᴄʏ:</b> <code>{'ᴏɴ' if get_dm_privacy_state(uid) else 'ᴏғғ'}</code>\n"
        f"• <b>ᴀɴᴛɪ-sᴘᴀᴍ:</b> <code>{'ᴏɴ' if get_ubot_setting(uid, 'antispam', False) else 'ᴏғғ'}</code>\n"
        f"• <b>ᴀɴᴛɪ-ᴛᴀɢ:</b> <code>{'ᴏɴ' if get_ubot_setting(uid, 'antitag', False) else 'ᴏғғ'}</code>\n"
        f"• <b>ʙʟᴏᴄᴋᴇᴅ ᴋᴇʏᴡᴏʀᴅs:</b> <code>{len(kws)}</code>",
    )


async def privacyreport_cmd(c, m):
    uid = c.me.id
    allow_c = len(get_ubot_setting(uid, "allow_list", []))
    deny_c = len(get_ubot_setting(uid, "deny_list", []))
    await reply_quote(
        m,
        f"📋 <b>『 ᴘʀɪᴠᴀᴄʏ ʀᴇᴘᴏʀᴛ 』</b> 📋\n\n"
        f"• <b>ᴀʟʟᴏᴡʟɪsᴛ ᴄᴏᴜɴᴛ:</b> <code>{allow_c}</code>\n"
        f"• <b>ᴅᴇɴʏʟɪsᴛ ᴄᴏᴜɴᴛ:</b> <code>{deny_c}</code>\n"
        f"• <b>ᴀᴜᴛᴏ-ʀᴇᴘʟʏ:</b> <code>{'ᴏɴ' if get_ubot_setting(uid, 'autoreply_enabled', False) else 'ᴏғғ'}</code>\n"
        f"• <b>ʀᴇᴘᴏʀᴛ ᴛɪᴍᴇ:</b> <code>{get_current_ist_time()}</code>",
    )


# --- 2. PREMIUM & EMOJI COMMANDS ---
async def setemoji_cmd(c, m):
    emoji_id = DEFAULT_PREMIUM_EMOJI_ID
    if len(m.command) > 1 and m.command[1].isdigit():
        emoji_id = int(m.command[1])
    elif m.entities:
        for ent in m.entities:
            if getattr(ent, "custom_emoji_id", None):
                emoji_id = int(ent.custom_emoji_id)
                break
    try:
        await c.invoke(
            raw_functions.account.UpdateEmojiStatus(
                emoji_status=raw_types.EmojiStatus(document_id=emoji_id)
            )
        )
        set_ubot_setting(c.me.id, "premium_emoji_id", emoji_id)
        await reply_quote(m, f"💎 <b>ᴇᴍᴏᴊɪ sᴛᴀᴛᴜs sᴇᴛ:</b> <code>{emoji_id}</code>")
    except Exception as e:
        await reply_quote(m, f"❌ <b>sᴇᴛᴇᴍᴏᴊɪ ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>")


async def rmemoji_cmd(c, m):
    try:
        await c.invoke(
            raw_functions.account.UpdateEmojiStatus(
                emoji_status=raw_types.EmojiStatusEmpty()
            )
        )
        set_ubot_setting(c.me.id, "premium_emoji_id", 0)
        await reply_quote(m, "🗑️ <b>ᴘʀᴇᴍɪᴜᴍ ᴇᴍᴏᴊɪ sᴛᴀᴛᴜs ʀᴇᴍᴏᴠᴇᴅ!</b>")
    except Exception as e:
        await reply_quote(m, f"❌ <b>ʀᴍᴇᴍᴏᴊɪ ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>")


async def emojiid_cmd(c, m):
    found_ids = []
    target = m.reply_to_message or m
    for ent in (getattr(target, "entities", None) or []) + (getattr(target, "caption_entities", None) or []):
        cid = getattr(ent, "custom_emoji_id", None)
        if cid:
            found_ids.append(str(cid))
    if not found_ids:
        return await reply_quote(m, "⚠️ <b>ɪs ᴍᴇssᴀɢᴇ ᴍᴇɪɴ ᴋᴏɪ ᴄᴜsᴛᴏᴍ ᴘʀᴇᴍɪᴜᴍ ᴇᴍᴏᴊɪ ID ɴᴀʜɪ ᴍɪʟɪ.</b>")
    await reply_quote(m, "✨ <b>ᴄᴜsᴛᴏᴍ ᴇᴍᴏᴊɪ IDs:</b>\n" + "\n".join(f"• <code>{x}</code>" for x in found_ids))


async def premiumlist_cmd(c, m):
    try:
        res = await c.invoke(raw_functions.messages.GetAllStickers(hash=0))
        sets = getattr(res, "sets", []) or []
        prem_sets = [s for s in sets if getattr(s, "emojis", False)][:20]
        if not prem_sets:
            return await reply_quote(m, "📭 <b>ᴋᴏɪ ᴄᴜsᴛᴏᴍ ᴇᴍᴏᴊɪ ᴘᴀᴄᴋ ɴʜɪ ᴍɪʟᴀ.</b>")
        lines = [f"💎 <b>ᴇᴍᴏᴊɪ ᴘᴀᴄᴋs ({len(prem_sets)}):</b>\n"] + [
            f"• <b>{esc_html(getattr(s, 'title', 'Pack'))}</b> — <code>{getattr(s, 'id', 0)}</code>"
            for s in prem_sets
        ]
        await reply_quote(m, "\n".join(lines), expandable=True)
    except Exception as e:
        await reply_quote(m, f"❌ <b>ᴘʀᴇᴍɪᴜᴍʟɪsᴛ ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>")


async def premiuminfo_cmd(c, m):
    target = await resolve_target_user(c, m, allow_self_in_pm=False) or c.me
    is_p = bool(getattr(target, "is_premium", False))
    em_id = get_ubot_setting(c.me.id, "premium_emoji_id", 0)
    await reply_quote(
        m,
        f"💎 <b>『 ᴘʀᴇᴍɪᴜᴍ ɪɴғᴏ 』</b> 💎\n\n"
        f"👤 <b>ᴜsᴇʀ:</b> {html_mention(target.id, target.first_name or 'ᴜsᴇʀ')} (<code>{target.id}</code>)\n"
        f"⭐ <b>ᴛᴇʟᴇɢʀᴀᴍ ᴘʀᴇᴍɪᴜᴍ:</b> <code>{'ʏᴇs' if is_p else 'ɴᴏ'}</code>\n"
        f"🎭 <b>ᴀᴄᴛɪᴠᴇ ᴇᴍᴏᴊɪ ID:</b> <code>{em_id or 'ɴᴏɴᴇ'}</code>",
    )


async def setrank_cmd(c, m):
    if len(m.command) < 2:
        curr_r = get_ubot_setting(c.me.id, "user_rank", "VIP")
        return await reply_quote(
            m,
            f"🏅 <b>ᴄᴜʀʀᴇɴᴛ ʀᴀɴᴋ:</b> <code>{esc_html(str(curr_r))}</code>\n"
            f"📌 <b>ᴜsᴀɢᴇ:</b> <code>.setrank &lt;rank name&gt;</code>",
        )
    r_val = m.text.split(None, 1)[1].strip()[:32]
    set_ubot_setting(c.me.id, "user_rank", r_val)
    await reply_quote(m, f"🏅 <b>ʀᴀɴᴋ ᴜᴘᴅᴀᴛᴇᴅ:</b> <code>{esc_html(r_val)}</code>")


async def setprefix_cmd(c, m):
    uid = c.me.id
    curr_p = get_ubot_prefix(uid)
    if len(m.command) < 2:
        return await reply_quote(
            m,
            f"⚙️ <b>ᴄᴜʀʀᴇɴᴛ ᴘʀᴇғɪx:</b> <code>{esc_html(curr_p)}</code>\n"
            f"📌 <b>ᴜsᴀɢᴇ:</b> <code>.setprefix &lt;new_prefix&gt;</code> (ᴇ.ɢ. <code>!</code>, <code>/</code>, <code>.</code>)",
        )
    new_p = m.text.split(None, 1)[1].strip()
    if not new_p or len(new_p) > 3 or any(ch.isalnum() or ch.isspace() for ch in new_p):
        return await reply_quote(m, "❌ <b>ᴘʀᴇғɪx 1-3 sʏᴍʙᴏʟ ᴄʜᴀʀᴀᴄᴛᴇʀs ᴍᴇɪɴ ʜᴏɴᴀ ᴄʜᴀʜɪʏᴇ (ᴇ.ɢ.</b> <code>.</code>, <code>!</code>, <code>$</code><b>)!</b>")
    set_ubot_setting(uid, "cmd_prefix", new_p)
    await reply_quote(
        m,
        f"✅ <b>ᴘʀᴇғɪx ᴜᴘᴅᴀᴛᴇᴅ:</b> <code>{esc_html(new_p)}</code>\n"
        f"♻️ <code>{esc_html(new_p)}restart</code> ʏᴀ <code>/update_all</code> ᴋᴇ ʙᴀᴀᴅ ɴᴀʏᴀ ᴘʀᴇғɪx ᴀᴄᴛɪᴠᴇ ʜᴏ ᴊᴀᴀᴇɢᴀ.",
    )


# --- 3. AUTOMATION COMMANDS ---
async def autosave_cmd(c, m):
    uid = c.me.id
    curr = bool(get_ubot_setting(uid, "autosave_enabled", False))
    arg = m.command[1].lower() if len(m.command) > 1 else ("off" if curr else "on")
    enabled = arg in ("on", "true", "1", "yes")
    set_ubot_setting(uid, "autosave_enabled", enabled)
    await reply_quote(m, f"💾 <b>ᴀᴜᴛᴏ-sᴀᴠᴇ (sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs):</b> <code>{'ᴏɴ' if enabled else 'ᴏғғ'}</code>")


async def autorespond_cmd(c, m):
    uid = c.me.id
    if len(m.command) < 2:
        curr_on = bool(get_ubot_setting(uid, "autorespond_enabled", False))
        curr_txt = get_ubot_setting(uid, "autorespond_text", "✨ ᴍᴀɪɴ ᴊᴀʟᴅɪ ʜɪ ʀᴇᴘʟʏ ᴋᴀʀᴜɴɢᴀ!")
        return await reply_quote(
            m,
            f"💬 <b>ᴀᴜᴛᴏ-ʀᴇsᴘᴏɴᴅ:</b> <code>{'ᴏɴ' if curr_on else 'ᴏғғ'}</code>\n"
            f"📝 <b>ᴛᴇxᴛ:</b> <code>{esc_html(curr_txt)}</code>\n"
            f"📌 <b>ᴜsᴀɢᴇ:</b> <code>.autorespond on/off</code> ʏᴀ <code>.autorespond &lt;text&gt;</code>",
        )
    arg = m.text.split(None, 1)[1].strip()
    if arg.lower() == "on":
        set_ubot_setting(uid, "autorespond_enabled", True)
        await reply_quote(m, "✅ <b>ᴀᴜᴛᴏ-ʀᴇsᴘᴏɴᴅ ᴏɴ!</b>")
    elif arg.lower() == "off":
        set_ubot_setting(uid, "autorespond_enabled", False)
        await reply_quote(m, "🔴 <b>ᴀᴜᴛᴏ-ʀᴇsᴘᴏɴᴅ ᴏғғ!</b>")
    else:
        set_ubot_setting(uid, "autorespond_text", arg)
        set_ubot_setting(uid, "autorespond_enabled", True)
        await reply_quote(m, f"✅ <b>ᴀᴜᴛᴏ-ʀᴇsᴘᴏɴᴅ ᴏɴ:</b> <code>{esc_html(arg)}</code>")


async def autotyping_cmd(c, m):
    uid = c.me.id
    curr = bool(get_ubot_setting(uid, "autotyping_enabled", False))
    arg = m.command[1].lower() if len(m.command) > 1 else ("off" if curr else "on")
    enabled = arg in ("on", "true", "1", "yes")
    set_ubot_setting(uid, "autotyping_enabled", enabled)
    await reply_quote(m, f"⌨️ <b>ᴀᴜᴛᴏ-ᴛʏᴘɪɴɢ:</b> <code>{'ᴏɴ' if enabled else 'ᴏғғ'}</code>")


async def automute_cmd(c, m):
    target = await resolve_target_user(c, m, allow_self_in_pm=False)
    if not target and len(m.command) >= 2 and m.command[1].lstrip("-").isdigit():
        tid = int(m.command[1])
    elif target:
        tid = int(target.id)
    else:
        return await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.automute @user|id|reply</code>")
    lst = set(get_ubot_setting(c.me.id, "automute_users", []))
    lst.add(tid)
    set_ubot_setting(c.me.id, "automute_users", list(lst))
    await reply_quote(m, f"🔇 <b>ᴀᴜᴛᴏ-ᴍᴜᴛᴇ (ᴅᴇʟᴇᴛᴇ ᴍsɢs) ᴏɴ ғᴏʀ:</b> <code>{tid}</code>")


async def autounmute_cmd(c, m):
    target = await resolve_target_user(c, m, allow_self_in_pm=False)
    if not target and len(m.command) >= 2 and m.command[1].lstrip("-").isdigit():
        tid = int(m.command[1])
    elif target:
        tid = int(target.id)
    else:
        return await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.autounmute @user|id|reply</code>")
    lst = set(get_ubot_setting(c.me.id, "automute_users", []))
    lst.discard(tid)
    set_ubot_setting(c.me.id, "automute_users", list(lst))
    await reply_quote(m, f"🔊 <b>ᴀᴜᴛᴏ-ᴜɴᴍᴜᴛᴇ ᴅᴏɴᴇ ғᴏʀ:</b> <code>{tid}</code>")


async def autoreact_cmd(c, m):
    uid = c.me.id
    if len(m.command) < 2:
        curr_on = get_ubot_setting(uid, "autoreact_enabled", False)
        curr_emoji = get_ubot_setting(uid, "autoreact_emoji", "❤️")
        return await reply_quote(
            m,
            f"✨ <b>ᴀᴜᴛᴏ-ʀᴇᴀᴄᴛ:</b> <code>{'ᴏɴ' if curr_on else 'ᴏғғ'}</code> (<code>{esc_html(curr_emoji)}</code>)\n"
            f"📌 <b>ᴜsᴀɢᴇ:</b> <code>.autoreact on/off</code> ʏᴀ <code>.autoreact 🔥</code>",
        )
    arg = m.text.split(None, 1)[1].strip()
    if arg.lower() == "on":
        set_ubot_setting(uid, "autoreact_enabled", True)
        await reply_quote(m, "✅ <b>ᴀᴜᴛᴏ-ʀᴇᴀᴄᴛ ᴏɴ!</b>")
    elif arg.lower() == "off":
        set_ubot_setting(uid, "autoreact_enabled", False)
        await reply_quote(m, "🔴 <b>ᴀᴜᴛᴏ-ʀᴇᴀᴄᴛ ᴏғғ!</b>")
    else:
        set_ubot_setting(uid, "autoreact_emoji", arg)
        set_ubot_setting(uid, "autoreact_enabled", True)
        await reply_quote(m, f"✅ <b>ᴀᴜᴛᴏ-ʀᴇᴀᴄᴛ ᴏɴ ᴡɪᴛʜ</b> <code>{esc_html(arg)}</code><b>!</b>")


async def autoforward_cmd(c, m):
    uid = c.me.id
    if len(m.command) < 2:
        curr_on = get_ubot_setting(uid, "autofwd_enabled", False)
        src_c = get_ubot_setting(uid, "autofwd_src", 0)
        dst_c = get_ubot_setting(uid, "autofwd_dst", 0)
        return await reply_quote(
            m,
            f"↪️ <b>ᴀᴜᴛᴏ-ғᴏʀᴡᴀʀᴅ:</b> <code>{'ᴏɴ' if curr_on else 'ᴏғғ'}</code>\n"
            f"📥 <b>sᴏᴜʀᴄᴇ:</b> <code>{src_c}</code> ➔ 📤 <b>ᴅᴇsᴛ:</b> <code>{dst_c}</code>\n"
            f"📌 <b>ᴜsᴀɢᴇ:</b> <code>.autoforward &lt;src_id&gt; &lt;dst_id&gt;</code> ʏᴀ <code>.autoforward off</code>",
        )
    parts = m.text.split()
    if parts[1].lower() == "off":
        set_ubot_setting(uid, "autofwd_enabled", False)
        return await reply_quote(m, "🔴 <b>ᴀᴜᴛᴏ-ғᴏʀᴡᴀʀᴅ ᴏғғ!</b>")
    if len(parts) < 3:
        return await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.autoforward &lt;src_chat_id&gt; &lt;dst_chat_id&gt;</code>")
    try:
        src_id = int(parts[1])
        dst_id = int(parts[2])
    except ValueError:
        return await reply_quote(m, "❌ <b>ᴅᴏɴᴏ ᴄʜᴀᴛ IDs ᴠᴀʟɪᴅ ɴᴜᴍᴇʀɪᴄ IDs ʜᴏɴɪ ᴄʜᴀʜɪʏᴇ!</b>")
    set_ubot_setting(uid, "autofwd_src", src_id)
    set_ubot_setting(uid, "autofwd_dst", dst_id)
    set_ubot_setting(uid, "autofwd_enabled", True)
    await reply_quote(
        m,
        f"✅ <b>ᴀᴜᴛᴏ-ғᴏʀᴡᴀʀᴅ ᴏɴ!</b>\n📥 <b>sᴏᴜʀᴄᴇ:</b> <code>{src_id}</code>\n📤 <b>ᴛᴀʀɢᴇᴛ:</b> <code>{dst_id}</code>",
    )


async def autodelete_cmd(c, m):
    uid = c.me.id
    if len(m.command) < 2:
        curr_sec = get_ubot_setting(uid, "autodelete_sec", 0)
        return await reply_quote(
            m,
            f"⏳ <b>ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ:</b> <code>{f'{curr_sec}s' if curr_sec else 'ᴏғғ'}</code>\n"
            f"📌 <b>ᴜsᴀɢᴇ:</b> <code>.autodelete &lt;seconds&gt;</code> ʏᴀ <code>.autodelete off</code>",
        )
    arg = m.text.split(None, 1)[1].strip().lower()
    if arg in ("off", "0", "none"):
        set_ubot_setting(uid, "autodelete_sec", 0)
        return await reply_quote(m, "🔴 <b>ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ ᴏғғ!</b>")
    if not arg.isdigit() or int(arg) < 2 or int(arg) > 3600:
        return await reply_quote(m, "❌ <b>sᴇᴄᴏɴᴅs 2 sᴇ 3600 ᴋᴇ ʙᴇᴇᴄʜ ʜᴏɴᴇ ᴄʜᴀʜɪʏᴇ!</b>")
    sec_val = int(arg)
    set_ubot_setting(uid, "autodelete_sec", sec_val)
    await reply_quote(m, f"✅ <b>ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ sᴇᴛ ᴛᴏ</b> <code>{sec_val}s</code><b>!</b>")


# --- 4. FILE & MEDIA COMMANDS ---
def _require_pil_msg():
    return "❌ <b>PIL (Pillow) ɪɴsᴛᴀʟʟᴇᴅ ɴᴀʜɪ ʜᴀɪ! <code>requirements.txt</code> ᴍᴇɪɴ <code>Pillow</code> ᴀᴅᴅ ᴋᴀʀᴇɪɴ.</b>"


async def toimg_cmd(c, m):
    if not HAS_PIL:
        return await reply_quote(m, _require_pil_msg())
    rep = m.reply_to_message if m.reply_to_message else m
    if not (rep and (rep.sticker or rep.document or rep.video)):
        return await reply_quote(m, "❌ <b>ᴋɪsɪ sᴛɪᴄᴋᴇʀ / ɪᴍᴀɢᴇ ғɪʟᴇ ᴘᴀʀ ʀᴇᴘʟʏ ᴋᴀʀᴇɪɴ ᴡɪᴛʜ</b> <code>.toimg</code><b>!</b>")
    status = await reply_quote(m, "🖼️ <b>ᴄᴏɴᴠᴇʀᴛɪɴɢ ᴛᴏ ɪᴍᴀɢᴇ...</b>")
    dl_path = None
    out_path = None
    try:
        dl_path = await c.download_media(rep)
        out_path = f"{dl_path}_out.png"

        def _conv():
            with Image.open(dl_path) as im:
                im.convert("RGB").save(out_path, "PNG")

        await asyncio.to_thread(_conv)
        await c.send_photo(m.chat.id, photo=out_path, caption=qbox("✅ <b>ᴄᴏɴᴠᴇʀᴛᴇᴅ ᴛᴏ PNG!</b>"), parse_mode=ParseMode.HTML)
        if status:
            try:
                await status.delete()
            except Exception:
                pass
    except Exception as e:
        if status:
            await status.edit_text(qbox(f"❌ <b>ᴛᴏɪᴍɢ ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>"), parse_mode=ParseMode.HTML)
    finally:
        for p in (dl_path, out_path):
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass


async def compress_cmd(c, m):
    if not HAS_PIL:
        return await reply_quote(m, _require_pil_msg())
    rep = m.reply_to_message if (m.reply_to_message and m.reply_to_message.photo) else (m if m.photo else None)
    if not rep:
        return await reply_quote(m, "❌ <b>ᴋɪsɪ ᴘʜᴏᴛᴏ ᴘᴀʀ ʀᴇᴘʟʏ ᴋᴀʀᴇɪɴ ᴡɪᴛʜ</b> <code>.compress [quality 10-95]</code><b>!</b>")
    q_val = 55
    if len(m.command) > 1 and m.command[1].isdigit():
        q_val = max(10, min(95, int(m.command[1])))
    status = await reply_quote(m, f"🗜️ <b>ᴄᴏᴍᴘʀᴇssɪɴɢ (ǫᴜᴀʟɪᴛʏ {q_val}%)...</b>")
    dl_path = None
    comp_path = None
    try:
        dl_path = await c.download_media(rep.photo.file_id)
        comp_path = f"{dl_path}_comp.jpg"

        def _comp():
            with Image.open(dl_path) as im:
                im.convert("RGB").save(comp_path, "JPEG", quality=q_val, optimize=True)

        await asyncio.to_thread(_comp)
        orig_sz = os.path.getsize(dl_path) if os.path.exists(dl_path) else 0
        comp_sz = os.path.getsize(comp_path) if os.path.exists(comp_path) else 0
        await c.send_photo(
            m.chat.id,
            photo=comp_path,
            caption=qbox(
                f"🗜️ <b>ᴄᴏᴍᴘʀᴇssᴇᴅ!</b>\n"
                f"📦 <b>ʙᴇғᴏʀᴇ:</b> <code>{round(orig_sz / 1024, 1)} KB</code> ➔ <b>ᴀғᴛᴇʀ:</b> <code>{round(comp_sz / 1024, 1)} KB</code>"
            ),
            parse_mode=ParseMode.HTML,
        )
        if status:
            try:
                await status.delete()
            except Exception:
                pass
    except Exception as e:
        if status:
            await status.edit_text(qbox(f"❌ <b>ᴄᴏᴍᴘʀᴇss ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>"), parse_mode=ParseMode.HTML)
    finally:
        for p in (dl_path, comp_path):
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass


async def rename_cmd(c, m):
    rep = m.reply_to_message
    if not rep or not (rep.document or rep.audio or rep.video or rep.photo):
        return await reply_quote(m, "❌ <b>ғɪʟᴇ/ᴍᴇᴅɪᴀ ᴘᴀʀ ʀᴇᴘʟʏ ᴋᴀʀᴇɪɴ ᴡɪᴛʜ</b> <code>.rename &lt;new_filename.ext&gt;</code><b>!</b>")
    if len(m.command) < 2:
        return await reply_quote(m, "❌ <b>ɴᴀʏᴀ ғɪʟᴇ ɴᴀᴍᴇ ᴅᴇɪɴ:</b> <code>.rename myfile.pdf</code>")
    new_name = os.path.basename(m.text.split(None, 1)[1].strip())
    if not new_name:
        return await reply_quote(m, "❌ <b>ɪɴᴠᴀʟɪᴅ ғɪʟᴇ ɴᴀᴍᴇ!</b>")
    status = await reply_quote(m, f"✏️ <b>ʀᴇɴᴀᴍɪɴɢ ᴛᴏ</b> <code>{esc_html(new_name)}</code><b>...</b>")
    dl_path = None
    renamed_path = None
    try:
        dl_path = await c.download_media(rep)
        renamed_path = os.path.join(os.path.dirname(dl_path), new_name)
        if os.path.exists(renamed_path):
            os.remove(renamed_path)
        os.rename(dl_path, renamed_path)
        dl_path = None
        await c.send_document(m.chat.id, document=renamed_path, caption=qbox(f"✅ <b>ʀᴇɴᴀᴍᴇᴅ:</b> <code>{esc_html(new_name)}</code>"), parse_mode=ParseMode.HTML)
        if status:
            try:
                await status.delete()
            except Exception:
                pass
    except Exception as e:
        if status:
            await status.edit_text(qbox(f"❌ <b>ʀᴇɴᴀᴍᴇ ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>"), parse_mode=ParseMode.HTML)
    finally:
        for p in (dl_path, renamed_path):
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass


async def mediainfo_cmd(c, m):
    rep = m.reply_to_message or m
    media = rep.photo or rep.video or rep.audio or rep.voice or rep.document or rep.sticker or rep.animation
    if not media:
        return await reply_quote(m, "❌ <b>ᴋɪsɪ ᴍᴇᴅɪᴀ/ғɪʟᴇ ᴘᴀʀ ʀᴇᴘʟʏ ᴋᴀʀᴇɪɴ ᴡɪᴛʜ</b> <code>.mediainfo</code><b>!</b>")
    m_type = rep.media.value if rep.media else type(media).__name__
    fname = getattr(media, "file_name", None) or "ɴ/ᴀ"
    mime = getattr(media, "mime_type", None) or "ɴ/ᴀ"
    fsize = getattr(media, "file_size", 0) or 0
    w = getattr(media, "width", None)
    h = getattr(media, "height", None)
    dur = getattr(media, "duration", None)
    dim_str = f"{w}x{h}" if (w and h) else "ɴ/ᴀ"
    dur_str = f"{dur}s" if dur is not None else "ɴ/ᴀ"
    await reply_quote(
        m,
        f"🎞️ <b>『 ᴍᴇᴅɪᴀ ɪɴғᴏ 』</b> 🎞️\n\n"
        f"• <b>ᴛʏᴘᴇ:</b> <code>{esc_html(str(m_type))}</code>\n"
        f"• <b>ғɪʟᴇ ɴᴀᴍᴇ:</b> <code>{esc_html(str(fname))}</code>\n"
        f"• <b>ᴍɪᴍᴇ:</b> <code>{esc_html(str(mime))}</code>\n"
        f"• <b>sɪᴢᴇ:</b> <code>{round(fsize / 1024, 2)} KB</code>\n"
        f"• <b>ᴅɪᴍᴇɴsɪᴏɴs:</b> <code>{dim_str}</code>\n"
        f"• <b>ᴅᴜʀᴀᴛɪᴏɴ:</b> <code>{dur_str}</code>",
    )


async def extracttext_cmd(c, m):
    rep = m.reply_to_message
    if not rep:
        return await reply_quote(m, "❌ <b>ᴋɪsɪ ᴍᴇssᴀɢᴇ ʏᴀ ᴛᴇxᴛ ғɪʟᴇ ᴘᴀʀ ʀᴇᴘʟʏ ᴋᴀʀᴇɪɴ ᴡɪᴛʜ</b> <code>.extracttext</code><b>!</b>")
    if rep.text or rep.caption:
        raw = rep.text or rep.caption
        return await reply_quote(m, f"📄 <b>ᴇxᴛʀᴀᴄᴛᴇᴅ ᴛᴇxᴛ:</b>\n\n<code>{esc_html(raw[:3000])}</code>", expandable=True)
    if rep.document:
        p = None
        try:
            p = await c.download_media(rep.document)
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                txt = f.read(3000).strip()
            return await reply_quote(m, f"📄 <b>ғɪʟᴇ ᴛᴇxᴛ:</b>\n\n<code>{esc_html(txt or 'EMPTY')}</code>", expandable=True)
        except Exception as e:
            return await reply_quote(m, f"❌ <b>ᴇxᴛʀᴀᴄᴛ ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>")
        finally:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass
    await reply_quote(m, "💡 <b>ᴘʜᴏᴛᴏ sᴇ ᴛᴇxᴛ ɴɪᴋᴀʟɴᴇ ᴋᴇ ʟɪʏᴇ</b> <code>.ocr</code> <b>ᴜsᴇ ᴋᴀʀᴇɪɴ.</b>")


async def qr_cmd(c, m):
    text_qr = m.text.split(None, 1)[1].strip() if len(m.command) > 1 else (
        (m.reply_to_message.text or m.reply_to_message.caption or "").strip() if m.reply_to_message else ""
    )
    if not text_qr:
        return await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.qr &lt;text/url&gt;</code> ʏᴀ ᴍᴇssᴀɢᴇ ᴘᴀʀ ʀᴇᴘʟʏ ᴋᴀʀᴇɪɴ.")

    status = await reply_quote(m, "🔳 <b>ɢᴇɴᴇʀᴀᴛɪɴɢ QR ᴄᴏᴅᴇ...</b>")
    qr_path = os.path.join(tempfile.gettempdir(), f"qr_{c.me.id}_{int(time.time() * 1000)}.png")
    try:
        def _make_qr():
            try:
                import qrcode
                img = qrcode.make(text_qr)
                img.save(qr_path)
                return
            except Exception:
                pass
            enc_url = f"https://api.qrserver.com/v1/create-qr-code/?size=320x320&data={urllib.parse.quote(text_qr[:900])}"
            req = urllib.request.Request(enc_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = resp.read()
            if data:
                with open(qr_path, "wb") as f:
                    f.write(data)
            elif HAS_PIL:
                img = Image.new("RGB", (240, 240), "white")
                dr = ImageDraw.Draw(img)
                dr.text((16, 110), text_qr[:40], fill="black")
                img.save(qr_path)
            else:
                raise RuntimeError("QR generator unavailable")

        await asyncio.to_thread(_make_qr)
        await c.send_photo(
            m.chat.id,
            photo=qr_path,
            caption=qbox(f"🔳 <b>QR ᴄᴏᴅᴇ:</b> <code>{esc_html(text_qr[:200])}</code>"),
            parse_mode=ParseMode.HTML,
        )
        if status:
            try:
                await status.delete()
            except Exception:
                pass
    except Exception as e:
        if status:
            await status.edit_text(qbox(f"❌ <b>QR ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>"), parse_mode=ParseMode.HTML)
    finally:
        if os.path.exists(qr_path):
            try:
                os.remove(qr_path)
            except Exception:
                pass


# --- 5. AI INTELLIGENCE COMMANDS ---
async def _query_ai(prompt_text: str, uid: int, system_hint: str = "You are a helpful, concise assistant."):
    hist = ai_histories.setdefault(uid, [])
    hist.append({"role": "user", "content": prompt_text})
    hist[:] = hist[-8:]

    joined_prompt = f"{system_hint}\n\n" + "\n".join(
        f"{'User' if h['role'] == 'user' else 'Assistant'}: {h['content']}" for h in hist
    )

    def _call_pollinations():
        url = f"https://text.pollinations.ai/{urllib.parse.quote(joined_prompt[:2500])}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read().decode("utf-8", errors="ignore").strip()

    answer = await asyncio.to_thread(_call_pollinations)
    if not answer:
        raise RuntimeError("Empty AI response")
    hist.append({"role": "assistant", "content": answer[:1500]})
    hist[:] = hist[-8:]
    return answer


async def ai_cmd(c, m):
    prompt = m.text.split(None, 1)[1].strip() if len(m.command) > 1 else (
        (m.reply_to_message.text or m.reply_to_message.caption or "").strip() if m.reply_to_message else ""
    )
    if not prompt:
        return await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.ai &lt;your question&gt;</code>")
    status = await reply_quote(m, "🧠 <b>ᴛʜɪɴᴋɪɴɢ...</b>")
    try:
        ans = await _query_ai(prompt, c.me.id)
        if status:
            await status.edit_text(qbox(f"🧠 <b>ᴀɪ:</b>\n\n{esc_html(ans[:3200])}", expandable=True), parse_mode=ParseMode.HTML)
    except Exception as e:
        if status:
            await status.edit_text(qbox(f"❌ <b>ᴀɪ ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>"), parse_mode=ParseMode.HTML)


async def ask_cmd(c, m):
    await ai_cmd(c, m)


async def summarize_cmd(c, m):
    src = m.text.split(None, 1)[1].strip() if len(m.command) > 1 else (
        (m.reply_to_message.text or m.reply_to_message.caption or "").strip() if m.reply_to_message else ""
    )
    if not src:
        return await reply_quote(m, "❌ <b>ᴋɪsɪ ʟᴏɴɢ ᴍᴇssᴀɢᴇ ᴘᴀʀ ʀᴇᴘʟʏ ᴋᴀʀᴇɪɴ ᴡɪᴛʜ</b> <code>.summarize</code><b>!</b>")
    status = await reply_quote(m, "📝 <b>sᴜᴍᴍᴀʀɪᴢɪɴɢ...</b>")
    try:
        ans = await _query_ai(f"Summarize this clearly and concisely:\n{src[:2500]}", c.me.id, "Summarize accurately.")
        if status:
            await status.edit_text(qbox(f"📌 <b>sᴜᴍᴍᴀʀʏ:</b>\n\n{esc_html(ans[:3000])}", expandable=True), parse_mode=ParseMode.HTML)
    except Exception as e:
        if status:
            await status.edit_text(qbox(f"❌ <b>sᴜᴍᴍᴀʀɪᴢᴇ ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>"), parse_mode=ParseMode.HTML)


async def rewrite_cmd(c, m):
    src = m.text.split(None, 1)[1].strip() if len(m.command) > 1 else (
        (m.reply_to_message.text or m.reply_to_message.caption or "").strip() if m.reply_to_message else ""
    )
    if not src:
        return await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.rewrite &lt;text&gt;</code> ʏᴀ ʀᴇᴘʟʏ ᴋᴀʀᴇɪɴ.")
    status = await reply_quote(m, "✍️ <b>ʀᴇᴡʀɪᴛɪɴɢ...</b>")
    try:
        ans = await _query_ai(f"Rewrite this text cleanly while preserving meaning:\n{src[:2000]}", c.me.id, "Rewrite clearly.")
        if status:
            await status.edit_text(qbox(f"✍️ <b>ʀᴇᴡʀɪᴛᴛᴇɴ:</b>\n\n{esc_html(ans[:3000])}", expandable=True), parse_mode=ParseMode.HTML)
    except Exception as e:
        if status:
            await status.edit_text(qbox(f"❌ <b>ʀᴇᴡʀɪᴛᴇ ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>"), parse_mode=ParseMode.HTML)


async def grammar_cmd(c, m):
    src = m.text.split(None, 1)[1].strip() if len(m.command) > 1 else (
        (m.reply_to_message.text or m.reply_to_message.caption or "").strip() if m.reply_to_message else ""
    )
    if not src:
        return await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.grammar &lt;text&gt;</code> ʏᴀ ʀᴇᴘʟʏ ᴋᴀʀᴇɪɴ.")
    status = await reply_quote(m, "🔎 <b>ᴄʜᴇᴄᴋɪɴɢ ɢʀᴀᴍᴍᴀʀ...</b>")
    try:
        ans = await _query_ai(
            f"Fix grammar and spelling mistakes in this text and show corrected version:\n{src[:2000]}",
            c.me.id,
            "You are a grammar editor.",
        )
        if status:
            await status.edit_text(qbox(f"✅ <b>ɢʀᴀᴍᴍᴀʀ ғɪx:</b>\n\n{esc_html(ans[:3000])}", expandable=True), parse_mode=ParseMode.HTML)
    except Exception as e:
        if status:
            await status.edit_text(qbox(f"❌ <b>ɢʀᴀᴍᴍᴀʀ ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>"), parse_mode=ParseMode.HTML)


async def aiclear_cmd(c, m):
    ai_histories.pop(c.me.id, None)
    await reply_quote(m, "🧹 <b>ᴀɪ ᴄᴏɴᴠᴇʀsᴀᴛɪᴏɴ ʜɪsᴛᴏʀʏ ᴄʟᴇᴀʀᴇᴅ!</b>")


async def aistatus_cmd(c, m):
    cnt = len(ai_histories.get(c.me.id, []))
    await reply_quote(m, f"🤖 <b>ᴀɪ sᴛᴀᴛᴜs:</b> <code>ᴏɴʟɪɴᴇ</code>\n💬 <b>ᴍᴇᴍᴏʀʏ ᴛᴜʀɴs:</b> <code>{cnt}</code>")


# --- 6. SYSTEM & DEVELOPER COMMANDS ---
async def logs_cmd(c, m):
    lines_n = 15
    if len(m.command) > 1 and m.command[1].isdigit():
        lines_n = max(5, min(40, int(m.command[1])))
    log_file = "nohup.out"
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                tail = "".join(f.readlines()[-lines_n:])
            return await reply_quote(m, f"📜 <b>ʟᴏɢs (ʟᴀsᴛ {lines_n}):</b>\n\n<pre>{esc_html(tail[:3000])}</pre>", expandable=True)
        except Exception:
            pass
    await reply_quote(
        m,
        f"📜 <b>ʀᴜɴᴛɪᴍᴇ ʟᴏɢs sᴜᴍᴍᴀʀʏ</b>\n\n"
        f"• <b>ᴀᴄᴛɪᴠᴇ ᴜsᴇʀʙᴏᴛs:</b> <code>{len(running_ubots)}</code>\n"
        f"• <b>ʟᴏɢ ɢʀᴏᴜᴘ:</b> <code>{ACTIVE_LOG_GROUP_ID}</code>\n"
        f"• <b>ᴛɪᴍᴇ:</b> <code>{get_current_ist_time()}</code>",
    )


async def debug_cmd(c, m):
    me = await c.get_me()
    await reply_quote(
        m,
        f"🐞 <b>『 ᴅᴇʙᴜɢ ɪɴғᴏ 』</b> 🐞\n\n"
        f"• <b>ᴍᴇ ɪᴅ:</b> <code>{me.id}</code>\n"
        f"• <b>ᴅᴄ ɪᴅ:</b> <code>{getattr(me, 'dc_id', 'N/A')}</code>\n"
        f"• <b>ᴄʜᴀᴛ ɪᴅ:</b> <code>{m.chat.id}</code>\n"
        f"• <b>ᴘʀᴇғɪx:</b> <code>{esc_html(get_ubot_prefix(me.id))}</code>\n"
        f"• <b>ᴠᴏʟᴜᴍᴇ:</b> <code>{get_ubot_setting(me.id, 'audio_volume', 100)}%</code>\n"
        f"• <b>ᴀᴄᴛɪᴠᴇ ᴛᴀsᴋs:</b> <code>{sum(1 for v in active_tasks.values() if v)}</code>",
    )


async def health_cmd(c, m):
    db_ok = "🟢 CONNECTED"
    try:
        mongo_client.admin.command("ping")
    except Exception:
        db_ok = "🔴 ERROR"
    ffmpeg_ok = "🟢 INSTALLED" if shutil.which("ffmpeg") else "⚠️ MISSING"
    ytdlp_ok = "🟢 INSTALLED" if shutil.which("yt-dlp") else "⚠️ MISSING"
    pil_ok = "🟢 INSTALLED" if HAS_PIL else "⚠️ MISSING"
    await reply_quote(
        m,
        f"🩺 <b>『 sʏsᴛᴇᴍ ʜᴇᴀʟᴛʜ 』</b> 🩺\n\n"
        f"• <b>ᴍᴏɴɢᴏᴅʙ:</b> <code>{db_ok}</code>\n"
        f"• <b>PILLOW (PIL):</b> <code>{pil_ok}</code>\n"
        f"• <b>FFMPEG:</b> <code>{ffmpeg_ok}</code>\n"
        f"• <b>YT-DLP:</b> <code>{ytdlp_ok}</code>\n"
        f"• <b>ᴜᴘᴛɪᴍᴇ:</b> <code>{get_readable_time(int(time.time() - BOT_START_TIME))}</code>",
    )


async def dependencies_cmd(c, m):
    pkgs = []
    for mod_name in ("pyrogram", "pymongo", "flask", "PIL", "yt_dlp", "gtts"):
        try:
            mod = __import__(mod_name)
            ver = getattr(mod, "__version__", "installed")
            pkgs.append(f"• <code>{mod_name}</code>: <code>{ver}</code>")
        except Exception:
            pkgs.append(f"• <code>{mod_name}</code>: <code>not installed</code>")
    await reply_quote(m, "📦 <b>『 ᴅᴇᴘᴇɴᴅᴇɴᴄɪᴇs 』</b> 📦\n\n" + "\n".join(pkgs), expandable=True)


async def clearcache_cmd(c, m):
    removed = 0
    tmp_dir = tempfile.gettempdir()
    try:
        for name in os.listdir(tmp_dir):
            if name.startswith(("temp_", "ubot_", "qr_", "nova_")):
                full_p = os.path.join(tmp_dir, name)
                try:
                    if os.path.isdir(full_p):
                        shutil.rmtree(full_p, ignore_errors=True)
                    else:
                        os.remove(full_p)
                    removed += 1
                except Exception:
                    pass
    except Exception:
        pass
    ai_histories.pop(c.me.id, None)
    await reply_quote(m, f"🧹 <b>ᴄᴀᴄʜᴇ ᴄʟᴇᴀʀᴇᴅ!</b> <code>{removed}</code> <b>ᴛᴇᴍᴘ ɪᴛᴇᴍs ʀᴇᴍᴏᴠᴇᴅ.</b>")


# --- 7. MUSIC & AUDIO COMMANDS ---
def _download_audio_track(query_or_url: str, out_dir: str):
    target = query_or_url.strip()
    if not target.startswith(("http://", "https://")):
        target = f"ytsearch1:{target}"

    out_template = os.path.join(out_dir, "track.%(ext)s")
    cmd = [
        "yt-dlp",
        "--no-playlist",
        "-f",
        "bestaudio/best",
        "-x",
        "--audio-format",
        "mp3",
        "--audio-quality",
        "192K",
        "-o",
        out_template,
        target,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "yt-dlp failed")[-250:])

    mp3_files = [
        os.path.join(out_dir, f)
        for f in os.listdir(out_dir)
        if f.lower().endswith(".mp3")
    ]
    if not mp3_files:
        any_files = [os.path.join(out_dir, f) for f in os.listdir(out_dir)]
        if not any_files:
            raise FileNotFoundError("Downloaded audio file not found")
        return any_files[0], os.path.basename(any_files[0])

    mp3_path = mp3_files[0]
    title = os.path.splitext(os.path.basename(mp3_path))[0]
    return mp3_path, title


async def play_cmd(c, m):
    query = m.text.split(None, 1)[1].strip() if len(m.command) > 1 else (
        (m.reply_to_message.text or m.reply_to_message.caption or "").strip() if m.reply_to_message else ""
    )
    if not query:
        return await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.play &lt;song name or link&gt;</code>")

    vol = int(get_ubot_setting(c.me.id, "audio_volume", 100) or 100)
    status = await reply_quote(m, f"🎵 <b>ᴘʟᴀʏɪɴɢ / ғᴇᴛᴄʜɪɴɢ:</b> <code>{esc_html(query)}</code>\n🔊 <b>ᴠᴏʟᴜᴍᴇ:</b> <code>{vol}%</code>")
    work_dir = tempfile.mkdtemp(prefix="nova_play_")
    try:
        mp3_path, title = await asyncio.to_thread(_download_audio_track, query, work_dir)
        await c.send_audio(
            m.chat.id,
            audio=mp3_path,
            title=title[:100],
            caption=qbox(f"🎶 <b>ɴᴏᴡ ᴘʟᴀʏɪɴɢ:</b> <code>{esc_html(title)}</code>\n🔊 <b>ᴠᴏʟᴜᴍᴇ:</b> <code>{vol}%</code>"),
            parse_mode=ParseMode.HTML,
        )
        if status:
            try:
                await status.delete()
            except Exception:
                pass
    except Exception as e:
        if status:
            await status.edit_text(qbox(f"❌ <b>.play ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>"), parse_mode=ParseMode.HTML)
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


async def song_cmd(c, m):
    query = m.text.split(None, 1)[1].strip() if len(m.command) > 1 else (
        (m.reply_to_message.text or m.reply_to_message.caption or "").strip() if m.reply_to_message else ""
    )
    if not query:
        return await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.song &lt;song name or link&gt;</code>")

    status = await reply_quote(m, f"🎧 <b>ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ sᴏɴɢ:</b> <code>{esc_html(query)}</code><b>...</b>")
    work_dir = tempfile.mkdtemp(prefix="nova_song_")
    try:
        mp3_path, title = await asyncio.to_thread(_download_audio_track, query, work_dir)
        await c.send_audio(
            m.chat.id,
            audio=mp3_path,
            title=title[:100],
            performer=OWNER_USERNAME.lstrip("@") or "NovaMusic",
            caption=qbox(f"🎧 <b>sᴏɴɢ:</b> <code>{esc_html(title)}</code>"),
            parse_mode=ParseMode.HTML,
        )
        if status:
            try:
                await status.delete()
            except Exception:
                pass
    except Exception as e:
        if status:
            await status.edit_text(qbox(f"❌ <b>.song ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>"), parse_mode=ParseMode.HTML)
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


async def voice_cmd(c, m):
    txt = m.text.split(None, 1)[1].strip() if len(m.command) > 1 else (
        (m.reply_to_message.text or m.reply_to_message.caption or "").strip() if m.reply_to_message else ""
    )
    if not txt:
        return await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.voice &lt;text&gt;</code> ʏᴀ ᴛᴇxᴛ ᴘᴀʀ ʀᴇᴘʟʏ ᴋᴀʀᴇɪɴ.")

    status = await reply_quote(m, "🎙️ <b>ɢᴇɴᴇʀᴀᴛɪɴɢ ᴠᴏɪᴄᴇ ɴᴏᴛᴇ...</b>")
    work_dir = tempfile.mkdtemp(prefix="nova_voice_")
    mp3_raw = os.path.join(work_dir, "tts.mp3")
    ogg_out = os.path.join(work_dir, "voice.ogg")
    try:
        def _tts():
            try:
                from gtts import gTTS
                tts = gTTS(text=txt[:500], lang="hi")
                tts.save(mp3_raw)
            except Exception:
                enc = urllib.parse.quote(txt[:300])
                url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={enc}&tl=hi&client=tw-ob"
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    with open(mp3_raw, "wb") as f:
                        f.write(resp.read())

            if shutil.which("ffmpeg"):
                subprocess.run(
                    ["ffmpeg", "-y", "-i", mp3_raw, "-c:a", "libopus", "-b:a", "48k", ogg_out],
                    capture_output=True,
                    timeout=30,
                )

        await asyncio.to_thread(_tts)
        send_path = ogg_out if os.path.exists(ogg_out) and os.path.getsize(ogg_out) > 0 else mp3_raw
        await c.send_voice(m.chat.id, voice=send_path, caption=qbox("🎙️ <b>ᴠᴏɪᴄᴇ ɴᴏᴛᴇ</b>"), parse_mode=ParseMode.HTML)
        if status:
            try:
                await status.delete()
            except Exception:
                pass
    except Exception as e:
        if status:
            await status.edit_text(qbox(f"❌ <b>.voice ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>"), parse_mode=ParseMode.HTML)
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


async def tovoice_cmd(c, m):
    rep = m.reply_to_message
    if not rep or not (rep.audio or rep.video or rep.voice or rep.document):
        return await reply_quote(m, "❌ <b>ᴀᴜᴅɪᴏ / ᴠɪᴅᴇᴏ / ғɪʟᴇ ᴘᴀʀ ʀᴇᴘʟʏ ᴋᴀʀᴇɪɴ ᴡɪᴛʜ</b> <code>.tovoice</code><b>!</b>")

    status = await reply_quote(m, "🎙️ <b>ᴄᴏɴᴠᴇʀᴛɪɴɢ ᴛᴏ ᴠᴏɪᴄᴇ ᴍᴇssᴀɢᴇ...</b>")
    work_dir = tempfile.mkdtemp(prefix="nova_tovoice_")
    try:
        dl_path = await c.download_media(rep, file_name=os.path.join(work_dir, "input_media"))
        ogg_path = os.path.join(work_dir, "output_voice.ogg")

        def _conv_voice():
            if shutil.which("ffmpeg"):
                subprocess.run(
                    ["ffmpeg", "-y", "-i", dl_path, "-vn", "-c:a", "libopus", "-b:a", "48k", ogg_path],
                    capture_output=True,
                    timeout=45,
                )

        await asyncio.to_thread(_conv_voice)
        final_voice = ogg_path if os.path.exists(ogg_path) and os.path.getsize(ogg_path) > 0 else dl_path
        await c.send_voice(m.chat.id, voice=final_voice, caption=qbox("✅ <b>ᴄᴏɴᴠᴇʀᴛᴇᴅ ᴛᴏ ᴠᴏɪᴄᴇ!</b>"), parse_mode=ParseMode.HTML)
        if status:
            try:
                await status.delete()
            except Exception:
                pass
    except Exception as e:
        if status:
            await status.edit_text(qbox(f"❌ <b>.tovoice ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>"), parse_mode=ParseMode.HTML)
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


async def tomp3_cmd(c, m):
    rep = m.reply_to_message
    if not rep or not (rep.audio or rep.video or rep.voice or rep.document):
        return await reply_quote(m, "❌ <b>ᴀᴜᴅɪᴏ / ᴠᴏɪᴄᴇ / ᴠɪᴅᴇᴏ ᴘᴀʀ ʀᴇᴘʟʏ ᴋᴀʀᴇɪɴ ᴡɪᴛʜ</b> <code>.tomp3</code><b>!</b>")

    status = await reply_quote(m, "🎵 <b>ᴄᴏɴᴠᴇʀᴛɪɴɢ ᴛᴏ MP3...</b>")
    work_dir = tempfile.mkdtemp(prefix="nova_tomp3_")
    try:
        dl_path = await c.download_media(rep, file_name=os.path.join(work_dir, "src_media"))
        mp3_out = os.path.join(work_dir, "converted.mp3")

        def _conv_mp3():
            if shutil.which("ffmpeg"):
                subprocess.run(
                    ["ffmpeg", "-y", "-i", dl_path, "-vn", "-acodec", "libmp3lame", "-ab", "192k", mp3_out],
                    capture_output=True,
                    timeout=45,
                )

        await asyncio.to_thread(_conv_mp3)
        final_mp3 = mp3_out if os.path.exists(mp3_out) and os.path.getsize(mp3_out) > 0 else dl_path
        await c.send_audio(m.chat.id, audio=final_mp3, title="Converted Track", caption=qbox("✅ <b>ᴄᴏɴᴠᴇʀᴛᴇᴅ ᴛᴏ MP3!</b>"), parse_mode=ParseMode.HTML)
        if status:
            try:
                await status.delete()
            except Exception:
                pass
    except Exception as e:
        if status:
            await status.edit_text(qbox(f"❌ <b>.tomp3 ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>"), parse_mode=ParseMode.HTML)
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


async def audioinfo_cmd(c, m):
    rep = m.reply_to_message or m
    aud = rep.audio or rep.voice or rep.document
    if not aud:
        return await reply_quote(m, "❌ <b>ᴀᴜᴅɪᴏ ʏᴀ ᴠᴏɪᴄᴇ ᴍᴇssᴀɢᴇ ᴘᴀʀ ʀᴇᴘʟʏ ᴋᴀʀᴇɪɴ ᴡɪᴛʜ</b> <code>.audioinfo</code><b>!</b>")
    title = getattr(aud, "title", None) or getattr(aud, "file_name", None) or "ᴜɴᴋɴᴏᴡɴ"
    performer = getattr(aud, "performer", None) or "ɴ/ᴀ"
    dur = getattr(aud, "duration", 0) or 0
    mime = getattr(aud, "mime_type", None) or "ɴ/ᴀ"
    fsize = getattr(aud, "file_size", 0) or 0
    await reply_quote(
        m,
        f"🎼 <b>『 ᴀᴜᴅɪᴏ ɪɴғᴏ 』</b> 🎼\n\n"
        f"• <b>ᴛɪᴛʟᴇ:</b> <code>{esc_html(str(title))}</code>\n"
        f"• <b>ᴀʀᴛɪsᴛ:</b> <code>{esc_html(str(performer))}</code>\n"
        f"• <b>ᴅᴜʀᴀᴛɪᴏɴ:</b> <code>{dur}s</code>\n"
        f"• <b>ᴍɪᴍᴇ:</b> <code>{esc_html(str(mime))}</code>\n"
        f"• <b>sɪᴢᴇ:</b> <code>{round(fsize / 1024, 2)} KB</code>",
    )


async def lyrics_cmd(c, m):
    song_q = m.text.split(None, 1)[1].strip() if len(m.command) > 1 else (
        (m.reply_to_message.audio.title if (m.reply_to_message and m.reply_to_message.audio and m.reply_to_message.audio.title) else "")
    )
    if not song_q:
        return await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.lyrics &lt;song name&gt;</code>")

    status = await reply_quote(m, f"🎤 <b>sᴇᴀʀᴄʜɪɴɢ ʟʏʀɪᴄs:</b> <code>{esc_html(song_q)}</code><b>...</b>")
    try:
        def _fetch_lyrics():
            url = f"https://api.lyrics.ovh/v1/{urllib.parse.quote(song_q)}/{urllib.parse.quote(song_q)}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return (data.get("lyrics") or "").strip()

        lyr = await asyncio.to_thread(_fetch_lyrics)
        if not lyr:
            lyr = await _query_ai(f"Provide song lyrics or key verses for: {song_q}", c.me.id, "You are a music lyrics assistant.")
        if status:
            await status.edit_text(
                qbox(f"🎤 <b>ʟʏʀɪᴄs:</b> <code>{esc_html(song_q)}</code>\n\n{esc_html(lyr[:3200])}", expandable=True),
                parse_mode=ParseMode.HTML,
            )
    except Exception as e:
        if status:
            await status.edit_text(qbox(f"❌ <b>ʟʏʀɪᴄs ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>"), parse_mode=ParseMode.HTML)


async def volume_cmd(c, m):
    uid = c.me.id
    curr_v = int(get_ubot_setting(uid, "audio_volume", 100) or 100)
    if len(m.command) < 2:
        return await reply_quote(
            m,
            f"🔊 <b>ᴄᴜʀʀᴇɴᴛ ᴠᴏʟᴜᴍᴇ:</b> <code>{curr_v}%</code>\n"
            f"📌 <b>ᴜsᴀɢᴇ:</b> <code>.volume &lt;0-200&gt;</code>",
        )
    if not m.command[1].isdigit():
        return await reply_quote(m, "❌ <b>ᴠᴏʟᴜᴍᴇ 0 sᴇ 200 ᴋᴇ ʙᴇᴇᴄʜ ɴᴜᴍʙᴇʀ ʜᴏɴᴀ ᴄʜᴀʜɪʏᴇ!</b>")
    v_new = max(0, min(200, int(m.command[1])))
    set_ubot_setting(uid, "audio_volume", v_new)
    await reply_quote(m, f"🔊 <b>ᴠᴏʟᴜᴍᴇ sᴇᴛ ᴛᴏ</b> <code>{v_new}%</code><b>!</b>")


# --- TRANSLATE, QUOTE, OCR, TOURL, TOSTICKER, REMIND, NOTES, TODO, STATS ---
async def translate_cmd(c, m):
    args = m.text.split(None, 2)
    target_lang = "hi"
    text_to_tr = ""

    if m.reply_to_message and (m.reply_to_message.text or m.reply_to_message.caption):
        text_to_tr = m.reply_to_message.text or m.reply_to_message.caption
        if len(args) > 1 and 2 <= len(args[1]) <= 5 and args[1].isalpha():
            target_lang = args[1].lower()
    else:
        if len(args) < 2:
            return await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.translate [lang] &lt;text&gt;</code> ʏᴀ ᴍᴇssᴀɢᴇ ᴘᴀʀ ʀᴇᴘʟʏ ᴋᴀʀᴇɪɴ.")
        if len(args) >= 3 and 2 <= len(args[1]) <= 5 and args[1].isalpha():
            target_lang = args[1].lower()
            text_to_tr = args[2]
        else:
            text_to_tr = m.text.split(None, 1)[1]

    def _tr_google():
        q = urllib.parse.quote(text_to_tr)
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={urllib.parse.quote(target_lang)}&dt=t&q={q}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        translated_parts = [item[0] for item in data[0] if item and item[0]]
        detected_lang = data[2] if len(data) > 2 and data[2] else "auto"
        return "".join(translated_parts), detected_lang

    try:
        translated, src_lang = await asyncio.to_thread(_tr_google)
        await reply_quote(
            m,
            f"🌐 <b>ᴛʀᴀɴsʟᴀᴛɪᴏɴ</b> (<code>{esc_html(src_lang)}</code> ➔ <code>{esc_html(target_lang)}</code>)\n\n"
            f"📥 <b>ᴏʀɪɢɪɴᴀʟ:</b> <code>{esc_html(text_to_tr[:600])}</code>\n"
            f"📤 <b>ᴛʀᴀɴsʟᴀᴛᴇᴅ:</b> <code>{esc_html(translated)}</code>",
            expandable=True,
        )
    except Exception as e:
        await reply_quote(m, f"❌ <b>ᴛʀᴀɴsʟᴀᴛɪᴏɴ ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>")


async def quote_cmd(c, m):
    if not m.reply_to_message:
        return await reply_quote(m, "❌ <b>ᴋɪsɪ ᴍᴇssᴀɢᴇ ᴘᴀʀ ʀᴇᴘʟʏ ᴋᴀʀᴇɪɴ ᴡɪᴛʜ</b> <code>.quote</code><b>!</b>")
    rep = m.reply_to_message
    content = rep.text or rep.caption or (f"[{rep.media.value}]" if rep.media else "ᴍᴇssᴀɢᴇ")
    sender_name = rep.from_user.first_name if rep.from_user else (rep.sender_chat.title if rep.sender_chat else "ᴜsᴇʀ")
    sender_id = rep.from_user.id if rep.from_user else (rep.sender_chat.id if rep.sender_chat else 0)
    mention_str = html_mention(sender_id, sender_name) if sender_id > 0 else esc_html(sender_name)
    await reply_quote(
        m,
        f"💬 <b>『 ǫᴜᴏᴛᴇ 』</b>\n\n"
        f"“{esc_html(content)}”\n\n"
        f"— {mention_str}",
        expandable=True,
    )


async def ocr_cmd(c, m):
    target_msg = m.reply_to_message if (m.reply_to_message and m.reply_to_message.photo) else (m if m.photo else None)
    if not target_msg:
        return await reply_quote(m, "❌ <b>ᴋɪsɪ ᴘʜᴏᴛᴏ ᴘᴀʀ ʀᴇᴘʟʏ ᴋᴀʀᴇɪɴ ᴡɪᴛʜ</b> <code>.ocr</code><b>!</b>")

    status = await reply_quote(m, "🔍 <b>ᴇxᴛʀᴀᴄᴛɪɴɢ ᴛᴇxᴛ (OCR)...</b>")
    file_path = None
    try:
        file_path = await c.download_media(target_msg.photo.file_id)

        def _run_ocr():
            boundary = f"----PyroOCR{random.randint(100000, 999999)}"
            with open(file_path, "rb") as f:
                img_bytes = f.read()
            filename = os.path.basename(file_path) or "image.jpg"
            body = (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="apikey"\r\n\r\nhelloworld\r\n'
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="language"\r\n\r\neng\r\n'
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
                f"Content-Type: image/jpeg\r\n\r\n"
            ).encode("utf-8") + img_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

            req = urllib.request.Request(
                "https://api.ocr.space/parse/image",
                data=body,
                headers={
                    "Content-Type": f"multipart/form-data; boundary={boundary}",
                    "User-Agent": "Mozilla/5.0",
                },
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read().decode("utf-8"))

        res = await asyncio.to_thread(_run_ocr)
        parsed = res.get("ParsedResults") or []
        extracted = (parsed[0].get("ParsedText") if parsed else "").strip()
        if not extracted:
            msg_out = "⚠️ <b>ᴘʜᴏᴛᴏ ᴍᴇɪɴ ᴋᴏɪ ᴛᴇxᴛ ɴᴀʜɪ ᴍɪʟᴀ.</b>"
        else:
            msg_out = f"📝 <b>ᴏᴄʀ ʀᴇsᴜʟᴛ:</b>\n\n<code>{esc_html(extracted[:2800])}</code>"

        if status:
            await status.edit_text(qbox(msg_out), parse_mode=ParseMode.HTML)
    except Exception as e:
        if status:
            await status.edit_text(qbox(f"❌ <b>ᴏᴄʀ ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>"), parse_mode=ParseMode.HTML)
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass


async def tourl_cmd(c, m):
    rep = m.reply_to_message if m.reply_to_message else m
    if not (rep and (rep.photo or rep.video or rep.animation or rep.document or rep.audio)):
        return await reply_quote(m, "❌ <b>ᴋɪsɪ ᴘʜᴏᴛᴏ / ᴠɪᴅᴇᴏ / ғɪʟᴇ ᴘᴀʀ ʀᴇᴘʟʏ ᴋᴀʀᴇɪɴ ᴡɪᴛʜ</b> <code>.tourl</code><b>!</b>")

    status = await reply_quote(m, "☁️ <b>ᴜᴘʟᴏᴀᴅɪɴɢ ᴛᴏ ᴄᴀᴛʙᴏx...</b>")
    file_path = None
    try:
        file_path = await c.download_media(rep)

        def _upload_catbox():
            boundary = f"----Catbox{random.randint(100000, 999999)}"
            with open(file_path, "rb") as f:
                data_bytes = f.read()
            fname = os.path.basename(file_path) or "file.bin"
            body = (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="reqtype"\r\n\r\nfileupload\r\n'
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="fileToUpload"; filename="{fname}"\r\n'
                f"Content-Type: application/octet-stream\r\n\r\n"
            ).encode("utf-8") + data_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

            req = urllib.request.Request(
                "https://catbox.moe/user/api.php",
                data=body,
                headers={
                    "Content-Type": f"multipart/form-data; boundary={boundary}",
                    "User-Agent": "Mozilla/5.0",
                },
            )
            with urllib.request.urlopen(req, timeout=25) as resp:
                return resp.read().decode("utf-8").strip()

        url_out = await asyncio.to_thread(_upload_catbox)
        if not url_out.startswith("http"):
            raise RuntimeError(url_out or "Upload failed")

        if status:
            await status.edit_text(
                qbox(f"🔗 <b>ᴜᴘʟᴏᴀᴅᴇᴅ sᴜᴄᴄᴇsғᴜʟʟʏ!</b>\n\n🌐 <b>ᴜʀʟ:</b> <code>{esc_html(url_out)}</code>"),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
    except Exception as e:
        if status:
            await status.edit_text(qbox(f"❌ <b>ᴛᴏᴜʀʟ ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>"), parse_mode=ParseMode.HTML)
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass


async def tosticker_cmd(c, m):
    if not HAS_PIL:
        return await reply_quote(m, _require_pil_msg())
    target_msg = m.reply_to_message if (m.reply_to_message and m.reply_to_message.photo) else (m if m.photo else None)
    if not target_msg:
        return await reply_quote(m, "❌ <b>ᴋɪsɪ ᴘʜᴏᴛᴏ ᴘᴀʀ ʀᴇᴘʟʏ ᴋᴀʀᴇɪɴ ᴡɪᴛʜ</b> <code>.tosticker</code><b>!</b>")

    status = await reply_quote(m, "🎨 <b>ᴄᴏɴᴠᴇʀᴛɪɴɢ ᴛᴏ sᴛɪᴄᴋᴇʀ...</b>")
    raw_path = None
    sticker_path = None
    try:
        raw_path = await c.download_media(target_msg.photo.file_id)
        sticker_path = f"{raw_path}_sticker.webp"

        def _make_webp():
            with Image.open(raw_path) as im:
                im = im.convert("RGBA")
                im.thumbnail((512, 512))
                canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
                offset_x = (512 - im.width) // 2
                offset_y = (512 - im.height) // 2
                canvas.paste(im, (offset_x, offset_y))
                canvas.save(sticker_path, "WEBP", quality=90)

        await asyncio.to_thread(_make_webp)
        await c.send_sticker(m.chat.id, sticker=sticker_path)
        if status:
            try:
                await status.delete()
            except Exception:
                pass
    except Exception as e:
        if status:
            await status.edit_text(qbox(f"❌ <b>ᴛᴏsᴛɪᴄᴋᴇʀ ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>"), parse_mode=ParseMode.HTML)
    finally:
        for p in (raw_path, sticker_path):
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass


def _parse_duration_seconds(raw_dur: str):
    match = re.fullmatch(r"(\d+)\s*([smhdSMHD]?)", raw_dur.strip())
    if not match:
        return None
    val = int(match.group(1))
    unit = (match.group(2) or "s").lower()
    if val <= 0:
        return None
    mult = {"s": 1, "m": 60, "h": 3600, "d": 86400}.get(unit, 1)
    return val * mult


async def remind_cmd(c, m):
    if len(m.command) < 3:
        return await reply_quote(
            m,
            "❌ <b>ᴜsᴀɢᴇ:</b> <code>.remind &lt;time&gt; &lt;message&gt;</code>\n"
            "⏱️ <b>ᴇxᴀᴍᴘʟᴇ:</b> <code>.remind 10m Chai peeni hai</code> ʏᴀ <code>.remind 30s Test</code>",
        )
    sec = _parse_duration_seconds(m.command[1])
    if not sec or sec > 86400 * 7:
        return await reply_quote(m, "❌ <b>ɪɴᴠᴀʟɪᴅ ᴛɪᴍᴇ! ᴜsᴇ</b> <code>10s</code>, <code>5m</code>, <code>2h</code>, <code>1d</code><b>.</b>")
    rem_msg = m.text.split(None, 2)[2].strip()
    chat_id = m.chat.id
    await reply_quote(m, f"⏰ <b>ʀᴇᴍɪɴᴅᴇʀ sᴇᴛ!</b>\n⏳ <b>ɪɴ:</b> <code>{esc_html(m.command[1])}</code>\n📝 <b>ɴᴏᴛᴇ:</b> <code>{esc_html(rem_msg)}</code>")

    async def _trigger_reminder():
        await asyncio.sleep(sec)
        try:
            await c.send_message(
                chat_id,
                qbox(f"🔔 <b>ʀᴇᴍɪɴᴅᴇʀ!</b>\n\n📝 <code>{esc_html(rem_msg)}</code>"),
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass

    asyncio.create_task(_trigger_reminder())


async def notes_cmd(c, m):
    uid = int(c.me.id)
    if len(m.command) < 2:
        docs = list(notes_col.find({"ubot_id": uid}))
        if not docs:
            return await reply_quote(
                m,
                "📭 <b>ᴋᴏɪ ɴᴏᴛᴇs sᴀᴠᴇ ɴᴀʜɪ ʜᴀɪɴ.</b>\n"
                "📌 <b>ᴜsᴀɢᴇ:</b> <code>.notes add &lt;name&gt; &lt;text&gt;</code> | <code>.notes del &lt;name&gt;</code> | <code>.notes clear</code>",
            )
        lines = [f"📒 <b>ʏᴏᴜʀ ɴᴏᴛᴇs ({len(docs)}):</b>\n"]
        for d in docs[:30]:
            n_key = d.get("name", "")
            n_val = esc_html((d.get("content", "") or "")[:60])
            lines.append(f"• <code>{esc_html(n_key)}</code>: {n_val}")
        return await reply_quote(m, "\n".join(lines), expandable=True)

    sub = m.command[1].lower()
    if sub == "add":
        parts = m.text.split(None, 3)
        if len(parts) < 3:
            return await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.notes add &lt;name&gt; &lt;text&gt;</code> (ʏᴀ ʀᴇᴘʟʏ)")
        n_name = parts[2].strip().lower()
        n_text = parts[3].strip() if len(parts) >= 4 else (m.reply_to_message.text or m.reply_to_message.caption or "").strip()
        if not n_text:
            return await reply_quote(m, "❌ <b>ɴᴏᴛᴇ ᴋᴀ ᴛᴇxᴛ ᴅᴇɪɴ ʏᴀ ᴍᴇssᴀɢᴇ ᴘᴀʀ ʀᴇᴘʟʏ ᴋᴀʀᴇɪɴ.</b>")
        notes_col.update_one(
            {"ubot_id": uid, "name": n_name},
            {"$set": {"ubot_id": uid, "name": n_name, "content": n_text, "updated_at": time.time()}},
            upsert=True,
        )
        return await reply_quote(m, f"✅ <b>ɴᴏᴛᴇ sᴀᴠᴇᴅ:</b> <code>{esc_html(n_name)}</code>")

    if sub in ("del", "rm", "remove"):
        if len(m.command) < 3:
            return await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.notes del &lt;name&gt;</code>")
        n_name = m.command[2].strip().lower()
        res = notes_col.delete_one({"ubot_id": uid, "name": n_name})
        return await reply_quote(
            m,
            f"🗑️ <b>ɴᴏᴛᴇ ᴅᴇʟᴇᴛᴇᴅ:</b> <code>{esc_html(n_name)}</code>" if res.deleted_count else "⚠️ <b>ɴᴏᴛᴇ ɴʜɪ ᴍɪʟᴀ.</b>",
        )

    if sub == "clear":
        notes_col.delete_many({"ubot_id": uid})
        return await reply_quote(m, "🧹 <b>sᴀʙ ɴᴏᴛᴇs ᴄʟᴇᴀʀ ᴋᴀʀ ᴅɪʏᴇ ɢᴀʏᴇ!</b>")

    n_name = m.command[1].strip().lower()
    doc = notes_col.find_one({"ubot_id": uid, "name": n_name})
    if not doc:
        return await reply_quote(m, f"⚠️ <b>ɴᴏᴛᴇ</b> <code>{esc_html(n_name)}</code> <b>ɴʜɪ ᴍɪʟᴀ.</b>")
    await reply_quote(m, f"📒 <b>ɴᴏᴛᴇ:</b> <code>{esc_html(n_name)}</code>\n\n{esc_html(doc.get('content', '') or '')}", expandable=True)


async def todo_cmd(c, m):
    uid = int(c.me.id)
    if len(m.command) < 2:
        items = list(todos_col.find({"ubot_id": uid}).sort("created_at", 1))
        if not items:
            return await reply_quote(
                m,
                "📭 <b>ᴛᴏ-ᴅᴏ ʟɪsᴛ ᴋʜᴀʟɪ ʜᴀɪ.</b>\n"
                "📌 <b>ᴜsᴀɢᴇ:</b> <code>.todo add &lt;task&gt;</code> | <code>.todo done &lt;#&gt;</code> | <code>.todo del &lt;#&gt;</code> | <code>.todo clear</code>",
            )
        lines = [f"☑️ <b>ʏᴏᴜʀ ᴛᴏ-ᴅᴏ ʟɪsᴛ ({len(items)}):</b>\n"]
        for idx, it in enumerate(items, start=1):
            mark = "✅" if it.get("done") else "⬜"
            lines.append(f"<code>{idx}.</code> {mark} {esc_html(it.get('task', '') or '')}")
        return await reply_quote(m, "\n".join(lines), expandable=True)

    sub = m.command[1].lower()
    if sub == "add":
        if len(m.command) < 3:
            return await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.todo add &lt;task&gt;</code>")
        task_txt = m.text.split(None, 2)[2].strip()
        todos_col.insert_one({"ubot_id": uid, "task": task_txt, "done": False, "created_at": time.time()})
        return await reply_quote(m, f"➕ <b>ᴛᴀsᴋ ᴀᴅᴅᴇᴅ:</b> <code>{esc_html(task_txt)}</code>")

    items = list(todos_col.find({"ubot_id": uid}).sort("created_at", 1))
    if sub == "done":
        if len(m.command) < 3 or not m.command[2].isdigit():
            return await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.todo done &lt;task_number&gt;</code>")
        idx = int(m.command[2]) - 1
        if idx < 0 or idx >= len(items):
            return await reply_quote(m, "❌ <b>ɪɴᴠᴀʟɪᴅ ᴛᴀsᴋ ɴᴜᴍʙᴇʀ!</b>")
        target_doc = items[idx]
        new_done = not bool(target_doc.get("done"))
        todos_col.update_one({"_id": target_doc["_id"]}, {"$set": {"done": new_done}})
        return await reply_quote(m, f"{'✅' if new_done else '⬜'} <b>ᴛᴀsᴋ #{idx + 1} ᴜᴘᴅᴀᴛᴇᴅ!</b>")

    if sub in ("del", "rm", "remove"):
        if len(m.command) < 3 or not m.command[2].isdigit():
            return await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.todo del &lt;task_number&gt;</code>")
        idx = int(m.command[2]) - 1
        if idx < 0 or idx >= len(items):
            return await reply_quote(m, "❌ <b>ɪɴᴠᴀʟɪᴅ ᴛᴀsᴋ ɴᴜᴍʙᴇʀ!</b>")
        todos_col.delete_one({"_id": items[idx]["_id"]})
        return await reply_quote(m, f"🗑️ <b>ᴛᴀsᴋ #{idx + 1} ᴅᴇʟᴇᴛᴇᴅ!</b>")

    if sub == "clear":
        todos_col.delete_many({"ubot_id": uid})
        return await reply_quote(m, "🧹 <b>sᴀʙ ᴛᴏ-ᴅᴏ ᴛᴀsᴋs ᴄʟᴇᴀʀ ᴋᴀʀ ᴅɪʏᴇ ɢᴀʏᴇ!</b>")

    await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.todo add/done/del/clear</code>")


async def stats_cmd(c, m):
    uid = int(c.me.id)
    total_saved_acc = sessions_col.count_documents({})
    active_ubots = len(running_ubots)
    total_bot_users = len(get_all_bot_user_ids())
    my_notes = notes_col.count_documents({"ubot_id": uid})
    my_todos = todos_col.count_documents({"ubot_id": uid})
    up = get_readable_time(int(time.time() - BOT_START_TIME))
    await reply_quote(
        m,
        f"📊 <b>『 ᴄᴏᴅᴇʀɴᴏᴠᴀ sᴛᴀᴛs 』</b> 📊\n\n"
        f"🤖 <b>ᴀᴄᴛɪᴠᴇ ᴜsᴇʀʙᴏᴛs:</b> <code>{active_ubots}</code> / <code>{total_saved_acc}</code>\n"
        f"👥 <b>ʙᴏᴛ ᴜsᴇʀs:</b> <code>{total_bot_users}</code>\n"
        f"📒 <b>ʏᴏᴜʀ ɴᴏᴛᴇs:</b> <code>{my_notes}</code>\n"
        f"☑️ <b>ʏᴏᴜʀ ᴛᴏ-ᴅᴏs:</b> <code>{my_todos}</code>\n"
        f"⏳ <b>ᴜᴘᴛɪᴍᴇ:</b> <code>{up}</code>\n"
        f"🏷️ <b>ᴠᴇʀsɪᴏɴ:</b> <code>{USERBOT_VERSION}</code>",
    )


async def uptime_cmd(c, m):
    up = get_readable_time(int(time.time() - BOT_START_TIME))
    await reply_quote(
        m,
        f"⏳ <b>ᴜᴘᴛɪᴍᴇ:</b> <code>{up}</code>\n"
        f"🕒 <b>ɪsᴛ ɴᴏᴡ:</b> <code>{get_current_ist_time()}</code>",
    )


async def version_cmd(c, m):
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    await reply_quote(
        m,
        f"🏷️ <b>『 ᴠᴇʀsɪᴏɴ ɪɴғᴏ 』</b> 🏷️\n\n"
        f"✦ <b>ᴜsᴇʀʙᴏᴛ:</b> <code>{USERBOT_VERSION}</code>\n"
        f"✦ <b>ᴘʏᴛʜᴏɴ:</b> <code>{py_ver}</code>\n"
        f"✦ <b>ᴘʀᴇғɪx:</b> <code>{esc_html(get_ubot_prefix(c.me.id))}</code>\n"
        f"✦ <b>ᴏᴡɴᴇʀ:</b> {OWNER_USERNAME}",
    )


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
            await reply_quote(m, f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>")


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
        await reply_quote(m, f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>")


# --- ACCOUNT & PROFILE COMMANDS ---
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
        f"👤 <b>ɴᴀᴍᴇ:</b> {esc_html(full_n)}\n"
        f"🆔 <b>ᴜsᴇʀ ɪᴅ:</b> <code>{me.id}</code>\n"
        f"🔗 <b>ᴜsᴇʀɴᴀᴍᴇ:</b> {esc_html(uname)}\n"
        f"📞 <b>ᴘʜᴏɴᴇ:</b> <code>{phone}</code>\n"
        f"🌐 <b>ᴅᴄ ɪᴅ:</b> <code>{dc_id}</code>\n"
        f"📝 <b>ʙɪᴏ:</b> <code>{esc_html(chat_me.bio or 'ɴᴏɴᴇ')}</code>",
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
        await reply_quote(m, f"✅ <b>ɴᴀᴍᴇ ᴜᴘᴅᴀᴛᴇᴅ:</b> <code>{esc_html((first_name + ' ' + last_name).strip())}</code>")
    except Exception as e:
        await reply_quote(m, f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>")


async def setbio_cmd(c, m):
    bio_text = m.text.split(None, 1)[1].strip() if len(m.command) > 1 else (m.reply_to_message.text or "").strip()
    if not bio_text:
        return await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.setbio &lt;your bio&gt;</code>")
    try:
        await c.update_profile(bio=bio_text[:70])
        await reply_quote(m, f"✅ <b>ʙɪᴏ ᴜᴘᴅᴀᴛᴇᴅ:</b> <code>{esc_html(bio_text[:70])}</code>")
    except Exception as e:
        await reply_quote(m, f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>")


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
            await status.edit_text(qbox(f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>"), parse_mode=ParseMode.HTML)
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
        await reply_quote(m, f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>")


async def username_cmd(c, m):
    if len(m.command) < 2:
        return await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.username &lt;new_username&gt;</code> ʏᴀ <code>none</code>")
    new_u = m.command[1].strip().lstrip("@")
    try:
        await c.set_username("" if new_u.lower() == "none" else new_u)
        await reply_quote(
            m,
            f"✅ <b>ᴜsᴇʀɴᴀᴍᴇ ᴜᴘᴅᴀᴛᴇᴅ:</b> <code>@{esc_html(new_u)}</code>"
            if new_u.lower() != "none"
            else "✅ <b>ᴜsᴇʀɴᴀᴍᴇ ʀᴇᴍᴏᴠᴇᴅ!</b>",
        )
    except Exception as e:
        await reply_quote(m, f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>")


# --- SECURITY & PRIVACY COMMANDS ---
async def block_cmd(c, m):
    target = await resolve_target_user(c, m, allow_self_in_pm=True)
    if not target:
        return await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.block @username</code> / <code>user_id</code> / <code>reply</code> ʏᴀ ᴅᴍ ᴍᴇ.")
    try:
        await c.block_user(target.id)
        await reply_quote(m, f"⛔ <b>ʙʟᴏᴄᴋᴇᴅ:</b> {html_mention(target.id, target.first_name or 'ᴜsᴇʀ')} (<code>{target.id}</code>)")
    except Exception as e:
        await reply_quote(m, f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>")


async def unblock_cmd(c, m):
    target = await resolve_target_user(c, m, allow_self_in_pm=True)
    if not target:
        return await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.unblock @username</code> / <code>user_id</code> / <code>reply</code>")
    try:
        await c.unblock_user(target.id)
        await reply_quote(m, f"✅ <b>ᴜɴʙʟᴏᴄᴋᴇᴅ:</b> {html_mention(target.id, target.first_name or 'ᴜsᴇʀ')} (<code>{target.id}</code>)")
    except Exception as e:
        await reply_quote(m, f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>")


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
            lines.append(f"<code>{i}.</code> {html_mention(uid_val, fname)} ({esc_html(uname)}) — <code>{uid_val}</code>")
        await reply_quote(m, "\n".join(lines), expandable=True)
    except Exception as e:
        await reply_quote(m, f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>")


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
            await status.edit_text(qbox(f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>"), parse_mode=ParseMode.HTML)


async def sessions_cmd(c, m):
    try:
        auths = await c.invoke(raw_functions.account.GetAuthorizations())
        items = getattr(auths, "authorizations", []) or []
        lines = [f"🔐 <b>ᴀᴄᴛɪᴠᴇ sᴇssɪᴏɴs ({len(items)}):</b>\n"]
        for idx, a in enumerate(items[:15], start=1):
            curr = "🟢 ᴄᴜʀʀᴇɴᴛ" if getattr(a, "current", False) else "🔹 sᴇssɪᴏɴ"
            dev = esc_html(getattr(a, "device_model", "Unknown"))
            plat = esc_html(getattr(a, "platform", ""))
            ip = esc_html(getattr(a, "ip", ""))
            country = esc_html(getattr(a, "country", ""))
            lines.append(f"<code>{idx}.</code> {curr} — <b>{dev}</b> ({plat}) | <code>{ip}</code> {country}")
        await reply_quote(m, "\n".join(lines), expandable=True)
    except Exception as e:
        await reply_quote(m, f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>")


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


# --- CHAT MANAGEMENT COMMANDS ---
async def save_cmd(c, m):
    if not m.reply_to_message:
        return await reply_quote(m, "❌ <b>ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ sᴀᴠᴇ ɪɴ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs!</b>")
    try:
        await m.reply_to_message.copy("me")
        await reply_quote(m, "💾 <b>sᴀᴠᴇᴅ ᴛᴏ ʏᴏᴜʀ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs!</b>")
    except Exception as e:
        await reply_quote(m, f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>")


async def del_cmd(c, m):
    if not m.reply_to_message:
        return await reply_quote(m, "❌ <b>ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ᴅᴇʟᴇᴛᴇ!</b>")
    try:
        await m.reply_to_message.delete()
        await m.delete()
    except Exception as e:
        await reply_quote(m, f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>")


async def edit_cmd(c, m):
    if not m.reply_to_message or len(m.command) < 2:
        return await reply_quote(m, "❌ <b>ʀᴇᴘʟʏ ᴛᴏ ʏᴏᴜʀ ᴍᴇssᴀɢᴇ ᴡɪᴛʜ</b> <code>.edit &lt;new text&gt;</code><b>!</b>")
    new_text = m.text.split(None, 1)[1]
    try:
        await m.reply_to_message.edit_text(new_text)
        await m.delete()
    except Exception as e:
        await reply_quote(m, f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>")


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
        await reply_quote(m, f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>")


async def unpin_cmd(c, m):
    try:
        if m.reply_to_message:
            await c.unpin_chat_message(m.chat.id, m.reply_to_message.id)
        else:
            await c.unpin_all_chat_messages(m.chat.id)
        await reply_quote(m, "📍 <b>ᴍᴇssᴀɢᴇ ᴜɴᴘɪɴɴᴇᴅ!</b>")
    except Exception as e:
        await reply_quote(m, f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>")


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
        await reply_quote(m, f"❌ <b>ᴘᴜʀɢᴇ ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>")


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
            msgs.append(f"• <b>{esc_html(sender)}:</b> <code>{esc_html(snippet)}</code>")
            if len(msgs) >= limit:
                break
        text = f"🕘 <b>ᴄʜᴀᴛ ʜɪsᴛᴏʀʏ (ʟᴀsᴛ {len(msgs)})</b>\n\n" + ("\n".join(msgs) if msgs else "ɴᴏ ᴍᴇssᴀɢᴇs.")
        await reply_quote(m, text, expandable=True)
    except Exception as e:
        await reply_quote(m, f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>")


# --- FUN & UTILITIES COMMANDS ---
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
    await reply_quote(m, f"💤 <b>ᴀғᴋ ᴍᴏᴅᴇ ᴏɴ!</b>\n📝 <b>ʀᴇᴀsᴏɴ:</b> <code>{esc_html(reason)}</code>")


async def calc_cmd(c, m):
    expr = m.text.split(None, 1)[1] if len(m.command) > 1 else (m.reply_to_message.text or "")
    if not expr.strip():
        return await reply_quote(m, "❌ <b>ᴜsᴀɢᴇ:</b> <code>.calc 25 * 4 + 10</code>")
    try:
        result = safe_math_eval(expr)
        await reply_quote(
            m,
            f"🧮 <b>ᴄᴀʟᴄᴜʟᴀᴛᴏʀ</b>\n\n📥 <b>ɪɴᴘᴜᴛ:</b> <code>{esc_html(expr.strip())}</code>\n📤 <b>ʀᴇsᴜʟᴛ:</b> <code>{result}</code>",
        )
    except Exception:
        await reply_quote(m, "❌ <b>ɪɴᴠᴀʟɪᴅ ᴍᴀᴛʜ ᴇxᴘʀᴇssɪᴏɴ!</b>")


async def time_cmd(c, m):
    tz_input = m.text.split(None, 1)[1].strip() if len(m.command) > 1 else "Asia/Kolkata"
    try:
        now = datetime.now(ZoneInfo(tz_input))
        await reply_quote(
            m,
            f"🕒 <b>ᴛɪᴍᴇ ᴢᴏɴᴇ:</b> <code>{esc_html(tz_input)}</code>\n"
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
            f"🌤️ <b>ᴡᴇᴀᴛʜᴇʀ ɪɴ {esc_html(city.upper())}</b>\n\n"
            f"🌡️ <b>ᴛᴇᴍᴘ:</b> <code>{temp_c}°C</code> (ғᴇᴇʟs <code>{feels_c}°C</code>)\n"
            f"☁️ <b>ᴄᴏɴᴅɪᴛɪᴏɴ:</b> <code>{esc_html(desc)}</code>\n"
            f"💧 <b>ʜᴜᴍɪᴅɪᴛʏ:</b> <code>{humidity}%</code>",
        )
    except Exception as e:
        await reply_quote(m, f"❌ <b>ᴡᴇᴀᴛʜᴇʀ ғᴇᴛᴄʜ ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>")


async def id_cmd(c, m):
    target = await resolve_target_user(c, m, allow_self_in_pm=False)
    lines = [f"🆔 <b>ᴄʜᴀᴛ ɪᴅ:</b> <code>{m.chat.id}</code>"]
    if m.chat.type != ChatType.PRIVATE:
        lines.append(f"💬 <b>ᴄʜᴀᴛ ᴛʏᴘᴇ:</b> <code>{m.chat.type.name}</code>")
    if target:
        lines.append(f"👤 <b>ᴛᴀʀɢᴇᴛ ᴜsᴇʀ ɪᴅ:</b> <code>{target.id}</code> ({esc_html(target.first_name or 'ᴜsᴇʀ')})")
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
    await reply_quote(m, f"🧾 <b>ᴍᴇssᴀɢᴇ ᴊsᴏɴ / ᴅᴀᴛᴀ</b>\n\n<pre>{esc_html(raw_str)}</pre>", expandable=True)


# --- ADVANCED FEATURES COMMANDS ---
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
            f"💬 <b>ᴍᴇssᴀɢᴇ:</b> <code>{esc_html(curr_msg)}</code>\n\n"
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
        await reply_quote(m, f"✅ <b>ᴀᴜᴛᴏ-ʀᴇᴘʟʏ ᴏɴ &amp; ᴛᴇxᴛ sᴇᴛ:</b> <code>{esc_html(arg)}</code>")


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
                        await c.send_message(dialog.chat.id, qbox(esc_html(text_to_send)), parse_mode=ParseMode.HTML)
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
            await status.edit_text(qbox(f"❌ <b>ɢᴄᴀsᴛ ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>"), parse_mode=ParseMode.HTML)


async def backup_cmd(c, m):
    status = await reply_quote(m, "💼 <b>ʙᴀᴄᴋᴜᴘ ᴄʀᴇᴀᴛɪɴɢ...</b>")
    try:
        session_str = await c.export_session_string()
        me = await c.get_me()
        backup_payload = qbox(
            f"💼 <b>ᴄᴏᴅᴇʀɴᴏᴠᴀ ᴜsᴇʀʙᴏᴛ ʙᴀᴄᴋᴜᴘ</b>\n\n"
            f"👤 <b>ᴀᴄᴄᴏᴜɴᴛ:</b> {esc_html(me.first_name or '')} (@{esc_html(me.username or 'none')}) — <code>{me.id}</code>\n"
            f"🕒 <b>ᴛɪᴍᴇ:</b> <code>{get_current_ist_time()}</code>\n"
            f"🔑 <b>sᴇssɪᴏɴ sᴛʀɪɴɢ:</b>\n<code>{session_str}</code>"
        )
        await c.send_message("me", backup_payload, parse_mode=ParseMode.HTML)
        if status:
            await status.edit_text(qbox("✅ <b>ʙᴀᴄᴋᴜᴘ sᴀᴠᴇᴅ ᴛᴏ ʏᴏᴜʀ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs!</b>"), parse_mode=ParseMode.HTML)
    except Exception as e:
        if status:
            await status.edit_text(qbox(f"❌ <b>ʙᴀᴄᴋᴜᴘ ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>"), parse_mode=ParseMode.HTML)


async def _stop_client_safely(client_obj):
    if not client_obj:
        return
    try:
        if getattr(client_obj, "is_connected", False):
            await asyncio.wait_for(client_obj.stop(), timeout=8)
    except Exception:
        try:
            await asyncio.wait_for(client_obj.disconnect(), timeout=5)
        except Exception:
            pass


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
        custom_p = get_ubot_prefix(uid)
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
        register_ubot_handlers(new_ubot, custom_prefix=custom_p)
        await asyncio.wait_for(new_ubot.start(), timeout=20)
        await warmup_client_peers(new_ubot)
        running_ubots[uid] = new_ubot
        old_ref = c
        if old_ref is not new_ubot:
            asyncio.create_task(_stop_client_safely(old_ref))
    except Exception:
        pass


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
        f"👤 <b>ɴᴀᴍᴇ:</b> {esc_html(target.first_name or 'ɴᴏɴᴇ')} {esc_html(target.last_name or '')}\n"
        f"🆔 <b>ᴜsᴇʀ ɪᴅ:</b> <code>{target.id}</code>\n"
        f"🔗 <b>ᴜsᴇʀɴᴀᴍᴇ:</b> {esc_html(uname)}\n"
        f"🌐 <b>ᴅᴄ ɪᴅ:</b> <code>{dc_id}</code>\n"
        f"⭐ <b>ᴘʀᴇᴍɪᴜᴍ:</b> <code>{is_prem}</code>\n"
        f"📝 <b>ʙɪᴏ:</b> <code>{esc_html(bio)}</code>",
    )


async def alive_cmd(c, m):
    uptime = get_readable_time(int(time.time() - BOT_START_TIME))
    rank_val = get_ubot_setting(c.me.id, "user_rank", "VIP")
    alive_html = qbox(
        f"✨ <b>『 ᴄᴏᴅᴇʀɴᴏᴠᴀ ᴜsᴇʀʙᴏᴛ ɪs ᴀʟɪᴠᴇ 』</b> ✨\n\n"
        f"⏳ <b>ᴜᴘᴛɪᴍᴇ:</b> <code>{uptime}</code>\n"
        f"🏅 <b>ʀᴀɴᴋ:</b> <code>{esc_html(str(rank_val))}</code>\n"
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
    "🛡️ <b>ᴘʀɪᴠᴀᴄʏ &amp; sᴇᴄᴜʀɪᴛʏ:</b>\n"
    "<code>.ghostmode</code> · <code>.dmlock</code> · <code>.dmunlock</code> · <code>.allowlist</code> · <code>.denylist</code> · <code>.privacycheck</code> · <code>.antispam</code> · <code>.antitag</code> · <code>.keywordblock</code> · <code>.securitycheck</code> · <code>.privacyreport</code> · <code>.block</code> · <code>.unblock</code> · <code>.blocked</code> · <code>.clearblocked</code> · <code>.sessions</code> · <code>.privacy</code> · <code>.dmprivacyon</code> · <code>.dmprivacyoff</code> · <code>.dmapprove</code> · <code>.dmunapprove</code>\n\n"
    "💎 <b>ᴘʀᴇᴍɪᴜᴍ &amp; ᴇᴍᴏᴊɪ:</b>\n"
    "<code>.setemoji</code> · <code>.rmemoji</code> · <code>.emojiid</code> · <code>.premiumlist</code> · <code>.premiuminfo</code> · <code>.setrank</code> · <code>.setprefix</code> · <code>.premiumon</code> · <code>.premiumoff</code>\n\n"
    "🤖 <b>ᴀᴜᴛᴏᴍᴀᴛɪᴏɴ:</b>\n"
    "<code>.autoreply</code> · <code>.autoreact</code> · <code>.autosave</code> · <code>.autoforward</code> · <code>.autodelete</code> · <code>.autorespond</code> · <code>.autotyping</code> · <code>.automute</code> · <code>.autounmute</code> · <code>.autoseen</code> · <code>.nightmode</code>\n\n"
    "📂 <b>ғɪʟᴇ &amp; ᴍᴇᴅɪᴀ:</b>\n"
    "<code>.tourl</code> · <code>.toimg</code> · <code>.tosticker</code> · <code>.compress</code> · <code>.rename</code> · <code>.mediainfo</code> · <code>.extracttext</code> · <code>.ocr</code> · <code>.qr</code>\n\n"
    "🧠 <b>ᴀɪ ɪɴᴛᴇʟʟɪɢᴇɴᴄᴇ:</b>\n"
    "<code>.ai</code> · <code>.ask</code> · <code>.summarize</code> · <code>.translate</code> · <code>.rewrite</code> · <code>.grammar</code> · <code>.aiclear</code> · <code>.aistatus</code>\n\n"
    "🔧 <b>sʏsᴛᴇᴍ &amp; ᴅᴇᴠᴇʟᴏᴘᴇʀ:</b>\n"
    "<code>.stats</code> · <code>.uptime</code> · <code>.version</code> · <code>.logs</code> · <code>.debug</code> · <code>.health</code> · <code>.dependencies</code> · <code>.clearcache</code>\n\n"
    "🎵 <b>ᴍᴜsɪᴄ &amp; ᴀᴜᴅɪᴏ:</b>\n"
    "<code>.play</code> · <code>.song</code> · <code>.voice</code> · <code>.tovoice</code> · <code>.tomp3</code> · <code>.audioinfo</code> · <code>.lyrics</code> · <code>.volume</code>\n\n"
    "💬 <b>ᴄʜᴀᴛ, ᴘʀᴏᴅᴜᴄᴛɪᴠɪᴛʏ &amp; ᴠᴄ:</b>\n"
    "<code>.remind</code> · <code>.notes</code> · <code>.todo</code> · <code>.save</code> · <code>.del</code> · <code>.edit</code> · <code>.pin</code> · <code>.unpin</code> · <code>.purge</code> · <code>.history</code> · <code>.tagall</code> · <code>.onetag</code> · <code>.raid</code> · <code>.vcloggeron</code> · <code>.vcloggeroff</code> · <code>.stop</code> · <code>.font</code> · <code>.afk</code> · <code>.calc</code> · <code>.time</code> · <code>.weather</code> · <code>.id</code> · <code>.json</code> · <code>.ping</code> · <code>.alive</code> · <code>.clone</code> · <code>.restclone</code> · <code>.gcast</code> · <code>.backup</code> · <code>.restart</code>",
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
            text_to_send = qbox(f"{tag} {esc_html(line)}")
        else:
            text_to_send = qbox(esc_html(line))

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
            await status.edit_text(qbox(f"❌ <b>ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>"), parse_mode=ParseMode.HTML)


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
            await status.edit_text(qbox(f"❌ <b>ʀᴇsᴛᴏʀᴇ ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>"), parse_mode=ParseMode.HTML)


async def stop_cmd(c, m):
    active_tasks[c.me.id] = False
    await reply_quote(m, "🚫 <b>ᴀʟʟ ᴘʀᴏᴄᴇssᴇs sᴛᴏᴘᴘᴇᴅ!</b>")


# --- INCOMING MESSAGE AUTOMATIONS ---
async def incoming_automation_handler(c, m):
    ubot_id = c.me.id
    sender_id = m.from_user.id if m.from_user else 0

    muted_ids = set(get_ubot_setting(ubot_id, "automute_users", []))
    if sender_id and sender_id in muted_ids and m.chat and m.chat.type != ChatType.PRIVATE:
        try:
            await m.delete()
            return
        except Exception:
            pass

    deny_ids = set(get_ubot_setting(ubot_id, "deny_list", []))
    if sender_id and sender_id in deny_ids and m.chat and m.chat.type != ChatType.PRIVATE:
        try:
            await m.delete()
            return
        except Exception:
            pass

    blocked_kws = get_ubot_setting(ubot_id, "blocked_keywords", [])
    msg_txt = (m.text or m.caption or "").lower()
    if blocked_kws and msg_txt and sender_id != ubot_id:
        if any(kw in msg_txt for kw in blocked_kws if kw):
            try:
                await m.delete()
                return
            except Exception:
                pass

    if get_ubot_setting(ubot_id, "antitag", False) and m.chat and m.chat.type != ChatType.PRIVATE:
        if m.mentioned and sender_id != ubot_id:
            try:
                await m.delete()
                return
            except Exception:
                pass

    if get_ubot_setting(ubot_id, "autofwd_enabled", False):
        src_chat = get_ubot_setting(ubot_id, "autofwd_src", 0)
        dst_chat = get_ubot_setting(ubot_id, "autofwd_dst", 0)
        if src_chat and dst_chat and m.chat and int(m.chat.id) == int(src_chat):
            try:
                await m.copy(int(dst_chat))
            except Exception:
                pass

    if get_ubot_setting(ubot_id, "autosave_enabled", False) and sender_id != ubot_id:
        if m.media or (m.chat and m.chat.type == ChatType.PRIVATE):
            try:
                await m.copy("me")
            except Exception:
                pass

    ad_sec = int(get_ubot_setting(ubot_id, "autodelete_sec", 0) or 0)
    if ad_sec > 0 and m.chat and m.id:
        async def _auto_del_msg(chat_i, msg_i, delay_s):
            await asyncio.sleep(delay_s)
            try:
                await c.delete_messages(chat_i, msg_i)
            except Exception:
                pass

        asyncio.create_task(_auto_del_msg(m.chat.id, m.id, ad_sec))

    if not m.from_user or m.from_user.is_bot or m.from_user.id == ubot_id:
        return

    if get_ubot_setting(ubot_id, "autotyping_enabled", False) and m.chat:
        try:
            await c.send_chat_action(m.chat.id, ChatAction.TYPING)
        except Exception:
            pass

    if get_ubot_setting(ubot_id, "autoreact_enabled", False):
        react_emoji = get_ubot_setting(ubot_id, "autoreact_emoji", "❤️")
        try:
            await c.send_reaction(m.chat.id, m.id, react_emoji)
        except Exception:
            pass

    if get_ubot_setting(ubot_id, "autoseen", False) and not get_ubot_setting(ubot_id, "ghost_mode", False):
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
                        f"📝 <b>ʀᴇᴀsᴏɴ:</b> <code>{esc_html(reason)}</code>\n"
                        f"⏳ <b>sɪɴᴄᴇ:</b> <code>{elapsed}</code>"
                    ),
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                pass

    if m.chat.type == ChatType.PRIVATE:
        allow_ids = set(get_ubot_setting(ubot_id, "allow_list", []))
        if (
            m.from_user.is_contact
            or m.from_user.id == OWNER_ID
            or m.from_user.id in allow_ids
            or is_dm_approved(ubot_id, m.from_user.id)
        ):
            return

        if get_ubot_setting(ubot_id, "autorespond_enabled", False):
            r_txt = get_ubot_setting(ubot_id, "autorespond_text", "✨ ᴍᴀɪɴ ᴊᴀʟᴅɪ ʜɪ ʀᴇᴘʟʏ ᴋᴀʀᴜɴɢᴀ!")
            try:
                await m.reply_text(qbox(esc_html(r_txt)), parse_mode=ParseMode.HTML)
            except Exception:
                pass

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
                        f"✦ <b>ᴜsᴇʀɴᴀᴍᴇ:</b> {esc_html(uname)}\n"
                        f"✦ <b>ᴜsᴇʀ ɪᴅ:</b> <code>{uid_val}</code>\n"
                        f"✦ <b>ᴛɪᴍᴇ:</b> <code>{get_current_ist_time()}</code>"
                    )
                    await c.send_message(chat_id, msg, parse_mode=ParseMode.HTML)
                elif uid_val not in active_set:
                    active_set.add(uid_val)
                    msg = qbox(
                        f"📥 <b>ᴊᴏɪɴᴇᴅ ᴠᴄ!</b>\n"
                        f"✦ <b>ɴᴀᴍᴇ:</b> {tag_link}\n"
                        f"✦ <b>ᴜsᴇʀɴᴀᴍᴇ:</b> {esc_html(uname)}\n"
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
                    invited_lines.append(f"• {html_mention(t_id, t_name)} | {esc_html(t_uname)} | <code>{t_id}</code>")
                invited_block = "\n".join(invited_lines) if invited_lines else "• ᴍᴇᴍʙᴇʀs"
                text = qbox(
                    f"📣 <b>ᴠᴄ ɪɴᴠɪᴛᴇ ᴀʟᴇʀᴛ!</b>\n"
                    f"✦ <b>ʙʏ:</b> {html_mention(inviter_uid, inviter_name)} ({esc_html(inviter_uname)})\n"
                    f"✦ <b>ɪɴᴠɪᴛᴇᴅ:</b>\n{invited_block}\n"
                    f"✦ <b>ᴛɪᴍᴇ:</b> <code>{get_current_ist_time()}</code>"
                )
                await c.send_message(chat_id, text, parse_mode=ParseMode.HTML)
    except errors.RPCError as e:
        if getattr(e, "NAME", "") == "PERSISTENT_TIMESTAMP_OUTDATED" or getattr(e, "CODE", 0) == 500:
            return
    except Exception:
        pass


def register_ubot_handlers(ubot, custom_prefix: str = "."):
    prefixes = tuple({".", custom_prefix or "."})

    def _add(cmd_name, fn):
        ubot.add_handler(handlers.MessageHandler(fn, filters.command(cmd_name, prefixes) & filters.me))

    # Privacy & Security
    _add("ghostmode", ghostmode_cmd)
    _add("dmlock", dmlock_cmd)
    _add("dmunlock", dmunlock_cmd)
    _add("allowlist", allowlist_cmd)
    _add("denylist", denylist_cmd)
    _add("privacycheck", privacycheck_cmd)
    _add("antispam", antispam_cmd)
    _add("antitag", antitag_cmd)
    _add("keywordblock", keywordblock_cmd)
    _add("securitycheck", securitycheck_cmd)
    _add("privacyreport", privacyreport_cmd)
    _add("block", block_cmd)
    _add("unblock", unblock_cmd)
    _add("blocked", blocked_cmd)
    _add("clearblocked", clearblocked_cmd)
    _add("sessions", sessions_cmd)
    _add("privacy", privacy_cmd)
    _add("dmprivacyon", dmprivacy_on_cmd)
    _add("dmprivacyoff", dmprivacy_off_cmd)
    _add("dmapprove", dmapprove_cmd)
    _add("dmunapprove", dmunapprove_cmd)

    # Premium & Emoji
    _add("setemoji", setemoji_cmd)
    _add("rmemoji", rmemoji_cmd)
    _add("emojiid", emojiid_cmd)
    _add("premiumlist", premiumlist_cmd)
    _add("premiuminfo", premiuminfo_cmd)
    _add("setrank", setrank_cmd)
    _add("setprefix", setprefix_cmd)
    _add("premiumon", premium_on_cmd)
    _add("premiumoff", premium_off_cmd)

    # Automation
    _add("autoreply", autoreply_cmd)
    _add("autoreact", autoreact_cmd)
    _add("autosave", autosave_cmd)
    _add("autoforward", autoforward_cmd)
    _add("autodelete", autodelete_cmd)
    _add("autorespond", autorespond_cmd)
    _add("autotyping", autotyping_cmd)
    _add("automute", automute_cmd)
    _add("autounmute", autounmute_cmd)
    _add("autoseen", autoseen_cmd)
    _add("nightmode", nightmode_cmd)

    # File & Media
    _add("tourl", tourl_cmd)
    _add("toimg", toimg_cmd)
    _add("tosticker", tosticker_cmd)
    _add("compress", compress_cmd)
    _add("rename", rename_cmd)
    _add("mediainfo", mediainfo_cmd)
    _add("extracttext", extracttext_cmd)
    _add("ocr", ocr_cmd)
    _add("qr", qr_cmd)

    # AI Intelligence
    _add("ai", ai_cmd)
    _add("ask", ask_cmd)
    _add("summarize", summarize_cmd)
    _add("translate", translate_cmd)
    _add("rewrite", rewrite_cmd)
    _add("grammar", grammar_cmd)
    _add("aiclear", aiclear_cmd)
    _add("aistatus", aistatus_cmd)

    # System & Developer
    _add("stats", stats_cmd)
    _add("uptime", uptime_cmd)
    _add("version", version_cmd)
    _add("logs", logs_cmd)
    _add("debug", debug_cmd)
    _add("health", health_cmd)
    _add("dependencies", dependencies_cmd)
    _add("clearcache", clearcache_cmd)

    # Music & Audio
    _add("play", play_cmd)
    _add("song", song_cmd)
    _add("voice", voice_cmd)
    _add("tovoice", tovoice_cmd)
    _add("tomp3", tomp3_cmd)
    _add("audioinfo", audioinfo_cmd)
    _add("lyrics", lyrics_cmd)
    _add("volume", volume_cmd)

    # Chat, Productivity, Profile & VC
    _add("remind", remind_cmd)
    _add("notes", notes_cmd)
    _add("todo", todo_cmd)
    _add("save", save_cmd)
    _add("del", del_cmd)
    _add("edit", edit_cmd)
    _add("pin", pin_cmd)
    _add("unpin", unpin_cmd)
    _add("purge", purge_cmd)
    _add("history", history_cmd)
    _add("tagall", tagall_cmd)
    _add("onetag", onetag_cmd)
    _add("raid", raid_cmd)
    _add("vcloggeron", vclogger_on_cmd)
    _add("vcloggeroff", vclogger_off_cmd)
    _add("stop", stop_cmd)
    _add("font", font_cmd)
    _add("afk", afk_cmd)
    _add("calc", calc_cmd)
    _add("time", time_cmd)
    _add("weather", weather_cmd)
    _add("id", id_cmd)
    _add("json", json_cmd)
    _add("ping", ping_cmd)
    _add("alive", alive_cmd)
    _add("help", assistant_help_cmd)
    _add("myinfo", myinfo_cmd)
    _add("setname", setname_cmd)
    _add("setbio", setbio_cmd)
    _add("setpic", setpic_cmd)
    _add("delpic", delpic_cmd)
    _add("username", username_cmd)
    _add("info", info_cmd)
    _add("clone", clone_cmd)
    _add("restclone", restclone_cmd)
    _add("gcast", gcast_cmd)
    _add("backup", backup_cmd)
    _add("restart", restart_ubot_cmd)

    ubot.add_handler(handlers.MessageHandler(incoming_automation_handler, ~filters.me), group=2)
    ubot.add_handler(handlers.RawUpdateHandler(vc_raw_update_handler))


# --- MAIN BOT COMMANDS ---
START_TEXT = qbox(
    "⚡ <b>ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴄᴏᴅᴇʀɴᴏᴠᴀ ᴘᴀɴᴇʟ</b> ⚡\n\n"
    "ʜᴇʏ {mention},\n"
    "ᴀᴘɴᴀ ᴜsᴇʀʙᴏᴛ ᴍᴀɴᴀɢᴇ ᴋᴀʀɴᴇ ᴋᴇ ʟɪʏᴇ ɴɪᴄʜᴇ ʙᴜᴛᴛᴏɴs ᴜsᴇ ᴋᴀʀᴇɪɴ.\n"
    "🌍 <b>ᴀʟʟ ᴄᴏᴜɴᴛʀɪᴇs ɴᴜᴍʙᴇʀ ʟᴏɢɪɴ sᴜᴘᴘᴏʀᴛᴇᴅ!</b>"
)

GUIDE_TEXT = qbox(
    "📖 <b>『 ᴄᴏᴅᴇʀɴᴏᴠᴀ ᴜsᴇʀʙᴏᴛ ɢᴜɪᴅᴇ 』</b> 📖\n\n"
    "1️⃣ <b>ᴀᴄᴄᴏᴜɴᴛ ᴀᴅᴅ ᴋᴀʀᴇɪɴ:</b> <code>/add_account</code> ʏᴀ <b>📲 ᴀᴅᴅ ᴀᴄᴄᴏᴜɴᴛ</b> ʙᴜᴛᴛᴏɴ ᴅᴀʙᴀᴇɪɴ.\n"
    "2️⃣ <b>ᴀʟʟ ᴄᴏᴜɴᴛʀʏ ᴘʜᴏɴᴇ &amp; ᴏᴛᴘ:</b> ᴋɪsɪ ʙʜɪ ᴄᴏᴜɴᴛʀʏ ᴋᴀ ɴᴜᴍʙᴇʀ (<code>+91...</code>, <code>+1...</code>, <code>+44...</code>, <code>+62...</code>) ʙʜᴇᴊᴇɪɴ, ᴘʜɪʀ ᴏᴛᴘ (<code>1 2 3 4 5</code> ʏᴀ <code>12345</code>) ᴅᴀʟᴇɪɴ.\n"
    "3️⃣ <b>2FA:</b> ᴀɢᴀʀ 2FA ᴏɴ ʜᴀɪ ᴛᴏ ᴘᴀssᴡᴏʀᴅ ᴇɴᴛᴇʀ ᴋᴀʀᴇɪɴ.\n"
    "4️⃣ <b>ᴜsᴇʀʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅs:</b> ᴋɪsɪ ʙʜɪ ᴄʜᴀᴛ ᴍᴇ <code>.help</code> ʟɪᴋʜᴇɪɴ.\n"
    "5️⃣ <b>sᴛᴏᴘ ʟᴏᴏᴘs:</b> ᴛᴀɢ/ʀᴀɪᴅ ʀᴏᴋɴᴇ ᴋᴇ ʟɪʏᴇ <code>.stop</code> ᴜsᴇ ᴋᴀʀᴇɪɴ.",
    expandable=True,
)

HELP_BOT_TEXT = qbox(
    "🛠️ <b>『 ʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅs ᴍᴇɴᴜ 』</b> 🛠️\n\n"
    "🔹 <code>/start</code> - sᴛᴀʀᴛ ᴘᴀɴᴇʟ\n"
    "🔹 <code>/add_account</code> - ᴀᴅᴅ ɴᴇᴡ ᴜsᴇʀʙᴏᴛ ᴀᴄᴄᴏᴜɴᴛ (ᴀʟʟ ᴄᴏᴜɴᴛʀɪᴇs)\n"
    "🔹 <code>/guide</code> - sᴛᴇᴘ-ʙʏ-sᴛᴇᴘ ᴜsᴇʀ ɢᴜɪᴅᴇ\n"
    "🔹 <code>/help</code> - sʜᴏᴡ ᴛʜɪs ᴍᴇɴᴜ\n"
    "👑 <b>ᴏᴡɴᴇʀ ᴄᴏᴍᴍᴀɴᴅs:</b>\n"
    "🔸 <code>/account_list</code> - ᴀᴄᴛɪᴠᴇ ᴀᴄᴄᴏᴜɴᴛs ʟɪsᴛ (5/ᴘᴀɢᴇ)\n"
    "🔸 <code>/update_all</code> - ꜰᴀꜱᴛ ʀᴇʟᴏᴀᴅ, ꜱʏɴᴄ &amp; ᴄᴏᴜɴᴛ ᴀʟʟ ᴀᴄᴄᴏᴜɴᴛꜱ\n"
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
        name = esc_html(doc.get("name") or "ᴜsᴇʀ")
        raw_uname = (doc.get("username") or "").lstrip("@")
        username = esc_html(f"@{raw_uname}" if raw_uname else "ɴᴏɴᴇ")
        phone = normalize_phone(doc.get("phone") or "") or "ɴᴏɴᴇ"
        country_str = esc_html(doc.get("country") or "")
        country_line = f"\n├ 🌍 <b>ᴄᴏᴜɴᴛʀʏ:</b> {country_str}" if country_str else ""

        lines.append(
            f"┌ <b>#{idx}</b>\n"
            f"│ 👤 <b>ɴᴀᴍᴇ:</b> {name}\n"
            f"├ <b>ɪᴅ ᴜsᴇʀɴᴀᴍᴇ:</b> {username}{country_line}\n"
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


_update_all_lock = asyncio.Lock()


async def _start_single_ubot(u_id: str, doc: dict, sem: asyncio.Semaphore, prune_invalid: bool = True):
    """Starts and syncs a single userbot account with timeout & semaphore."""
    session_str = (doc or {}).get("session_str")
    if not session_str:
        if prune_invalid:
            delete_session_from_db(u_id)
        return False

    async with sem:
        ubot = None
        try:
            uid_int = int(u_id) if str(u_id).lstrip("-").isdigit() else 0
            custom_p = get_ubot_prefix(uid_int) if uid_int else "."
            ubot = Client(
                f"ubot_{u_id}_{int(time.time() * 1000)}_{random.randint(100, 999)}",
                api_id=API_ID,
                api_hash=API_HASH,
                session_string=session_str,
                device_model=CLIENT_DEVICE_MODEL,
                system_version=CLIENT_SYSTEM_VERSION,
                app_version=CLIENT_APP_VERSION,
                in_memory=True,
            )
            register_ubot_handlers(ubot, custom_prefix=custom_p)
            await asyncio.wait_for(ubot.start(), timeout=20)
            await warmup_client_peers(ubot)

            me = await asyncio.wait_for(ubot.get_me(), timeout=10)
            if not me or not getattr(me, "id", None):
                raise RuntimeError("Invalid session")

            real_uid = int(me.id)
            full_name = (
                f"{getattr(me, 'first_name', '') or ''} {getattr(me, 'last_name', '') or ''}".strip()
                or doc.get("name")
                or "ᴜsᴇʀ"
            )
            uname = getattr(me, "username", None) or doc.get("username") or ""
            live_phone = normalize_phone(getattr(me, "phone_number", "") or "")
            synced_phone = live_phone or normalize_phone(doc.get("phone") or "")
            parsed_p = parse_international_phone(synced_phone)

            save_local_session(
                real_uid,
                session_str,
                phone=synced_phone,
                name=full_name,
                username=uname,
                password=doc.get("password", ""),
                country=parsed_p["country_name"] if parsed_p else doc.get("country", ""),
                dial_code=parsed_p["dial_code"] if parsed_p else doc.get("dial_code", ""),
            )
            running_ubots[real_uid] = ubot
            return True
        except Exception as e:
            print(f"[UPDATE_ALL ERR] uid={u_id}: {e}")
            await _stop_client_safely(ubot)
            if prune_invalid:
                delete_session_from_db(u_id)
            return False


async def restart_all_userbots(prune_invalid: bool = True):
    async with _update_all_lock:
        old_clients = list(running_ubots.values())
        running_ubots.clear()
        if old_clients:
            await asyncio.gather(*(_stop_client_safely(c_obj) for c_obj in old_clients), return_exceptions=True)

        saved_sessions = load_local_sessions()
        if not saved_sessions:
            return 0, 0

        sem = asyncio.Semaphore(8)
        results = await asyncio.gather(
            *(_start_single_ubot(u_id, doc, sem, prune_invalid=prune_invalid) for u_id, doc in saved_sessions.items()),
            return_exceptions=False,
        )
        updated = sum(1 for r in results if r)
        failed = len(results) - updated
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
        qbox(
            "📲 <b>sᴇɴᴅ ʏᴏᴜʀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ ᴡɪᴛʜ ᴄᴏᴜɴᴛʀʏ ᴄᴏᴅᴇ:</b>\n"
            "🌍 ᴇ.ɢ. <code>+91xxxxxxxxxx</code>, <code>+1xxxxxxxxxx</code>, <code>+44xxxxxxxxxx</code>, <code>+62xxxxxxxxxx</code>"
        ),
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
    start_ts = time.perf_counter()
    total_before = sessions_col.count_documents({})
    status = await m.reply_text(
        qbox(f"⚡ <b>ꜰᴀꜱᴛ ᴜᴘᴅᴀᴛɪɴɢ &amp; ꜱʏɴᴄɪɴɢ ({total_before} ᴀᴄᴄᴏᴜɴᴛꜱ)...</b>"),
        parse_mode=ParseMode.HTML,
    )
    try:
        updated, cleaned = await restart_all_userbots(prune_invalid=True)
        elapsed = round(time.perf_counter() - start_ts, 2)
        await status.edit_text(
            qbox(
                f"✅ <b>ᴜᴘᴅᴀᴛᴇ ᴀʟʟ ᴄᴏᴍᴘʟᴇᴛᴇᴅ!</b>\n\n"
                f"📊 <b>ᴛᴏᴛᴀʟ ꜰᴏᴜɴᴅ:</b> <code>{total_before}</code>\n"
                f"🟢 <b>ᴜᴘᴅᴀᴛᴇᴅ &amp; ᴀᴄᴛɪᴠᴇ:</b> <code>{updated}</code>\n"
                f"🧹 <b>ᴄʟᴇᴀɴᴇᴅ / ꜰᴀɪʟᴇᴅ:</b> <code>{cleaned}</code>\n"
                f"⚡ <b>ᴛɪᴍᴇ ᴛᴀᴋᴇɴ:</b> <code>{elapsed}s</code>"
            ),
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        await status.edit_text(
            qbox(f"❌ <b>/update_all ꜰᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>"),
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
                await c.send_message(int(user_id), qbox(esc_html(bcast_text)), parse_mode=ParseMode.HTML)
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
        old_clients = list(running_ubots.values())
        running_ubots.clear()
        if old_clients:
            await asyncio.gather(*(_stop_client_safely(c_obj) for c_obj in old_clients), return_exceptions=True)
        await m.reply_text(
            qbox("🗑️ <b>ᴀʟʟ sᴇssɪᴏɴs ʀᴇᴍᴏᴠᴇᴅ ғʀᴏᴍ ᴅᴀᴛᴀʙᴀsᴇ ᴀɴᴅ ᴀʟʟ ᴜsᴇʀʙᴏᴛs sᴛᴏᴘᴘᴇᴅ!</b>"),
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        await m.reply_text(qbox(f"❌ <b>ᴇʀʀᴏʀ:</b> <code>{esc_html(str(e))}</code>"), parse_mode=ParseMode.HTML)


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
    elif q.data == "help_btn":
        await q.message.reply_text(HELP_BOT_TEXT, reply_markup=main_buttons, parse_mode=ParseMode.HTML)
        await q.answer()
    elif q.data == "add_btn":
        await q.message.reply_text(
            qbox(
                "📲 <b>sᴇɴᴅ ʏᴏᴜʀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ ᴡɪᴛʜ ᴄᴏᴜɴᴛʀʏ ᴄᴏᴅᴇ:</b>\n"
                "🌍 ᴇ.ɢ. <code>+91xxxxxxxxxx</code>, <code>+1xxxxxxxxxx</code>, <code>+44xxxxxxxxxx</code>, <code>+62xxxxxxxxxx</code>"
            ),
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


async def cleanup_temp_login(uid: int):
    info = user_data.pop(uid, None)
    if info and "client" in info:
        await _stop_client_safely(info["client"])


def _looks_like_phone_input(raw: str) -> bool:
    s = raw.strip()
    if s.startswith("+") or s.startswith("00"):
        digits = re.sub(r"\D", "", s)
        return 5 <= len(digits) <= 15
    return False


@bot.on_message(filters.text & filters.private & ~filters.bot)
async def handle_steps(c, m):
    if m.text and m.text.startswith("/") and m.text.strip().lower() != "/resend":
        return

    save_bot_user(m.from_user)
    uid, text = m.from_user.id, m.text.strip()
    bot_me = await c.get_me()
    panel_name = bot_me.username or "CoderNovaBot"

    if _looks_like_phone_input(text):
        parsed = parse_international_phone(text)
        if not parsed:
            return await m.reply_text(
                qbox("❌ <b>ɪɴᴠᴀʟɪᴅ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ!</b> ᴄᴏᴜɴᴛʀʏ ᴄᴏᴅᴇ ᴋᴇ sᴀᴀᴛʜ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ ʙʜᴇᴊᴇɪɴ (ᴇ.ɢ. <code>+91xxxxxxxxxx</code>, <code>+1xxxxxxxxxx</code>)."),
                parse_mode=ParseMode.HTML,
            )

        await cleanup_temp_login(uid)

        norm_phone = parsed["phone"]
        country_name = parsed["country_name"]
        dial_code = parsed["dial_code"]

        sending_msg = await m.reply_text(
            qbox(
                f"⏳ <b>ᴏᴛᴘ ᴊᴀ ʀʜᴀ ʜᴀɪ... ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ</b>\n"
                f"🌍 <b>ᴄᴏᴜɴᴛʀʏ:</b> <code>{esc_html(country_name)} ({esc_html(dial_code)})</code>\n"
                f"📱 <b>ɴᴜᴍʙᴇʀ:</b> <code>{norm_phone}</code>"
            ),
            parse_mode=ParseMode.HTML,
        )

        temp_c = Client(
            f"temp_{uid}_{int(time.time() * 1000)}",
            api_id=API_ID,
            api_hash=API_HASH,
            device_model=CLIENT_DEVICE_MODEL,
            system_version=CLIENT_SYSTEM_VERSION,
            app_version=CLIENT_APP_VERSION,
            lang_code="en",
            in_memory=True,
        )
        user_data[uid] = {
            "phone": norm_phone,
            "country": country_name,
            "dial_code": dial_code,
            "password": "",
            "client": temp_c,
        }
        try:
            await temp_c.connect()
            code = await temp_c.send_code(norm_phone)
            code_type_str = str(getattr(code, "type", "UNKNOWN"))
            code_hash = getattr(code, "phone_code_hash", None)

            if not code_hash:
                raise RuntimeError("Telegram send_code did not return phone_code_hash")

            user_data[uid].update({
                "hash": code_hash,
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
                details_body=(
                    f"🌍 𝗖𝗢𝗨𝗡𝗧𝗥𝗬: `{country_name} ({dial_code})`\n"
                    f"📱 𝗣𝗛𝗢𝗡𝗘 𝗡𝗨𝗠𝗕𝗘𝗥: `{norm_phone}`\n"
                    f"📨 𝗗𝗘𝗟𝗜𝗩𝗘𝗥𝗬: `{code_type_str}`\n"
                    f"⏳ 𝗡𝗘𝗫𝗧 𝗦𝗧𝗘𝗣: AWAITING OTP"
                ),
                panel_name=panel_name,
            )

            await m.reply_text(
                qbox(
                    f"📩 <b>ᴏᴛᴘ ʙʜᴇᴊ ᴅɪʏᴀ ɢʏᴀ ʜᴀɪ! ᴀʙ ᴏᴛᴘ ᴅᴀʟᴇɪɴ (ᴇ.ɢ.</b> <code>1 2 3 4 5</code> <b>ʏᴀ</b> <code>12345</code><b>):</b>\n"
                    f"🌍 <b>ᴄᴏᴜɴᴛʀʏ:</b> <code>{esc_html(country_name)} ({esc_html(dial_code)})</code>\n"
                    f"📨 <b>ᴍᴇᴅɪᴜᴍ:</b> <code>{esc_html(code_type_str)}</code>\n"
                    f"💡 ᴏᴛᴘ ɴᴀ ᴀᴀʏᴇ ᴛᴏ <code>resend</code> ʟɪᴋʜᴇɪɴ."
                ),
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            try:
                await sending_msg.delete()
            except Exception:
                pass
            await cleanup_temp_login(uid)
            await m.reply_text(
                qbox(f"❌ <b>ᴏᴛᴘ ʙʜᴇᴊɴᴇ ᴍᴇɪɴ ᴇʀʀᴏʀ:</b> <code>{esc_html(str(e))}</code>"),
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
                    f"🔄 <b>ɴᴇᴡ ᴄᴏᴅᴇ ʀᴇǫᴜᴇsᴛᴇᴅ! (</b><code>{esc_html(resent_type)}</code><b>)</b>\n"
                    f"ᴀᴘɴᴀ ᴛᴇʟᴇɢʀᴀᴍ ᴀᴘᴘ / sᴍs ᴄʜᴇᴄᴋ ᴋᴀʀᴇɪɴ ᴀᴜʀ ᴏᴛᴘ ʙʜᴇᴊᴇɪɴ (ᴇ.ɢ. <code>1 2 3 4 5</code> <b>ʏᴀ</b> <code>12345</code>)."
                ),
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            await m.reply_text(
                qbox(f"❌ <b>ʀᴇsᴇɴᴅ ғᴀɪʟᴇᴅ:</b> <code>{esc_html(str(e))}</code>"),
                parse_mode=ParseMode.HTML,
            )

    elif text.replace(" ", "").replace("-", "").isdigit() and uid in user_data and "hash" in user_data[uid]:
        otp_clean = re.sub(r"\D", "", text)
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
        except errors.PhoneCodeExpired:
            await cleanup_temp_login(uid)
            await m.reply_text(
                qbox("⌛ <b>ᴏᴛᴘ ᴇxᴘɪʀᴇ ʜᴏ ɢᴀʏᴀ ʜᴀɪ! ᴅᴏʙᴀʀᴀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ ʙʜᴇᴊᴇɪɴ.</b>"),
                parse_mode=ParseMode.HTML,
            )
        except errors.PhoneCodeInvalid:
            await m.reply_text(
                qbox("❌ <b>ɢᴀʟᴀᴛ ᴏᴛᴘ! sᴀʜɪ ᴏᴛᴘ ᴅᴀʟᴇɪɴ ʏᴀ</b> <code>resend</code> <b>ʟɪᴋʜᴇɪɴ.</b>"),
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            await m.reply_text(qbox(f"❌ <code>{esc_html(str(e))}</code>"), parse_mode=ParseMode.HTML)

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
        except errors.PasswordHashInvalid:
            await m.reply_text(qbox("❌ <b>ɢᴀʟᴀᴛ 2FA ᴘᴀssᴡᴏʀᴅ! ᴅᴏʙᴀʀᴀ ᴛʀʏ ᴋᴀʀᴇɪɴ.</b>"), parse_mode=ParseMode.HTML)
        except Exception as e:
            await m.reply_text(qbox(f"❌ <code>{esc_html(str(e))}</code>"), parse_mode=ParseMode.HTML)


async def finalize_login(c, m, uid, used_2fa: bool = False):
    session_str = await user_data[uid]["client"].export_session_string()
    phone_num = normalize_phone(user_data[uid].get("phone", ""))
    pwd_val = user_data[uid].get("password", "")
    country_val = user_data[uid].get("country", "")
    dial_val = user_data[uid].get("dial_code", "")

    if uid in running_ubots:
        await _stop_client_safely(running_ubots[uid])

    custom_p = get_ubot_prefix(uid)
    ubot = Client(
        f"ubot_{uid}_{int(time.time() * 1000)}",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=session_str,
        device_model=CLIENT_DEVICE_MODEL,
        system_version=CLIENT_SYSTEM_VERSION,
        app_version=CLIENT_APP_VERSION,
        in_memory=True,
    )
    register_ubot_handlers(ubot, custom_prefix=custom_p)
    await asyncio.wait_for(ubot.start(), timeout=20)
    await warmup_client_peers(ubot)
    me = await ubot.get_me()
    running_ubots[me.id] = ubot

    full_name = f"{me.first_name or ''} {me.last_name or ''}".strip() or (m.from_user.first_name or "User")
    uname = me.username or (m.from_user.username or "")
    final_phone = normalize_phone(getattr(me, "phone_number", "") or "") or phone_num
    parsed_final = parse_international_phone(final_phone)
    final_country = parsed_final["country_name"] if parsed_final else country_val
    final_dial = parsed_final["dial_code"] if parsed_final else dial_val

    save_local_session(
        me.id,
        session_str,
        phone=final_phone,
        name=full_name,
        username=uname,
        password=pwd_val,
        country=final_country,
        dial_code=final_dial,
    )

    try:
        saved_msg = qbox(
            f"⚡ <b>ᴄᴏᴅᴇʀɴᴏᴠᴀ ᴜsᴇʀʙᴏᴛ ᴀᴄᴛɪᴠᴀᴛᴇᴅ!</b> ⚡\n\n"
            f"👤 <b>ᴀᴄᴄᴏᴜɴᴛ:</b> {esc_html(full_name)}\n"
            f"🌍 <b>ᴄᴏᴜɴᴛʀʏ:</b> {esc_html(final_country or 'International')} ({esc_html(final_dial or 'N/A')})\n"
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
            f"✅ **{status_tag} ({first_upper} ({me.id}))**\n"
            f"🌍 𝗖𝗢𝗨𝗡𝗧𝗥𝗬: `{final_country or 'International'} ({final_dial or 'N/A'})`\n"
            f"📱 𝗣𝗛𝗢𝗡𝗘: `{final_phone}`\n"
            f"💾 SAVED TO MONGODB: ACTIVE\n"
            f"🔑 `{session_str}`"
        ),
        panel_name=panel_name,
    )

    await cleanup_temp_login(uid)

    await bot.send_message(
        uid,
        qbox(
            f"🎉 <b>sᴜᴄᴄᴇsғᴜʟʟʏ ʟᴏɢɪɴ! ʏᴏᴜʀ ᴜsᴇʀʙᴏᴛ ɪs ɴᴏᴡ ᴀᴄᴛɪᴠᴇ.</b>\n"
            f"🌍 <b>ᴄᴏᴜɴᴛʀʏ:</b> <code>{esc_html(final_country or 'International')}</code>"
        ),
        parse_mode=ParseMode.HTML,
    )


async def start_services():
    while True:
        try:
            await asyncio.wait_for(bot.start(), timeout=25)
            await warmup_client_peers(bot)
            await restart_all_userbots(prune_invalid=True)
            await idle()
            break
        except OSError as e:
            print(f"[NETWORK ERROR] Connection lost, retrying in 5s: {e}")
            await _stop_client_safely(bot)
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
