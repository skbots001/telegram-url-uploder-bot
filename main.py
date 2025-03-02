import os
import requests
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from moviepy.editor import VideoFileClip  # For video compression
from pyrogram.errors import RPCError

# Telegram API Credentials
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))  # Ensure this is an integer

app = Client("URLUploaderBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Directory to store files temporarily
DOWNLOAD_FOLDER = "downloads"
COMPRESSED_FOLDER = "compressed"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(COMPRESSED_FOLDER, exist_ok=True)

# Function to send progress updates
async def progress_callback(current, total, message: Message):
    percent = int((current / total) * 100)
    await message.edit(f"📥 Downloading... {percent}%")

# Video Compression Function
def compress_video(input_file, output_file, target_size=1900):
    try:
        clip = VideoFileClip(input_file)
        clip_resized = clip.resize(height=480)  # Resize for compression
        clip_resized.write_videofile(output_file, bitrate="1000k", codec="libx264")
        return output_file
    except Exception as e:
        return None

@app.on_message(filters.command("upload") & filters.private)
async def upload_file(client, message: Message):
    if len(message.command) < 2:
        await message.reply("❌ Please send a valid URL!\nExample: `/upload https://example.com/file.mp4`")
        return

    url = message.command[1]
    file_name = url.split("/")[-1]
    file_path = os.path.join(DOWNLOAD_FOLDER, file_name)
    compressed_file_path = os.path.join(COMPRESSED_FOLDER, "compressed_" + file_name)

    # Notify user about download start
    progress_msg = await message.reply(f"📥 Downloading `{file_name}`...")

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, stream=True, headers=headers)
        response.raise_for_status()
        
        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)

        await progress_msg.edit(f"✅ Download complete! Uploading `{file_name}` to Telegram...")

        # Check if the file is a video and needs compression
        if file_name.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
            if file_size > 2000:  # If file is over 2GB, compress it
                await progress_msg.edit("⚠️ Video too large! Compressing...")
                compressed_file = compress_video(file_path, compressed_file_path)
                if compressed_file:
                    file_path = compressed_file
                    await progress_msg.edit("✅ Compression Complete! Uploading now...")
                else:
                    await progress_msg.edit("❌ Compression failed! Uploading original file...")

            # Send video
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

        os.remove(file_path)  # Clean up the file after sending it
        if os.path.exists(compressed_file_path):
            os.remove(compressed_file_path)

    except RPCError as rpc_error:
        await progress_msg.edit(f"❌ Telegram Error: {rpc_error}")
    except Exception as e:
        await progress_msg.edit(f"❌ Error: {e}")

if __name__ == "__main__":
    app.run()
