import os
import subprocess
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls import PyTgCalls, Stream
import yt_dlp

API_ID = "YOUR_API_ID"
API_HASH = "YOUR_API_HASH"
BOT_TOKEN = "YOUR_BOT_TOKEN"
LOG_GROUP_ID = -1001234567890  # Log group ID
SUPPORT_GROUP = "https://t.me/YOUR_SUPPORT_GROUP"  # Support group link
OWNER_ID = "YOUR_TELEGRAM_USER_ID"

bot = Client("MusicBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
bot_voice = PyTgCalls(bot)

music_queue = {}  # Stores song queues for multiple groups

# 🎵 YouTube Music Download
def download_audio(url, cookies_file="cookies.txt"):
    ydl_opts = {
        "format": "bestaudio/best",
        "cookiefile": cookies_file,  # YouTube cookies support
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}]
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        return info_dict["title"] + ".mp3"

# 🔥 Audio Speed Modification
def change_speed(input_file, output_file, speed=2.0):
    command = ["ffmpeg", "-i", input_file, "-filter:a", f"atempo={speed}", "-vn", output_file]
    subprocess.run(command)

# 🚀 Bot Start Message with Buttons
@bot.on_message(filters.command("start"))
def start(client, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ Powerful Music Bot", url="https://t.me/YOUR_BOT_USERNAME")],
        [InlineKeyboardButton("🔹 Owner Support", url=f"https://t.me/{OWNER_ID}")],
        [InlineKeyboardButton("💬 Support Group", url=SUPPORT_GROUP)]  # Support Button
    ])
    message.reply_text("🎵 Welcome to the Music Bot!\nSend a YouTube link and choose playback speed!", reply_markup=keyboard)

# 🎶 Music Playback with Speed Selection
@bot.on_message(filters.command("play"))
def play_music(client, message):
    url = message.text.split(maxsplit=1)[1]
    message.reply_text("⏳ Processing... Choose speed:", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("1.5x Speed", callback_data=f"speed:{url}:1.5"),
         InlineKeyboardButton("2.0x Speed", callback_data=f"speed:{url}:2.0"),
         InlineKeyboardButton("3.0x Speed", callback_data=f"speed:{url}:3.0")]
    ]))

@bot.on_callback_query(filters.regex(r"speed:(.+):(.+)"))
def speed_callback(client, callback_query):
    url, speed = callback_query.data.split(":")[1:]
    callback_query.message.edit_text(f"⏳ Processing at {speed}x speed... 🎵")
    input_song = download_audio(url)
    output_song = "fast_" + input_song
    change_speed(input_song, output_song, speed=float(speed))
    
    chat_id = callback_query.message.chat.id
    music_queue[chat_id] = music_queue.get(chat_id, []) + [output_song]  # Add to queue

    bot_voice.join_group_call(chat_id, Stream.audio(output_song))
    callback_query.message.reply_audio(output_song)
    os.remove(input_song)
    
# 📢 Broadcast Feature
@bot.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
def broadcast_message(client, message):
    text = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else "🚀 Broadcast Message!"
    for group_id in music_queue.keys():
        client.send_message(group_id, text)

# 🔄 Skip Music
@bot.on_message(filters.command("skip"))
def skip_music(client, message):
    chat_id = message.chat.id
    if chat_id in music_queue and len(music_queue[chat_id]) > 1:
        music_queue[chat_id].pop(0)  # Remove current song
        next_song = music_queue[chat_id][0]
        bot_voice.join_group_call(chat_id, Stream.audio(next_song))  # Play next song
        message.reply_audio(next_song)
    else:
        message.reply_text("🚫 No more songs in queue!")

# ⏹ Stop Music
@bot.on_message(filters.command("stop"))
def stop_music(client, message):
    chat_id = message.chat.id
    if chat_id in music_queue:
        bot_voice.leave_group_call(chat_id)  # Stop playback
        music_queue.pop(chat_id, None)  # Clear queue
        message.reply_text("⏹ Music stopped!")

# 🛠 Log Group Tracking
@bot.on_message(filters.text)
def log_message(client, message):
    log_text = f"User: {message.from_user.username}\nMessage: {message.text}"
    client.send_message(LOG_GROUP_ID, log_text)

bot.run()
