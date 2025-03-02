import os
import logging
import requests
from pyrogram import Client, filters
from pyrogram.types import Message

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment variables
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))  # Replace with your Telegram user ID

# Max file size limit (2GB for Telegram)
MAX_FILE_SIZE_MB = 2048

app = Client("URLUploaderBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Directory to store files temporarily
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Dictionary to store bot usage stats
stats = {"uploads": 0, "users": set()}

# Admin check function
def is_admin(user_id):
    return user_id == ADMIN_ID

# Start command
@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message: Message):
    stats["users"].add(message.chat.id)
    await message.reply(
        "👋 **Welcome to the URL Uploader Bot!**\n\n"
        "📥 Send a URL to download and upload it to Telegram.\n"
        "🔹 Use `/upload <URL>` to start.\n"
        "❓ Use `/help` for more details."
    )

# Help command
@app.on_message(filters.command("help") & filters.private)
async def help_command(client, message: Message):
    await message.reply(
        "**ℹ️ How to Use the Bot:**\n\n"
        "📌 **Upload a file** – Send a URL like this:\n"
        "`/upload https://example.com/file.mp4`\n\n"
        "⚠️ **Limitations:**\n"
        "🔸 Max file size: **2GB**\n"
        "🔸 Some websites may block downloads\n\n"
        "🛠 **Developed by:** Your Name"
    )

# Upload command
@app.on_message(filters.command("upload") & filters.private)
async def upload_file(client, message: Message):
    if len(message.command) < 2:
        await message.reply("⚠️ Please send a valid URL!\nExample: `/upload https://example.com/file.mp4`")
        return

    url = message.command[1]
    file_name = url.split("/")[-1]
    file_path = os.path.join(DOWNLOAD_FOLDER, file_name)

    await message.reply(f"⏳ Downloading `{file_name}`...")

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # Check file size
        file_size_mb = int(response.headers.get("content-length", 0)) / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            await message.reply(f"❌ File too large! Max allowed size is **{MAX_FILE_SIZE_MB}MB**.")
            return

        # Save the file
        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)

        await message.reply(f"✅ Download complete! Uploading `{file_name}` to Telegram...")

        await client.send_document(
            chat_id=message.chat.id,
            document=file_path,
            caption=f"📁 Here is your file: `{file_name}`"
        )

        os.remove(file_path)  # Clean up after upload
        stats["uploads"] += 1
    except Exception as e:
        logger.error(f"Error: {e}")
        await message.reply(f"❌ Error: {e}")

# Admin Command: Check Stats
@app.on_message(filters.command("stats") & filters.private)
async def stats_command(client, message: Message):
    if not is_admin(message.from_user.id):
        await message.reply("🚫 **Permission Denied!** This command is for admins only.")
        return

    total_users = len(stats["users"])
    total_uploads = stats["uploads"]
    await message.reply(f"📊 **Bot Stats:**\n👥 Users: {total_users}\n📁 Files Uploaded: {total_uploads}")

# Admin Command: Broadcast Message
@app.on_message(filters.command("broadcast") & filters.private)
async def broadcast_command(client, message: Message):
    if not is_admin(message.from_user.id):
        await message.reply("🚫 **Permission Denied!** This command is for admins only.")
        return

    if len(message.command) < 2:
        await message.reply("⚠️ Usage: `/broadcast Your message here`")
        return

    text = " ".join(message.command[1:])
    for user_id in stats["users"]:
        try:
            await client.send_message(chat_id=user_id, text=f"📢 **Broadcast from Admin:**\n\n{text}")
        except Exception as e:
            logger.error(f"Failed to send message to {user_id}: {e}")

    await message.reply("✅ **Broadcast sent successfully!**")

if __name__ == "__main__":
    app.run()
