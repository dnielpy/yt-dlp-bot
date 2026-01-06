import os
import yt_dlp
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Cargar token de .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Carpeta de descargas
DOWNLOADS_DIR = "downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# Variables globales para el estado de descarga
download_message = None
update_obj = None

# Variables globales para el estado de descarga
download_message = None
update_obj = None

def progress_hook(d):
    """Hook para actualizar el progreso de la descarga"""
    asyncio.create_task(update_progress(d))

async def update_progress(d):
    """Actualiza el mensaje de progreso en Telegram"""
    global download_message, update_obj
    
    if d['status'] == 'downloading':
        total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
        downloaded = d.get('downloaded_bytes', 0)
        
        if total > 0:
            percentage = (downloaded / total) * 100
            speed = d.get('speed', 0)
            
            # Convertir velocidad a formato legible
            if speed:
                if speed > 1024*1024:
                    speed_str = f"{speed / (1024*1024):.2f} MB/s"
                elif speed > 1024:
                    speed_str = f"{speed / 1024:.2f} KB/s"
                else:
                    speed_str = f"{speed:.2f} B/s"
            else:
                speed_str = "Calculando..."
            
            # Crear barra de progreso
            bar_length = 20
            filled = int(bar_length * percentage / 100)
            bar = '█' * filled + '░' * (bar_length - filled)
            
            progress_text = (
                f"📥 Descargando...\n\n"
                f"[{bar}] {percentage:.1f}%\n"
                f"🚀 Velocidad: {speed_str}"
            )
            
            try:
                if download_message is None and update_obj:
                    # Enviar primer mensaje
                    download_message = await update_obj.message.reply_text(progress_text)
                elif download_message:
                    # Editar mensaje existente
                    await download_message.edit_text(progress_text)
            except Exception as e:
                print(f"Error actualizando progreso: {e}")
    
    elif d['status'] == 'finished':
        try:
            if download_message:
                await download_message.edit_text("✅ Descarga completada")
        except Exception as e:
            print(f"Error finalizando mensaje: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global download_message, update_obj
    
    download_message = None
    update_obj = update
    
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
        "progress_hooks": [progress_hook],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extraer info sin descargar
            info = ydl.extract_info(url, download=False)

            # Obtener lista de videos (playlist o single video)
            videos = info.get("entries", [info])

            await update.message.reply_text(f"Encontré {len(videos)} video(s). Empezando descarga...")

            for i, video in enumerate(videos, start=1):
                download_message = None  # Reset para cada video
                
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
