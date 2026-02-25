import logging
import asyncio
import time
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ================= CONFIG =================

TOKEN = "TU_TOKEN_AQUI"
EXPIRACION = 300  # 5 minutos

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# Guardado temporal por usuario
sesiones = {}


# ================= FUNCIONES =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔍 Envíame varios enlaces de Telegram separados por espacio o salto de línea.\n"
        "Los procesaré todos juntos."
    )


async def procesar_enlaces(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    texto = update.message.text

    # Extraer enlaces
    links = []
    for linea in texto.split():
        if "t.me/" in linea:
            links.append(linea.strip())

    if not links:
        await update.message.reply_text("❌ No se detectaron enlaces.")
        return

    # Quitar duplicados
    links = list(set(links))

    mensaje_procesando = await update.message.reply_text(
        f"⏳ Procesando {len(links)} enlaces..."
    )

    validos = []
    invalidos = []

    # Simulación de validación
    for link in links:
        await asyncio.sleep(1)

        # Aquí va tu lógica real de validación
        if "invalid" in link:
            invalidos.append(link)
        else:
            validos.append(link)

    # Guardar sesión
    sesiones[user_id] = {
        "validos": validos,
        "invalidos": invalidos,
        "timestamp": time.time(),
    }

    teclado = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🔵 Válidos ({len(validos)})", callback_data="ver_validos")],
        [InlineKeyboardButton(f"🔴 No válidos ({len(invalidos)})", callback_data="ver_invalidos")],
    ])

    await mensaje_procesando.edit_text(
        "📊 Resultado listo.\nSelecciona una opción:",
        reply_markup=teclado,
    )


async def botones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if user_id not
