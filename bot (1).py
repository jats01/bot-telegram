import os, subprocess, asyncio, uuid, time, sys
from telethon import TelegramClient, events
from telethon.tl.types import DocumentAttributeVideo
import nest_asyncio

# ================= CONFIGURACIÓN =================
API_ID = 27104013
API_HASH = "3a5002f911548e3de97af1e652f8a7be"
BOT_TOKEN = "8084845589:AAGSukadge6JtNTJy65VWStVptHf6G9Agxg"

SESSION_DIR = "/content/drive/MyDrive/telegram_session/"
os.makedirs(SESSION_DIR, exist_ok=True)
MARK_FILE = os.path.join(SESSION_DIR, "watermark.txt")
BOT_SESSION = os.path.join(SESSION_DIR, "bot_turbo_v7") 
WORK_DIR = "/content/work_dir"
os.makedirs(WORK_DIR, exist_ok=True)

def get_mark():
    if os.path.exists(MARK_FILE):
        with open(MARK_FILE, "r") as f: return f.read().strip()
    return "@sarplay3"

# ================= MONITOREO DE CONSOLA =================
def progress_bar(current, total, status="Descargando"):
    percentage = (current / total) * 100
    sys.stdout.write(f'\r{status}: [{"#" * int(percentage//5)}{"." * (20 - int(percentage//5))}] {percentage:.2f}%')
    sys.stdout.flush()

# ================= MANEJADORES =================
client = TelegramClient(BOT_SESSION, API_ID, API_HASH, connection_retries=15)

@client.on(events.NewMessage(pattern="/start"))
async def start_handler(event):
    current_m = get_mark()
    welcome = (
        "✨ **¡BIENVENIDO AL BOT TURBO V10!** ✨\n\n"
        "🎬 **¿Qué puedo hacer?**\n"
        "Pongo tu marca de agua a cualquier video manteniendo la calidad y el peso optimizado para Telegram.\n\n"
        "⚙️ **Configuración Actual:**\n"
        f"└ 🏷️ Marca: `{current_m}`\n"
        f"└ 🌫️ Opacidad: `23%` (Sutil)\n\n"
        "🛠️ **Comandos Útiles:**\n"
        "• `/setmark NOMBRE` - Cambia tu marca de agua.\n"
        "  _Ejemplo: /setmark @MiCanalVIP_\n\n"
        "--- \n"
        "📥 **¡Envíame un video para empezar!**"
    )
    await event.respond(welcome)

@client.on(events.NewMessage(pattern="/setmark"))
async def setmark(event):
    new_m = event.text.replace("/setmark", "").strip()
    if new_m:
        with open(MARK_FILE, "w") as f: f.write(new_m)
        await event.respond(f"✅ **Marca de agua actualizada:** `{new_m}`")
    else:
        await event.respond("❌ Indica un nombre. Ejemplo: `/setmark @sarplay3`")

@client.on(events.NewMessage)
async def video_handler(event):
    if not event.video or (event.text and event.text.startswith('/')): return
    
    start_time = time.time()
    current_mark = get_mark()
    uid = str(uuid.uuid4())[:8]
    in_p = os.path.join(WORK_DIR, f"in_{uid}.mp4")
    out_p = os.path.join(WORK_DIR, f"out_{uid}.mp4")
    thumb_p = os.path.join(WORK_DIR, f"thumb_{uid}.jpg")
    
    status = await event.respond("⏳ **Analizando video... revisa la consola de Colab.**")

    try:
        # 1. DESCARGA CON MONITOR
        print(f"\n\n[1/3] RECIBIENDO VIDEO: {uid}")
        await status.edit("⬇️ **Descargando...**")
        await event.download_media(file=in_p, progress_callback=lambda c, t: progress_bar(c, t, "📥 Descargando"))
        print("\n✅ Descarga completada.")

        # Obtener metadata para el reproductor
        probe = f'ffprobe -v error -select_streams v:0 -show_entries stream=width,height,duration -of default=noprint_wrappers=1:nokey=1 "{in_p}"'
        info = subprocess.check_output(probe, shell=True).decode().split()
        orig_w, orig_h, orig_dur = int(info[0]), int(info[1]), int(float(info[2]))

        # 2. PROCESO FFmpeg
        await status.edit(f"⚙️ **Editando {orig_dur}s... (CRF 28)**")
        print(f"[2/3] Procesando marca: {current_mark}")
        
        cmd = [
            "ffmpeg", "-y", "-i", in_p,
            "-vf", f"drawtext=text='{current_mark}':fontcolor=white@0.23:fontsize=h/25:x=w-tw-15:y=15",
            "-c:v", "libx264", "-preset", "superfast", "-crf", "28",
            "-c:a", "copy", "-pix_fmt", "yuv420p", "-threads", "0", "-movflags", "+faststart", out_p
        ]
        
        process = await asyncio.create_subprocess_exec(*cmd, stdout=sys.stdout, stderr=sys.stderr)
        await process.wait()
        print("\n✅ Edición finalizada.")

        # 3. SUBIDA
        await status.edit("📤 **Subiendo a Telegram...**")
        print("[3/3] Enviando archivo final...")
        
        subprocess.run(f'ffmpeg -y -i "{out_p}" -ss 00:00:02 -vframes 1 "{thumb_p}"', shell=True, capture_output=True)

        await client.send_file(
            event.chat_id, out_p, caption=event.message.text,
            thumb=thumb_p, supports_streaming=True,
            attributes=[DocumentAttributeVideo(duration=orig_dur, w=orig_w, h=orig_h, supports_streaming=True)]
        )
        
        total_time = int(time.time() - start_time)
        final_size = round(os.path.getsize(out_p) / (1024 * 1024), 2)
        print(f"✨ PROCESO COMPLETADO: {final_size}MB en {total_time}s")
        await status.edit(f"✅ **¡Listo!**\n⏱️ Tiempo: `{total_time}s` | 📦 Peso: `{final_size}MB`")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        await status.edit(f"❌ Error: {e}")
    finally:
        for f in [in_p, out_p, thumb_p]:
            if os.path.exists(f): os.remove(f)

# ================= ARRANQUE =================
nest_asyncio.apply()
async def run():
    await client.start(bot_token=BOT_TOKEN)
    print("🚀 BOT CONECTADO - ESPERANDO VIDEOS...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(run())