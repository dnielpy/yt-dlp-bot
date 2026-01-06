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

    # validar que sea un link
    if not url.startswith("http"):
        await update.message.reply_text("Por favor envíame un enlace válido 😅")
        return

    await update.message.reply_text("Descargando el video... ⏳")

    # ruta de salida
    output_path = os.path.join(DOWNLOADS_DIR, "%(title)s.%(ext)s")

    ydl_opts = {
        "outtmpl": output_path,
        "format": "mp4/bestaudio/best",
        "quiet": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        await update.message.reply_text("Subiendo el archivo a Telegram... 📤")

        await update.message.reply_video(video=open(filename, "rb"), caption=info.get("title", "Video"))

        os.remove(filename)

    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Bot corriendo...")
    app.run_polling()

if __name__ == "__main__":
    main()
