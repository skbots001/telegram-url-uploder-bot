import os
import requests
from pyrogram import Client, filters
from pyrogram.types import Message

# Get your Telegram API credentials from environment variables
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client("URLUploaderBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Directory to store files temporarily
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.on_message(filters.command("upload") & filters.private)
async def upload_file(client, message: Message):
    if len(message.command) < 2:
        await message.reply("Please send a valid URL!\nExample: `/upload https://example.com/file.mp4`")
        return

    url = message.command[1]
    file_name = url.split("/")[-1]
    file_path = os.path.join(DOWNLOAD_FOLDER, file_name)

    await message.reply(f"Downloading `{file_name}`...")

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
            caption=f"Here is your file: `{file_name}`"
        )

        os.remove(file_path)  # Clean up the file after sending it
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

if __name__ == "__main__":
    app.run(
