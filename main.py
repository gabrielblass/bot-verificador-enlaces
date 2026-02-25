import os
import telebot
import re
import logging
import time
from flask import Flask
from threading import Thread
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================= CONFIG =================

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN no configurado")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

user_results = {}
MAX_LINKS = 50
EXPIRATION_TIME = 300  # 5 minutos

# ================= SERVIDOR =================

@app.route("/")
def home():
    return "Bot PRO Activo 🚀", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# ================= UTILIDADES =================

def extract_username(url):
    match = re.search(r"t\.me/([a-zA-Z0-9_]+)", url)
    if match:
        username = match.group(1)

        # Ignorar enlaces tipo + (invitaciones privadas)
        if username.startswith("+"):
            return None

        if "share" in username.lower():
            return None

        return username
    return None


def check_chat(username):
    try:
        chat = bot.get_chat(f"@{username}")

        if chat.type == "private":
            return None

        name = chat.title if chat.title else username

        return {
            "name": name,
            "link": f"https://t.me/{username}"
        }

    except:
        return None

def clean_expired_sessions():
    current_time = time.time()
    expired_users = []

    for user_id, data in user_results.items():
        if current_time - data["timestamp"] > EXPIRATION_TIME:
            expired_users.append(user_id)

    for user_id in expired_users:
        del user_results[user_id]

# ================= START =================

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(
        message,
        "🔎 Envíame enlaces de Telegram.\n"
        "Los validaré todos juntos."
    )

# ================= PROCESAMIENTO PRINCIPAL =================

@bot.message_handler(func=lambda message: True)
def handle_links(message):

    clean_expired_sessions()

    urls = re.findall(r'https?://t\.me/[^\s]+', message.text)
    urls = list(set(urls))  # eliminar duplicados

    if not urls:
        bot.reply_to(message, "No encontré enlaces válidos.")
        return

    if len(urls) > MAX_LINKS:
        bot.reply_to(message, f"⚠️ Máximo {MAX_LINKS} enlaces.")
        return

    msg = bot.reply_to(message, "🔍 Analizando enlaces...")

    validos = []
    invalidos = []

    for url in urls:
        username = extract_username(url)
        if not username:
            invalidos.append(url)
            continue

        data = check_chat(username)

        if data:
            validos.append(data)
        else:
            invalidos.append(url)

    # Guardar sesión con timestamp
    user_results[message.from_user.id] = {
        "validos": validos,
        "invalidos": invalidos,
        "timestamp": time.time()
    }

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(f"🔵 Válidos ({len(validos)})", callback_data="ver_validos")
    )
    markup.add(
        InlineKeyboardButton(f"🔴 No válidos ({len(invalidos)})", callback_data="ver_invalidos")
    )

    bot.edit_message_text(
        "📊 Resultado listo.\nSelecciona una opción:",
        message.chat.id,
        msg.message_id,
        reply_markup=markup
    )

# ================= BOTONES =================

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):

    clean_expired_sessions()

    user_id = call.from_user.id
    data = user_results.get(user_id)

    if not data:
        bot.answer_callback_query(call.id, "⏳ Resultados expirados (5 min).")
        return

    if call.data == "ver_validos":

        if not data["validos"]:
            bot.answer_callback_query(call.id, "No hay válidos.")
            return

        markup = InlineKeyboardMarkup()

        for grupo in data["validos"]:
            markup.add(
                InlineKeyboardButton(
                    grupo["name"],
                    url=grupo["link"]
                )
            )

        bot.send_message(
            call.message.chat.id,
            "🔵 Enlaces válidos:",
            reply_markup=markup
        )

    elif call.data == "ver_invalidos":

        if not data["invalidos"]:
            bot.answer_callback_query(call.id, "No hay inválidos.")
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
            logging.error(f"Error polling: {e}")

if __name__ == "__main__":
    main()
