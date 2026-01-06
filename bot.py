import os
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

DOWNLOADS_DIR = "downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not url.startswith("http"):
        await update.message.reply_text("Por favor envíame un enlace válido 😅")
        return

    await update.message.reply_text("Descargando... ⏳ Esto puede tardar según el tamaño de la playlist.")

    # Hook que se llama cada vez que un video termina de descargarse
    async def progress_hook(d):
        if d['status'] == 'finished':
            filename = d['filename']
            title = d.get('title', 'Video')

            await update.message.reply_text(f"Subiendo a Telegram: {title} 📤")

            # Subir video
            with open(filename, 'rb') as f:
                await update.message.reply_video(video=f, caption=title)

            # Borrar archivo
            os.remove(filename)

    # yt-dlp no soporta async hooks directamente, hacemos workaround con wrapper
    def sync_hook(d):
        import asyncio
        asyncio.create_task(progress_hook(d))

    ydl_opts = {
        "outtmpl": os.path.join(DOWNLOADS_DIR, "%(title)s.%(ext)s"),
        "format": "mp4/bestaudio/best",
        "quiet": True,
        "progress_hooks": [sync_hook],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])  # descarga toda la playlist
        await update.message.reply_text("¡Todos los videos procesados! ✅")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Envíame un enlace de YouTube o playlist y lo descargaré y subiré a Telegram."
    )

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.COMMAND, start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Bot corriendo...")
    app.run_polling()

if __name__ == "__main__":
    main()
