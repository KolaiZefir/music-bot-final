import logging
import os
import sys
import traceback
import json
from flask import Flask, request, jsonify
import telegram
import config

# --- 1. ЛОГИРОВАНИЕ ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# --- 2. Flask ---
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# --- 3. Простой бот (без Application) ---
bot = telegram.Bot(token=config.BOT_TOKEN)

# --- 4. Главная страница ---
@app.route('/')
def index():
    return jsonify({
        "status": "работает! 👍",
        "message": "Music Bot Backend",
        "webhook_url": f"{config.RENDER_EXTERNAL_URL}/webhook"
    })

# --- 5. ПРОСТЕЙШИЙ ВЕБХУК ---
@app.route('/webhook', methods=['POST'])
def webhook():
    """Максимально простой вебхук"""
    logger.info("="*50)
    logger.info("🔥 ПОЛУЧЕН ЗАПРОС")
    
    try:
        # Логируем всё подряд
        logger.info(f"Headers: {dict(request.headers)}")
        
        # Получаем данные
        update_data = request.get_json()
        logger.info(f"Body: {update_data}")
        
        if not update_data:
            logger.error("❌ Пустые данные")
            return jsonify({"error": "empty"}), 400
        
        # Проверяем, что это сообщение /start
        if 'message' in update_data:
            message = update_data['message']
            text = message.get('text', '')
            chat_id = message['chat']['id']
            user = message['from']
            
            logger.info(f"📨 Сообщение от {user.get('first_name')}: {text}")
            
            # Если это /start - отвечаем
if text == '/start':
    logger.info(f"🔥 Отвечаем на /start для {chat_id}")
    
    try:
        # Отправляем сообщение и СОХРАНЯЕМ результат
        sent_message = bot.send_message(
            chat_id=chat_id,
            text=f"🎵 Привет, {user.get('first_name')}!\n\nНажми кнопку ниже, чтобы открыть музыкальный плеер:",
            reply_markup=json.dumps({
                "inline_keyboard": [[
                    {"text": "🎵 Открыть плеер", "web_app": {"url": f"{config.FRONTEND_URL}?user_id={user.get('id')}"}}
                ]]
            })
        )
        logger.info(f"✅ Ответ отправлен, message_id: {sent_message.message_id}")
        
        # Проверяем, что бот вообще может писать этому пользователю
        bot_info = bot.get_me()
        logger.info(f"🤖 Информация о боте: @{bot_info.username}")
        
    except Exception as e:
        logger.error(f"❌ ОШИБКА ПРИ ОТПРАВКЕ: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# --- 6. API ---
@app.route('/api/music-list', methods=['GET'])
def get_music_list():
    return jsonify([
        {"id": 1, "title": "Тест 1", "url": "https://example.com/1.mp3"}
    ])

# --- 7. ЗАПУСК ---
if __name__ == '__main__':
    logger.info("🚀 ЗАПУСК ПРОСТОЙ ВЕРСИИ")
    
    # Устанавливаем вебхук
    webhook_url = f"{config.RENDER_EXTERNAL_URL}/webhook"
    try:
        logger.info(f"🔄 Устанавливаем вебхук на {webhook_url}")
        result = bot.set_webhook(url=webhook_url)
        logger.info(f"✅ Результат: {result}")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
    
    app.run(host='0.0.0.0', port=config.PORT, debug=False)