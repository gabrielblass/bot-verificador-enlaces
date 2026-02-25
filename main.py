import os
import telebot
import re
import logging
from flask import Flask
from threading import Thread

# ---------------- CONFIG ----------------
logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN no configurado")

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")
app = Flask(__name__)

MAX_LINKS = 30

# ---------------- SERVIDOR ----------------
@app.route("/")
def home():
    return "Verificador PRO 🚀", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# ---------------- EXTRAER USERNAME ----------------
def extract_username(url):
    match = re.search(r"t\.me/([a-zA-Z0-9_]+)", url)
    if match:
        username = match.group(1)

        # Ignorar enlaces tipo share o joinchat
        if "share" in username.lower():
            return None
        return username
    return None

# ---------------- VALIDAR LINK CON API ----------------
def check_telegram_chat(username):
    try:
        chat = bot.get_chat(f"@{username}")
        members = bot.get_chat_member_count(chat.id)

        name = chat.title if chat.title else username

        return f"✅ ACTIVO\n📛 {name}\n👥 {members} miembros"

    except Exception as e:
        logging.error(f"Error con {username}: {e}")
        return "❌ CAÍDO / PRIVADO"

# ---------------- START ----------------
@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(
        message,
        "Envíame enlaces públicos de Telegram.\n"
        "Te mostraré nombre y número de miembros."
    )

# ---------------- PROCESAMIENTO ----------------
@bot.message_handler(func=lambda message: True)
def handle_links(message):
    urls = re.findall(r'https?://t\.me/[^\s]+', message.text)

    if not urls:
        bot.reply_to(message, "No encontré enlaces válidos.")
        return

    # Eliminar duplicados
    urls = list(set(urls))

    if len(urls) > MAX_LINKS:
        bot.reply_to(message, f"Máximo {MAX_LINKS} enlaces.")
        return

    msg_wait = bot.reply_to(message, f"🔍 Revisando {len(urls)} enlaces...")

    resultados = []

    for url in urls:
        username = extract_username(url)

        if not username:
            continue  # ignora links share o inválidos

        estado = check_telegram_chat(username)
        resultados.append(f"{estado}\n🔗 https://t.me/{username}")

    if not resultados:
        bot.edit_message_text(
            "No encontré enlaces válidos para revisar.",
            message.chat.id,
            msg_wait.message_id
        )
        return

    reporte = "*📊 RESULTADO:*\n\n" + "\n\n".join(resultados)

    try:
        bot.edit_message_text(
            reporte,
            message.chat.id,
            msg_wait.message_id,
            disable_web_page_preview=True
        )
    except:
        bot.send_message(
            message.chat.id,
            reporte,
            disable_web_page_preview=True
        )

# ---------------- MAIN ----------------
def main():
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    logging.info("Bot iniciado")

    while True:
        try:
            bot.infinity_polling(skip_pending=True)
        except Exception as e:
            logging.error(f"Error polling: {e}")

if __name__ == "__main__":
    main()
