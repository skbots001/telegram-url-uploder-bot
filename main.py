import os
import requests
import threading
from flask import Flask
from pyrogram import Client, filters
from pyrogram.types import Message

# Get your Telegram API credentials from environment variables
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))  # Ensure ADMIN_ID is an integer

app = Client("URLUploaderBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Directory to store files temporarily
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.on_message(filters.command("start") & filters.private)
async def start(client, message: Message):
    await message.reply("👋 Hello! I am a URL Uploader Bot.\nSend me a URL with `/upload <URL>` to start.")

@app.on_message(filters.command("help") & filters.private)
async def help_command(client, message: Message):
    help_text = "📌 **Available Commands:**\n"
    help_text += "/start - Welcome message\n"
    help_text += "/upload <URL> - Upload file from URL\n"
    help_text += "/help - Show this message\n"
    
    if message.from_user.id == ADMIN_ID:
        help_text += "\n⚙️ **Admin Commands:**\n"
        help_text += "/stats - Show bot usage stats\n"
    
    await message.reply(help_text)

@app.on_message(filters.command("upload") & filters.private)
async def upload_file(client, message: Message):
    if len(message.command) < 2:
        await message.reply("❌ Please send a valid URL!\nExample: `/upload https://example.com/file.mp4`")
        return

    url = message.command[1]
    file_name = url.split("/")[-1]
    file_path = os.path.join(DOWNLOAD_FOLDER, file_name)

    await message.reply(f"📥 Downloading `{file_name}`...")

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)

        await message.reply(f"✅ Download complete! Uploading `{file_name}` to Telegram...")

        await client.send_document(
            chat_id=message.chat.id,
            document=file_path,
            caption=f"📂 Here is your file: `{file_name}`"
        )

        os.remove(file_path)  # Clean up the file after sending it
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

@app.on_message(filters.command("stats") & filters.private)
async def stats(client, message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("❌ You are not authorized to use this command!")
        return
    
    file_count = len(os.listdir(DOWNLOAD_FOLDER))
    await message.reply(f"📊 **Bot Stats:**\nFiles stored: {file_count}")

# Flask app for health check
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app_flask.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()  # Start Flask health check server
    app.run()  # Start Telegram bot
