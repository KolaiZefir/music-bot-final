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

# --- 3. Создаём и инициализируем бота ---
bot = Bot(token=config.BOT_TOKEN)
# Инициализация бота (обязательно!)
asyncio.run(bot.initialize())

# --- 4. Создаём и инициализируем обработчик команд ---
telegram_app = Application.builder().token(config.BOT_TOKEN).build()
asyncio.run(telegram_app.initialize())

# --- 5. Команда /start ---
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

# --- 6. Регистрируем команду ---
telegram_app.add_handler(CommandHandler("start", start))

# --- 7. Главная страница ---
@app.route('/')
def index():
    return jsonify({
        "status": "работает! 👍",
        "message": "Music Bot Backend",
        "webhook_url": f"{config.RENDER_EXTERNAL_URL}/webhook"
    })

# --- 8. Вебхук для Telegram (с безопасной работой с asyncio) ---
@app.route('/webhook', methods=['POST'])
def webhook():
    """Принимает обновления от Telegram"""
    logger.info("="*50)
    logger.info("🔥 ПОЛУЧЕН ЗАПРОС НА /webhook")

    try:
        # Получаем данные от Telegram
        update_data = request.get_json()
        logger.info(f"Body: {update_data}")

        if not update_data:
            logger.error("❌ Пустые данные")
            return jsonify({"error": "empty data"}), 400

        if 'message' in update_data:
            logger.info(f"📨 Сообщение: {update_data['message'].get('text')}")

        # Создаём объект Update
        update = Update.de_json(update_data, bot)
        logger.info(f"✅ Update создан: {update.update_id}")

        # --- Корректная работа с event loop ---
        try:
            # Пытаемся получить текущий цикл событий
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # Если цикла нет, создаём новый
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Если цикл уже запущен (например, в gunicorn), создаём задачу
            if loop.is_running():
                asyncio.create_task(telegram_app.process_update(update))
                logger.info("✅ Задача создана в работающем цикле")
            else:
                # Если цикл не запущен, запускаем и ждём
                loop.run_until_complete(telegram_app.process_update(update))
                logger.info("✅ Update обработан в новом цикле")

        except Exception as e:
            logger.error(f"❌ Ошибка при обработке Update: {e}")
            logger.error(traceback.format_exc())

        return 'ok', 200

    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА В ВЕБХУКЕ: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# --- 9. API для фронтенда (список треков) ---
@app.route('/api/music-list', methods=['GET'])
def get_music_list():
    """Возвращает тестовый список песен"""
    music_list = [
        {"id": 1, "title": "Тестовая песня 1", "url": "https://example.com/song1.mp3"},
        {"id": 2, "title": "Тестовая песня 2", "url": "https://example.com/song2.mp3"},
    ]
    return jsonify(music_list)

# --- 10. Запуск сервера ---
if __name__ == '__main__':
    logger.info("🚀 ЗАПУСК СЕРВЕРА")
    logger.info(f"✅ BOT_TOKEN: {config.BOT_TOKEN[:10]}...")
    logger.info(f"✅ FRONTEND_URL: {config.FRONTEND_URL}")
    logger.info(f"✅ RENDER_EXTERNAL_URL: {config.RENDER_EXTERNAL_URL}")

    # Устанавливаем вебхук при старте
    webhook_url = f"{config.RENDER_EXTERNAL_URL}/webhook"
    try:
        logger.info(f"🔄 Устанавливаем вебхук на {webhook_url}")
        result = bot.set_webhook(url=webhook_url)
        logger.info(f"✅ Результат установки вебхука: {result}")

        # Проверяем информацию о вебхуке
        webhook_info = bot.get_webhook_info()
        logger.info(f"📞 Информация о вебхуке: {webhook_info}")
    except Exception as e:
        logger.error(f"❌ Не удалось установить вебхук: {e}")
        logger.error(traceback.format_exc())

    # Запускаем Flask-приложение
    app.run(host='0.0.0.0', port=config.PORT, debug=False)