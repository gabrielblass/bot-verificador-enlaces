import os
import telebot
import logging
from flask import Flask
from threading import Thread

# ---------------- CONFIGURACIÓN DE LOGS ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ---------------- TOKEN ----------------
TOKEN = os.environ.get("BOT_TOKEN")

if not TOKEN:
    logging.error("BOT_TOKEN no está configurado")
    raise RuntimeError("BOT_TOKEN no configurado")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
app = Flask(__name__)

# ---------------- FLASK KEEP-ALIVE ----------------
@app.route("/")
def home():
    return "Bot activo correctamente 🚀", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    logging.info(f"Iniciando servidor Flask en puerto {port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# ---------------- COMANDOS DEL BOT ----------------
@bot.message_handler(commands=["start"])
def start_message(message):
    logging.info(f"/start usado por {message.from_user.id}")
    bot.reply_to(
        message,
        "¡Bienvenido al <b>Verificador de Enlaces</b> 🔗\n\n"
        "Envíame los links que deseas revisar."
    )

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    logging.info(f"Mensaje recibido de {message.from_user.id}")
    bot.reply_to(
        message,
        "Recibí tu mensaje 📩\n"
        "Estoy preparándome para procesar los enlaces..."
    )

# ---------------- INICIO PRINCIPAL ----------------
def main():
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    logging.info("Bot iniciado correctamente")

    # Reconexión automática si hay error
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=30)
        except Exception as e:
            logging.error(f"Error en polling: {e}")

if __name__ == "__main__":
    main()
