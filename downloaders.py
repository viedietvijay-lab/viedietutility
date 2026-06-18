# downloaders.py
import telebot
import os, re, time, shutil
import instaloader
import yt_dlp
from config import BOT_TOKEN, TOOL_COST
from database import Database
from points_manager import PointsManager
from buttons import back_button, main_menu, create_colored_keyboard

bot = telebot.TeleBot(BOT_TOKEN)
db = Database()
pm = PointsManager()

L = instaloader.Instaloader(save_metadata=False, download_comments=False, post_metadata_txt_pattern="")

def download_instagram(url):
    try:
        shortcode = re.search(r"instagram\.com/(?:reel|p|tv)/([a-zA-Z0-9_-]+)", url).group(1)
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        if not post.is_video:
            return None, "Not a video"
        temp_dir = f"insta_{shortcode}_{int(time.time())}"
        os.makedirs(temp_dir, exist_ok=True)
        L.download_post(post, target=temp_dir)
        for f in os.listdir(temp_dir):
            if f.endswith(".mp4"):
                return os.path.join(temp_dir, f), None
        return None, "No video file"
    except Exception as e:
        return None, str(e)[:100]

def download_youtube(url):
    try:
        timestamp = int(time.time())
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': f"yt_{timestamp}.%(ext)s",
            'quiet': True, 'no_warnings': True,
            'merge_output_format': 'mp4',
            'http_headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            fname = ydl.prepare_filename(info)
            if os.path.exists(fname):
                return fname, None
            for f in os.listdir('.'):
                if f.startswith(f"yt_{timestamp}") and f.endswith('.mp4'):
                    return f, None
        return None, "File not found"
    except Exception as e:
        return None, str(e)[:100]

@bot.callback_query_handler(func=lambda call: call.data == "menu:downloaders")
def downloaders_menu(call):
    buttons = [
        [("📸 Instagram", "dl_instagram", "primary")],
        [("▶️ YouTube", "dl_youtube", "danger")],
        [("◀️ Back", "menu:main", "primary")]
    ]
    bot.edit_message_text("📥 <b>Downloaders</b>\n\nSelect platform:",
                          chat_id=call.message.chat.id, message_id=call.message.message_id,
                          reply_markup=create_colored_keyboard(buttons))
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("dl_"))
def download_platform(call):
    user_id = call.from_user.id
    platform = call.data  # "dl_instagram" or "dl_youtube"
    if not pm.can_use_tool(user_id):
        bot.answer_callback_query(call.id, f"❌ Need {TOOL_COST} point!", show_alert=True)
        return
    pending_download[user_id] = platform
    bot.edit_message_text(f"📱 Send the URL to download:",
                          chat_id=call.message.chat.id, message_id=call.message.message_id,
                          reply_markup=back_button())
    bot.answer_callback_query(call.id)

pending_download = {}

@bot.message_handler(func=lambda m: m.text and m.text.startswith(("http://", "https://")) and m.from_user.id in pending_download)
def handle_download_url(message):
    user_id = message.from_user.id
    platform = pending_download.pop(user_id, None)
    if not platform:
        return
    if not pm.can_use_tool(user_id):
        bot.send_message(user_id, f"❌ Need {TOOL_COST} point!", reply_markup=main_menu())
        return
    url = message.text
    processing = bot.send_message(user_id, "⏳ Downloading...")
    if platform == "dl_instagram":
        fpath, err = download_instagram(url)
    else:
        fpath, err = download_youtube(url)
    if fpath and os.path.exists(fpath):
        pm.use_tool(user_id)
        size = os.path.getsize(fpath)/(1024*1024)
        with open(fpath, 'rb') as vid:
            bot.send_video(user_id, vid, caption=f"✅ Download complete!\n📦 Size: {size:.1f} MB")
        try: os.remove(fpath)
        except: pass
        shutil.rmtree(os.path.dirname(fpath), ignore_errors=True)
        bot.delete_message(user_id, processing.message_id)
    else:
        bot.edit_message_text(f"❌ Failed: {err}", chat_id=user_id, message_id=processing.message_id)