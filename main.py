import os
import asyncio
import logging
from pathlib import Path
from yt_dlp import YoutubeDL
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Берём токен из переменной окружения (Render Environment Variable)
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан. На Render добавь переменную окружения BOT_TOKEN с токеном бота.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VIDEO_DIR = Path("downloads")
VIDEO_DIR.mkdir(exist_ok=True)

ydl_opts = {
    'outtmpl': str(VIDEO_DIR / '%(id)s.%(ext)s'),
    'format': 'mp4',
    'quiet': True,
    'no_warnings': True
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Пришли мне ссылку на Instagram Reels или TikTok — я скачаю видео для тебя."
    )

async def download_video(url: str) -> str | None:
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        return filename
    except Exception as e:
        logger.error(f"Ошибка при скачивании: {e}")
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url:
        return
    if "instagram.com" not in url and "tiktok.com" not in url:
        await update.message.reply_text("Пришли ссылку с instagram.com или tiktok.com 👍")
        return

    notice = await update.message.reply_text("⏳ Скачиваю видео...")
    filepath = await asyncio.to_thread(download_video, url)
    if filepath and os.path.exists(filepath):
        with open(filepath, 'rb') as video:
            await update.message.reply_video(video)
        os.remove(filepath)
        await notice.edit_text("✅ Готово!")
    else:
        await notice.edit_text("❌ Не удалось скачать видео. Проверь ссылку.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Бот запущен и готов к работе!")
    app.run_polling()

if __name__ == "__main__":
    main()
