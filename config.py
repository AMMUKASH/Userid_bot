import os

# --- TELEGRAM API & BOT CONFIG ---
API_ID = int(os.environ.get("API_ID", 31980984))
API_HASH = os.environ.get("API_HASH", "a61358dd3cd8c3a56cd53d9ddd8a0c67")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8709782891:AAHhT65venvu-KbJO8Q7zJoBcMXNdrj7deo")

# --- LOGS & DATABASE ---
LOG_GROUP = int(os.environ.get("LOG_GROUP", -1003947649552))
MONGO_URL = os.environ.get(
    "MONGO_URL",
    "mongodb+srv://misssqn_db_user:Nova01@cluster0.6xxsrwq.mongodb.net/?retryWrites=true&w=majority",
)
DB_NAME = os.environ.get("DB_NAME", "CoderNovaBotDB")

# --- CHANNELS, MEDIA & OWNER ---
FSUB_CHANNELS = ["NovaBot_Support", "Friend_Forevrrr", "Villain_Loves", "SticrAura"]
START_VIDEO = os.environ.get("START_VIDEO", "https://files.catbox.moe/pnaxj0.mp4")
ALIVE_IMG = os.environ.get(
    "ALIVE_IMG",
    "https://graph.org/file/422440e09d466500f2c93-953253772b0d8d2bfc.jpg",
)
OWNER_ID = int(os.environ.get("OWNER_ID", 8724182918))
OWNER_USERNAME = os.environ.get("OWNER_USERNAME", "@CoderNova")

# --- WEB SERVER ---
PORT = int(os.environ.get("PORT", 8080))
