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

# --- 3. Простой бот ---
bot = telegram.Bot(token=config.BOT_TOKEN)

# --- 4. Главная страница ---
@app.route('/')
def index():
    return jsonify({
        "status": "работает! 👍",
        "message": "Music Bot Backend",
        "webhook_url": f"{config.RENDER_EXTERNAL_URL}/webhook"
    })

# --- 5. ВЕБХУК (ИСПРАВЛЕННЫЙ) ---
@app.route('/webhook', methods=['POST'])
def webhook():
    """Принимает обновления от Telegram"""
    logger.info("="*50)
    logger.info("🔥 ПОЛУЧЕН ЗАПРОС НА /webhook")
    
    try:
        # Логируем заголовки
        logger.info(f"Headers: {dict(request.headers)}")
        
        # Получаем данные
        update_data = request.get_json()
        logger.info(f"Body: {update_data}")
        
        if not update_data:
            logger.error("❌ Пустые данные")
            return jsonify({"error": "empty"}), 400
        
        # Проверяем, что это сообщение
        if 'message' in update_data:
            message = update_data['message']
            text = message.get('text', '')
            chat_id = message['chat']['id']
            user = message['from']
            user_id = user.get('id')
            first_name = user.get('first_name', 'пользователь')
            
            logger.info(f"📨 Сообщение от {first_name} (ID: {user_id}): {text}")
            
            # Если это /start - отвечаем
            if text == '/start':
                logger.info(f"🔥 Отвечаем на /start для {chat_id}")
                
                try:
                    # Отправляем сообщение
                    sent_message = bot.send_message(
                        chat_id=chat_id,
                        text=f"🎵 Привет, {first_name}!\n\nНажми кнопку ниже, чтобы открыть музыкальный плеер:",
                        reply_markup=json.dumps({
                            "inline_keyboard": [[
                                {"text": "🎵 Открыть плеер", "web_app": {"url": f"{config.FRONTEND_URL}?user_id={user_id}"}}
                            ]]
                        })
                    )
                    logger.info(f"✅ Ответ отправлен, message_id: {sent_message.message_id}")
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка при отправке сообщения: {e}")
                    logger.error(traceback.format_exc())
        
        return 'ok', 200
        
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА В ВЕБХУКЕ: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# --- 6. API для списка музыки ---
@app.route('/api/music-list', methods=['GET'])
def get_music_list():
    """Возвращает список доступных треков"""
    music_list = [
        {"id": 1, "title": "Тестовая песня 1", "url": "https://example.com/song1.mp3"},
        {"id": 2, "title": "Тестовая песня 2", "url": "https://example.com/song2.mp3"},
    ]
    return jsonify(music_list)

# --- 7. ЗАПУСК ---
if __name__ == '__main__':
    logger.info("🚀 ЗАПУСК СЕРВЕРА")
    logger.info(f"✅ BOT_TOKEN: {config.BOT_TOKEN[:10]}...")
    logger.info(f"✅ FRONTEND_URL: {config.FRONTEND_URL}")
    logger.info(f"✅ RENDER_EXTERNAL_URL: {config.RENDER_EXTERNAL_URL}")
    
    # Получаем информацию о боте
    try:
        bot_info = bot.get_me()
        logger.info(f"✅ Бот @{bot_info.username} (ID: {bot_info.id})")
    except Exception as e:
        logger.error(f"❌ Не удалось получить информацию о боте: {e}")
    
    # Устанавливаем вебхук
    webhook_url = f"{config.RENDER_EXTERNAL_URL}/webhook"
    try:
        logger.info(f"🔄 Устанавливаем вебхук на {webhook_url}")
        result = bot.set_webhook(url=webhook_url)
        logger.info(f"✅ Результат установки вебхука: {result}")
        
        # Проверяем вебхук
        webhook_info = bot.get_webhook_info()
        logger.info(f"📞 Информация о вебхуке: {webhook_info}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при установке вебхука: {e}")
        logger.error(traceback.format_exc())
    
    # Запускаем Flask
    logger.info(f"🚀 Сервер запускается на порту {config.PORT}")
    app.run(host='0.0.0.0', port=config.PORT, debug=False)