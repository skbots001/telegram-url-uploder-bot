import os
import requests
import asyncio
import mimetypes
import re
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import RPCError
from moviepy.editor import VideoFileClip

# Load API credentials from environment variables
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))  # Admin only commands

app = Client("AdvancedUploaderBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Directories for storage
DOWNLOAD_FOLDER = "downloads"
COMPRESSED_FOLDER = "compressed"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(COMPRESSED_FOLDER, exist_ok=True)

# Extract final direct link from Google Drive, Dropbox, etc.
def get_final_url(url):
    try:
        session = requests.Session()
        response = session.head(url, allow_redirects=True)
        return response.url
    except Exception as e:
        return None

# Progress callback
async def progress_callback(current, total, message: Message):
    percent = int((current / total) * 100)
    await message.edit(f"📥 Downloading... {percent}%")

# Video Compression
def compress_video(input_file, output_file):
    try:
        clip = VideoFileClip(input_file)
        clip_resized = clip.resize(height=480)
        clip_resized.write_videofile(output_file, bitrate="800k", codec="libx264")
        return output_file
    except Exception as e:
        return None

# Function to validate URL
def is_valid_url(url):
    regex = re.compile(r'^(https?|ftp)://[^\s/$.?#].[^\s]*$', re.IGNORECASE)
    return re.match(regex, url) is not None

# Command to upload file from URL
@app.on_message(filters.command("upload") & filters.private)
async def upload_file(client, message: Message):
    if len(message.command) < 2:
        await message.reply("❌ Please provide a valid URL!\nExample: `/upload https://example.com/file.mp4`")
        return

    url = message.command[1]

    if not is_valid_url(url):
        await message.reply("❌ Invalid URL format! Please send a direct link.")
        return

    final_url = get_final_url(url)
    if not final_url:
        await message.reply("❌ Failed to resolve direct link!")
        return

    file_name = final_url.split("/")[-1]
    file_path = os.path.join(DOWNLOAD_FOLDER, file_name)
    compressed_file_path = os.path.join(COMPRESSED_FOLDER, "compressed_" + file_name)

    progress_msg = await message.reply(f"📥 Downloading `{file_name}`...")

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(final_url, stream=True, headers=headers)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))

        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                file.write(chunk)

        await progress_msg.edit(f"✅ Download complete! Uploading `{file_name}` to Telegram...")

        # Check if file is a video
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type and "video" in mime_type:
            file_size = os.path.getsize(file_path) / (1024 * 1024)

            if file_size > 2000:  # Compress if over 2GB
                await progress_msg.edit("⚠️ Video too large! Compressing...")
                compressed_file = compress_video(file_path, compressed_file_path)
                if compressed_file:
                    file_path = compressed_file
                    await progress_msg.edit("✅ Compression complete! Uploading now...")
                else:
                    await progress_msg.edit("❌ Compression failed! Uploading original file...")

            await client.send_video(
                chat_id=message.chat.id,
                video=file_path,
                caption=f"🎥 Here is your video: `{file_name}`"
            )
        else:
            await client.send_document(
                chat_id=message.chat.id,
                document=file_path,
                caption=f"📁 Here is your file: `{file_name}`"
            )

        os.remove(file_path)
        if os.path.exists(compressed_file_path):
            os.remove(compressed_file_path)

    except RPCError as rpc_error:
        await progress_msg.edit(f"❌ Telegram Error: {rpc_error}")
    except Exception as e:
        await progress_msg.edit(f"❌ Error: {e}")

# Admin-only command to clear all files
@app.on_message(filters.command("clear") & filters.user(ADMIN_ID))
async def clear_files(client, message: Message):
    for folder in [DOWNLOAD_FOLDER, COMPRESSED_FOLDER]:
        for file in os.listdir(folder):
            os.remove(os.path.join(folder, file))
    await message.reply("✅ All stored files have been deleted!")

if __name__ == "__main__":
    app.run()
