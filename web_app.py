import logging
import os
import sys
import traceback
import json
import asyncio
from flask import Flask, request, jsonify
from telegram import Bot, Update
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

# --- 3. СОЗДАЁМ БОТА И ЦИКЛ СОБЫТИЙ ---
bot = Bot(token=config.BOT_TOKEN)

# Создаём глобальный цикл событий
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Инициализируем бота
loop.run_until_complete(bot.initialize())

# --- 4. Главная страница ---
@app.route('/')
def index():
    return jsonify({
        "status": "работает! 👍",
        "message": "Music Bot Backend",
        "webhook_url": f"{config.RENDER_EXTERNAL_URL}/webhook"
    })

# --- 5. ВЕБХУК ---
@app.route('/webhook', methods=['POST'])
def webhook():
    """Принимает обновления от Telegram"""
    logger.info("="*50)
    logger.info("🔥 ПОЛУЧЕН ЗАПРОС НА /webhook")
    
    try:
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
                
                # СОЗДАЁМ КОРУТИНУ ДЛЯ ОТПРАВКИ
                async def send_reply():
                    try:
                        msg = await bot.send_message(
                            chat_id=chat_id,
                            text=f"🎵 Привет, {first_name}!\n\nНажми кнопку ниже, чтобы открыть музыкальный плеер:",
                            reply_markup=json.dumps({
                                "inline_keyboard": [[
                                    {"text": "🎵 Открыть плеер", "web_app": {"url": f"{config.FRONTEND_URL}?user_id={user_id}"}}
                                ]]
                            })
                        )
                        logger.info(f"✅ Ответ отправлен, message_id: {msg.message_id}")
                        return msg
                    except Exception as e:
                        logger.error(f"❌ Ошибка в send_reply: {e}")
                        logger.error(traceback.format_exc())
                        return None
                
                # ЗАПУСКАЕМ КОРУТИНУ В ГЛОБАЛЬНОМ ЦИКЛЕ
                future = asyncio.run_coroutine_threadsafe(send_reply(), loop)
                try:
                    # Ждём результат с таймаутом
                    future.result(timeout=10)
                except Exception as e:
                    logger.error(f"❌ Ошибка при ожидании ответа: {e}")
        
        return 'ok', 200
        
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# --- 6. API для списка музыки ---
@app.route('/api/music-list', methods=['GET'])
def get_music_list():
    music_list = [
        {"id": 1, "title": "Тестовая песня 1", "url": "https://example.com/song1.mp3"},
        {"id": 2, "title": "Тестовая песня 2", "url": "https://example.com/song2.mp3"},
    ]
    return jsonify(music_list)

# --- 7. ЗАПУСК ---
if __name__ == '__main__':
    logger.info("🚀 ЗАПУСК СЕРВЕРА")
    
    # Устанавливаем вебхук
    webhook_url = f"{config.RENDER_EXTERNAL_URL}/webhook"
    try:
        # Для установки вебхука используем тот же цикл
        async def setup_webhook():
            result = await bot.set_webhook(url=webhook_url)
            logger.info(f"✅ Результат установки вебхука: {result}")
            webhook_info = await bot.get_webhook_info()
            logger.info(f"📞 Информация о вебхуке: {webhook_info}")
        
        loop.run_until_complete(setup_webhook())
        
    except Exception as e:
        logger.error(f"❌ Ошибка при установке вебхука: {e}")
        logger.error(traceback.format_exc())
    
    # Запускаем Flask
    logger.info(f"🚀 Сервер запускается на порту {config.PORT}")
    app.run(host='0.0.0.0', port=config.PORT, debug=False)