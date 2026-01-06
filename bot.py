import os
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Cargar token de .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Carpeta de descargas
DOWNLOADS_DIR = "downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not url.startswith("http"):
        await update.message.reply_text("Por favor envíame un enlace válido 😅")
        return

    await update.message.reply_text("Procesando enlace... ⏳")

    # Configuración de yt-dlp
    ydl_opts = {
        "outtmpl": os.path.join(DOWNLOADS_DIR, "%(title)s.%(ext)s"),
        "format": "mp4/bestaudio/best",
        "quiet": True,
        "noplaylist": False,  # queremos que detecte playlists
        "max_filesize": 1500*1024*1024,  # 1.5 GB max
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extraer info sin descargar
            info = ydl.extract_info(url, download=False)

            # Obtener lista de videos (playlist o single video)
            videos = info.get("entries", [info])

            await update.message.reply_text(f"Encontré {len(videos)} video(s). Empezando descarga...")

            for i, video in enumerate(videos, start=1):
                title = video.get("title", "Video")
                video_url = video.get("webpage_url")

                await update.message.reply_text(f"Descargando video {i}/{len(videos)}: {title} ⏳")

                # Descargar solo este video
                ydl.download([video_url])
                filename = ydl.prepare_filename(video)

                await update.message.reply_text(f"Subiendo a Telegram: {title} 📤")

                # Subir video
                with open(filename, "rb") as f:
                    await update.message.reply_video(video=f, caption=title)

                # Borrar archivo para liberar espacio
                os.remove(filename)

            await update.message.reply_text("✅ Todos los videos procesados y subidos.")

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
