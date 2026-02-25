import telebot
from flask import Flask
from threading import Thread
import os

# Configuración del bot
TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot de Enlaces Online"

def run_server():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "¡Bienvenido al Verificador de Enlaces! Envíame los links que quieres revisar.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # Aquí es donde programaremos la lógica para verificar si el link sirve
    bot.reply_to(message, "Recibí tu lista. Estoy preparándome para validarlos...")

if __name__ == "__main__":
    Thread(target=run_server).start()
    bot.infinity_polling()
000))
    app_web.run(host="0.0.0.0", port=port)

# =========================
# CONFIGURACIÓN
# =========================
TOKEN_BOT = "8118811284:AAGfPxDdtjfHe0_c5S6vv-VGIZjgN-aoAj0"
ID_GRUPO_PRINCIPAL = -1003190310538
USUARIOS_AUTORIZADOS = [8290078424, 1243433271]
ARCHIVO_DB = "enviados.txt"

TEMAS = {
    "Casting Argentina": 2,
    "Deditos": 14,
    "Exclusivos": 16,
    "Nacho Fierro": 17,
    "Solo Fotitos": 18,
    "Only": 19,
    "Chiboli": 20,
    "Milenaxx": 21,
    "MilkyPe": 22,
    "Tetaspando": 23,
    "SexMEx": 24,
    "Mamadas": 25,
    "Omegle": 27,
    "Videos Largos": 57,
    "OGringas": 519,
    "Colegios": 892,
    "Camara": 893,
    "Dormida": 894,
    "Espiadas": 895,
    "Grabadas": 897,
    "Tiktoker": 898,
    "Americas": 899,
    "Casero": 900,
    "Montando": 1146,
    "Gras en la Calle": 1205,
    "Borrachas": 1225,
    "SOPHIERIIN": 901,
    "Latinaspy": 2970,
    "Cazaputas": 2989,
    "Asiaticas": 2978,
    "Juegos": 2980,
    "Cosplay": 2981,
    "Gianluca": 2987,
    "Pornhub": 2979,
    "Agregar 1": 9282,
    "Agregar 2": 2983,
    "Agregar 3": 2984,
    "Agregar 4": 2985,
    "Agregar 5": 2986,
}

cola_archivos = {}

# =========================
# CONTROL DE ENVIADOS
# =========================
def ya_fue_enviado(file_id):
    if not os.path.exists(ARCHIVO_DB):
        return False
    with open(ARCHIVO_DB, "r") as f:
        enviados = f.read().splitlines()
    return file_id in enviados

def guardar_enviado(file_id):
    with open(ARCHIVO_DB, "a") as f:
        f.write(f"{file_id}\n")

# =========================
# PROCESAR COLA
# =========================
async def procesar_cola(chat_id, context: ContextTypes.DEFAULT_TYPE):
    await asyncio.sleep(5)

    if chat_id not in cola_archivos:
        return

    archivos = cola_archivos[chat_id]["archivos"]
    if not archivos:
        return

    cantidad = len(archivos)

    teclado = [
        [InlineKeyboardButton(f"📦 Enviar {cantidad} JUNTOS", callback_data="batch_junto")],
        [InlineKeyboardButton(f"📑 Enviar {cantidad} SEPARADOS", callback_data="batch_separado")]
    ]

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"Recibidos {cantidad} archivos. ¿Cómo los envío?",
        reply_markup=InlineKeyboardMarkup(teclado),
    )

# =========================
# RECIBIR ARCHIVOS
# =========================
async def recibir_archivo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in USUARIOS_AUTORIZADOS:
        return

    chat_id = update.effective_chat.id
    msg = update.message

    file_id = None
    tipo = None

    if msg.photo:
        file_id = msg.photo[-1].file_id
        tipo = "photo"
    elif msg.video:
        file_id = msg.video.file_id
        tipo = "video"

    if not file_id:
        return

    if chat_id not in cola_archivos:
        cola_archivos[chat_id] = {"archivos": [], "tarea": None}

    cola_archivos[chat_id]["archivos"].append({
        "id": file_id,
        "type": tipo
    })

    if cola_archivos[chat_id]["tarea"]:
        cola_archivos[chat_id]["tarea"].cancel()

    cola_archivos[chat_id]["tarea"] = asyncio.create_task(
        procesar_cola(chat_id, context)
    )

# =========================
# CALLBACKS
# =========================
async def manejar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = update.effective_chat.id
    data = query.data

    if data.startswith("batch_"):
        context.user_data["modo"] = data
        nombres = list(TEMAS.keys())
        teclado = []

        for i in range(0, len(nombres), 2):
            fila = [InlineKeyboardButton(nombres[i], callback_data=f"t_{nombres[i]}")]
            if i + 1 < len(nombres):
                fila.append(
                    InlineKeyboardButton(nombres[i+1], callback_data=f"t_{nombres[i+1]}")
                )
            teclado.append(fila)

        await query.edit_message_text(
            "🎯 Elige el tema destino:",
            reply_markup=InlineKeyboardMarkup(teclado),
        )

    elif data.startswith("t_"):
        tema = data.replace("t_", "")
        thread_id = TEMAS.get(tema)

        archivos = cola_archivos.get(chat_id, {}).get("archivos", [])
        modo = context.user_data.get("modo", "")

        await query.edit_message_text(f"🚀 Enviando a {tema}...")

        enviados = 0
        omitidos = 0

        nuevos = []
        for a in archivos:
            if ya_fue_enviado(a["id"]):
                omitidos += 1
            else:
                nuevos.append(a)

        if not nuevos:
            await context.bot.send_message(
                chat_id=chat_id,
                text="⚠️ Todos los archivos ya fueron enviados anteriormente."
            )
            cola_archivos[chat_id] = {"archivos": [], "tarea": None}
            return

        try:
            # ENVÍO JUNTOS (máx 10)
            if "junto" in modo and len(nuevos) > 1:
                media = []

                for a in nuevos[:10]:
                    if a["type"] == "photo":
                        media.append(InputMediaPhoto(media=a["id"]))
                    else:
                        media.append(InputMediaVideo(media=a["id"]))

                await context.bot.send_media_group(
                    chat_id=ID_GRUPO_PRINCIPAL,
                    media=media,
                    message_thread_id=thread_id,
                )

                for a in nuevos[:10]:
                    guardar_enviado(a["id"])
                    enviados += 1

            # ENVÍO SEPARADO
            else:
                for a in nuevos:
                    if a["type"] == "photo":
                        await context.bot.send_photo(
                            chat_id=ID_GRUPO_PRINCIPAL,
                            photo=a["id"],
                            message_thread_id=thread_id,
                        )
                    else:
                        await context.bot.send_video(
                            chat_id=ID_GRUPO_PRINCIPAL,
                            video=a["id"],
                            message_thread_id=thread_id,
                        )

                    guardar_enviado(a["id"])
                    enviados += 1
                    await asyncio.sleep(0.3)

        except Exception as e:
            logger.error(f"Error enviando archivos: {e}")

        mensaje = f"✅ Enviados: {enviados}"
        if omitidos > 0:
            mensaje += f"\n⚠️ Omitidos (ya enviados): {omitidos}"

        await context.bot.send_message(chat_id=chat_id, text=mensaje)

        cola_archivos[chat_id] = {"archivos": [], "tarea": None}

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    Thread(target=run_web).start()

    app = ApplicationBuilder().token(TOKEN_BOT).build()
    app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO, recibir_archivo))
    app.add_handler(CallbackQueryHandler(manejar_callback))

    logger.info("Bot iniciado correctamente 🚀")
    app.run_polling()
# =========================

if __name__ == "__main__":

    Thread(target=run_web).start()



    app = ApplicationBuilder().token(TOKEN_BOT).build()



    app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO, recibir_archivo))

    app.add_handler(CallbackQueryHandler(manejar_callback))



    logger.info("Bot iniciado correctamente 🚀")

    app.run_polling()