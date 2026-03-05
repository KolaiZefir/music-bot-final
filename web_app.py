import logging
import os
import sys
import traceback
import asyncio
from flask import Flask, request, jsonify
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
import config

# --- 1. МАКСИМАЛЬНОЕ ЛОГИРОВАНИЕ ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# --- 2. Создаём веб-сервер Flask ---
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# --- 3. ГЛОБАЛЬНЫЙ ЦИКЛ СОБЫТИЙ (исправляет ошибку с закрытием) ---
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# --- 4. Создаём и инициализируем бота ---
bot = Bot(token=config.BOT_TOKEN)
loop.run_until_complete(bot.initialize())

# --- 5. Создаём и инициализируем обработчик команд ---
telegram_app = Application.builder().token(config.BOT_TOKEN).build()
loop.run_until_complete(telegram_app.initialize())

# --- 6. Команда /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет кнопку с ссылкой на Mini App"""
    try:
        user = update.effective_user
        logger.info(f"🔥 Команда /start от пользователя {user.id} ({user.first_name})")

        mini_app_url = f"{config.FRONTEND_URL}?user_id={user.id}"

        await update.message.reply_text(
            f"🎵 Привет, {user.first_name}!\n\n"
            f"Нажми кнопку ниже, чтобы открыть музыкальный плеер:",
            reply_markup={
                "inline_keyboard": [[
                    {"text": "🎵 Открыть плеер", "web_app": {"url": mini_app_url}}
                ]]
            }
        )
        logger.info(f"✅ Ответ на /start отправлен пользователю {user.id}")
    except Exception as e:
        logger.error(f"❌ Ошибка в start: {e}\n{traceback.format_exc()}")

# --- 7. Регистрируем команду ---
telegram_app.add_handler(CommandHandler("start", start))

# --- 8. Главная страница ---
@app.route('/')
def index():
    return jsonify({
        "status": "работает! 👍",
        "message": "Music Bot Backend",
        "webhook_url": f"{config.RENDER_EXTERNAL_URL}/webhook"
    })

# --- 9. ВЕБХУК (ПРОСТОЙ И РАБОЧИЙ) ---
@app.route('/webhook', methods=['POST'])
def webhook():
    """Принимает обновления от Telegram"""
    logger.info("🔥 ПОЛУЧЕН ЗАПРОС НА /webhook")

    try:
        # Получаем данные
        update_data = request.get_json()
        logger.info(f"Body: {update_data}")

        if not update_data:
            return jsonify({"error": "empty data"}), 400

        if 'message' in update_data:
            logger.info(f"📨 Сообщение: {update_data['message'].get('text')}")

        # Создаём объект Update
        update = Update.de_json(update_data, bot)
        logger.info(f"✅ Update создан: {update.update_id}")

        # --- ЕДИНСТВЕННЫЙ РАБОЧИЙ СПОСОБ ---
        # Используем ГЛОБАЛЬНЫЙ цикл, который уже работает
        future = asyncio.run_coroutine_threadsafe(
            telegram_app.process_update(update),
            loop
        )
        # Ждём результат (необязательно, но для логов)
        future.result(timeout=5)
        logger.info("✅ Update обработан")

        return 'ok', 200

    except Exception as e:
        logger.error(f"❌ ОШИБКА: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# --- 10. API для фронтенда ---
@app.route('/api/music-list', methods=['GET'])
def get_music_list():
    music_list = [
        {"id": 1, "title": "Тестовая песня 1", "url": "https://example.com/song1.mp3"},
        {"id": 2, "title": "Тестовая песня 2", "url": "https://example.com/song2.mp3"},
    ]
    return jsonify(music_list)

# --- 11. ЗАПУСК ---
if __name__ == '__main__':
    logger.info("🚀 ЗАПУСК СЕРВЕРА")

    # Устанавливаем вебхук
    webhook_url = f"{config.RENDER_EXTERNAL_URL}/webhook"
    try:
        logger.info(f"🔄 Устанавливаем вебхук на {webhook_url}")
        result = bot.set_webhook(url=webhook_url)
        logger.info(f"✅ Результат: {result}")
    except Exception as e:
        logger.error(f"❌ Ошибка установки вебхука: {e}")

    # Запускаем Flask (в том же потоке, цикл уже работает)
    app.run(host='0.0.0.0', port=config.PORT, debug=False)