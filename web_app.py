import logging
import os
from flask import Flask, request, jsonify
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
import config

# --- 1. Настройка логирования ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- 2. Создаём веб-сервер Flask ---
app = Flask(__name__)

# --- ВАЖНО! Говорим Flask как обрабатывать JSON ---
app.config['JSON_AS_ASCII'] = False

# --- 3. Создаём бота ---
bot = Bot(token=config.BOT_TOKEN)

# --- 4. Создаём "обработчик команд" ---
telegram_app = Application.builder().token(config.BOT_TOKEN).build()

# --- 5. Команда /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Когда пользователь пишет /start - показываем кнопку с плеером"""
    user = update.effective_user
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

# --- 8. ВАЖНО! Вебхук для Telegram ---
@app.route('/webhook', methods=['POST'])
async def webhook():
    """Сюда Telegram присылает сообщения"""
    try:
        # Получаем данные от Telegram
        update_data = request.get_json()
        logger.info(f"🔥 Получен вебхук: {update_data}")
        
        if not update_data:
            logger.error("Пустые данные от Telegram")
            return 'empty', 400
        
        # Превращаем JSON в объект Update
        update = Update.de_json(update_data, bot)
        
        # Обрабатываем сообщение
        await telegram_app.process_update(update)
        
        return 'ok', 200
    except Exception as e:
        logger.error(f"❌ Ошибка вебхука: {e}")
        return f'error: {e}', 500

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
    # Устанавливаем вебхук
    webhook_url = f"{config.RENDER_EXTERNAL_URL}/webhook"
    try:
        bot.set_webhook(url=webhook_url)
        logger.info(f"✅ Вебхук установлен: {webhook_url}")
        
        # Проверяем что установилось
        webhook_info = bot.get_webhook_info()
        logger.info(f"📞 Информация о вебхуке: {webhook_info}")
    except Exception as e:
        logger.error(f"❌ Не удалось установить вебхук: {e}")
    
    # Запускаем сервер
    app.run(host='0.0.0.0', port=config.PORT)