import logging
import os
import sys
import traceback
from flask import Flask, request, jsonify
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
import config

# --- 1. МАКСИМАЛЬНОЕ ЛОГИРОВАНИЕ ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,  # DEBUG вместо INFO
    stream=sys.stdout
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# --- 2. Создаём веб-сервер Flask ---
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# --- 3. Создаём бота ---
bot = Bot(token=config.BOT_TOKEN)

# --- 4. Создаём обработчик команд ---
telegram_app = Application.builder().token(config.BOT_TOKEN).build()

# --- 5. Команда /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Когда пользователь пишет /start - показываем кнопку с плеером"""
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

# --- 8. Вебхук с ПОЛНЫМ логированием ошибок ---
@app.route('/webhook', methods=['POST'])
def webhook():
    """Сюда Telegram присылает сообщения"""
    logger.info("="*50)
    logger.info("🔥 ПОЛУЧЕН ЗАПРОС НА /webhook")
    
    try:
        # Логируем заголовки запроса
        logger.info(f"Headers: {dict(request.headers)}")
        
        # Получаем данные
        update_data = request.get_json()
        logger.info(f"Body: {update_data}")
        
        if not update_data:
            logger.error("❌ Пустые данные от Telegram")
            return jsonify({"error": "empty data"}), 400
        
        # Проверяем, что это сообщение
        if 'message' in update_data:
            logger.info(f"📨 Сообщение: {update_data['message'].get('text')}")
        
        # Пытаемся обработать через telegram_app
        try:
            logger.info("🔄 Создаём объект Update...")
            update = Update.de_json(update_data, bot)
            logger.info(f"✅ Update создан: {update.update_id}")
            
            # Запускаем обработку
            logger.info("🔄 Запускаем process_update...")
            # ВАЖНО: process_update - асинхронный, нужно запустить по-другому
            import asyncio
            
            # Создаём новый event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Запускаем асинхронную функцию
            loop.run_until_complete(telegram_app.process_update(update))
            loop.close()
            
            logger.info("✅ Update обработан успешно")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при обработке Update: {e}")
            logger.error(traceback.format_exc())
        
        return 'ok', 200
        
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА В ВЕБХУКЕ: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# --- 9. API для фронтенда ---
@app.route('/api/music-list', methods=['GET'])
def get_music_list():
    """Список песен для плеера"""
    music_list = [
        {"id": 1, "title": "Тестовая песня 1", "url": "https://example.com/song1.mp3"},
        {"id": 2, "title": "Тестовая песня 2", "url": "https://example.com/song2.mp3"},
    ]
    return jsonify(music_list)

# --- 10. Запуск ---
if __name__ == '__main__':
    logger.info("🚀 ЗАПУСК СЕРВЕРА")
    logger.info(f"✅ BOT_TOKEN: {config.BOT_TOKEN[:10]}...")
    logger.info(f"✅ FRONTEND_URL: {config.FRONTEND_URL}")
    logger.info(f"✅ RENDER_EXTERNAL_URL: {config.RENDER_EXTERNAL_URL}")
    
    # Устанавливаем вебхук
    webhook_url = f"{config.RENDER_EXTERNAL_URL}/webhook"
    try:
        logger.info(f"🔄 Устанавливаем вебхук на {webhook_url}")
        result = bot.set_webhook(url=webhook_url)
        logger.info(f"✅ Результат установки вебхука: {result}")
        
        # Проверяем что установилось
        webhook_info = bot.get_webhook_info()
        logger.info(f"📞 Информация о вебхуке: {webhook_info}")
    except Exception as e:
        logger.error(f"❌ Не удалось установить вебхук: {e}")
        logger.error(traceback.format_exc())
    
    # Запускаем сервер
    logger.info(f"🚀 Сервер запускается на порту {config.PORT}")
    app.run(host='0.0.0.0', port=config.PORT, debug=False)
