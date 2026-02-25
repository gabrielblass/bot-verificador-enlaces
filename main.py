import os
import telebot
import re
import logging
from flask import Flask
from threading import Thread
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================= CONFIGURACIÓN =================

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN no configurado")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Memoria temporal por usuario
user_results = {}

MAX_LINKS = 50  # límite de seguridad

# ================= SERVIDOR FLASK =================

@app.route("/")
def home():
    return "Bot Verificador PRO activo 🚀", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# ================= UTILIDADES =================

def extract_username(url):
    """
    Extrae el username de un enlace t.me
    Ignora enlaces tipo share o inválidos
    """
    match = re.search(r"t\.me/([a-zA-Z0-9_]+)", url)
    if match:
        username = match.group(1)

        if "share" in username.lower():
            return None

        return username
    return None


def check_chat(username):
    """
    Verifica si el chat existe.
    Si es público obtiene nombre real.
    Si es privado muestra username.
    Si no existe devuelve None.
    """
    try:
        chat = bot.get_chat(f"@{username}")

        # Si es chat privado de usuario o bot, lo ignoramos
        if chat.type == "private":
            return None

        name = chat.title if chat.title else username

        return {
            "name": name,
            "link": f"https://t.me/{username}",
            "private": False
        }

    except Exception:
        # Puede ser privado o inaccesible
        return {
            "name": username,
            "link": f"https://t.me/{username}",
            "private": True
        }

# ================= COMANDO START =================

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(
        message,
        "🔎 Envíame enlaces de Telegram.\n"
        "Los organizaré automáticamente en válidos e inválidos."
    )

# ================= PROCESAR MENSAJES =================

@bot.message_handler(func=lambda message: True)
def handle_links(message):

    urls = re.findall(r'https?://t\.me/[^\s]+', message.text)
    urls = list(set(urls))  # eliminar duplicados

    if not urls:
        bot.reply_to(message, "No encontré enlaces válidos.")
        return

    if len(urls) > MAX_LINKS:
        bot.reply_to(message, f"⚠️ Máximo permitido: {MAX_LINKS} enlaces.")
        return

    validos = []
    invalidos = []

    for url in urls:
        username = extract_username(url)
        if not username:
            continue

        data = check_chat(username)

        if data:
            validos.append(data)
        else:
            invalidos.append(url)

    # Guardamos resultados por usuario
    user_results[message.from_user.id] = {
        "validos": validos,
        "invalidos": invalidos
    }

    # Creamos botones principales
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(f"🔵 Válidos ({len(validos)})", callback_data="ver_validos")
    )
    markup.add(
        InlineKeyboardButton(f"🔴 No válidos ({len(invalidos)})", callback_data="ver_invalidos")
    )

    bot.reply_to(
        message,
        "📊 Revisión completada.\nSelecciona una opción:",
        reply_markup=markup
    )

# ================= MANEJO DE BOTONES =================

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):

    user_id = call.from_user.id
    data = user_results.get(user_id)

    if not data:
        bot.answer_callback_query(call.id, "Sesión expirada.")
        return

    # 🔵 MOSTRAR VÁLIDOS
    if call.data == "ver_validos":

        if not data["validos"]:
            bot.send_message(call.message.chat.id, "No hay enlaces válidos.")
            bot.answer_callback_query(call.id)
            return

        markup = InlineKeyboardMarkup()

        for grupo in data["validos"]:
            nombre = grupo["name"]

            if grupo["private"]:
                nombre = f"🔒 {nombre}"

            markup.add(
                InlineKeyboardButton(
                    nombre,
                    url=grupo["link"]
                )
            )

        bot.send_message(
            call.message.chat.id,
            "🔵 Enlaces disponibles:",
            reply_markup=markup
        )

    # 🔴 MOSTRAR INVÁLIDOS
    elif call.data == "ver_invalidos":

        if not data["invalidos"]:
            bot.send_message(call.message.chat.id, "No hay enlaces inválidos.")
            bot.answer_callback_query(call.id)
            return

        texto = "🔴 Enlaces no válidos:\n\n" + "\n".join(data["invalidos"])

        bot.send_message(call.message.chat.id, texto)

    bot.answer_callback_query(call.id)

# ================= MAIN =================

def main():
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    logging.info("Bot iniciado correctamente")

    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=60)
        except Exception as e:
            logging.error(f"Error en polling: {e}")

if __name__ == "__main__":
    main()
