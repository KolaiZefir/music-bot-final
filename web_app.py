import logging
import os
import json
import sqlite3
import asyncio
from datetime import datetime
from flask import Flask, request, jsonify
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- НАСТРОЙКА ЛОГИРОВАНИЯ ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- КОНФИГУРАЦИЯ ---
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8496222715:AAF5Yrq4VqWS9KNixjjT_wKInY1OBF9p0lk')
CHANNEL_ID = int(os.environ.get('CHANNEL_ID', '-1003801427378'))
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://music-frontend.vercel.app')
RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL', 'https://music-bot-final-51qb.onrender.com')
PORT = int(os.environ.get('PORT', 10000))

# --- БАЗА ДАННЫХ ---
DB_PATH = 'music.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT UNIQUE,
            file_name TEXT,
            caption TEXT,
            added_at TIMESTAMP,
            message_id INTEGER UNIQUE
        )
    ''')
    conn.commit()
    conn.close()
    logger.info("✅ База данных готова")

def save_track(file_id, file_name, caption, message_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            'INSERT OR IGNORE INTO tracks (file_id, file_name, caption, added_at, message_id) VALUES (?, ?, ?, ?, ?)',
            (file_id, file_name, caption, datetime.now(), message_id)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения: {e}")
        return False

def get_all_tracks():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, file_id, file_name, caption FROM tracks ORDER BY added_at DESC')
    tracks = [{'id': row[0], 'file_id': row[1], 'title': row[2] or 'Без названия', 'caption': row[3]} for row in c.fetchall()]
    conn.close()
    return tracks

# --- СОЗДАЁМ FLASK-ПРИЛОЖЕНИЕ ---
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# --- ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ДЛЯ БОТА ---
bot = None
application = None

# --- ФУНКЦИЯ ДЛЯ ИНИЦИАЛИЗАЦИИ БОТА ---
def init_bot():
    global bot, application
    if bot is None:
        bot = Bot(token=BOT_TOKEN)
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Регистрируем обработчики
        @application.message(Command("start"))
        async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user = update.effective_user
            web_app_url = f"{FRONTEND_URL}?user_id={user.id}"
            
            await update.message.reply_text(
                f"🎵 Привет, {user.first_name}!",
                reply_markup={
                    "inline_keyboard": [[
                        {"text": "🎧 ОТКРЫТЬ ПЛЕЕР", "web_app": {"url": web_app_url}}
                    ]]
                }
            )
            logger.info(f"✅ Ответ на /start отправлен")
        
        # Инициализируем приложение
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(application.initialize())
        logger.info("✅ Бот инициализирован")
    
    return bot, application

# --- МАРШРУТЫ FLASK ---
@app.route('/')
def index():
    tracks_count = len(get_all_tracks())
    return jsonify({
        "status": "работает! 🎵",
        "bot": "@my_music_player_2024_bot",
        "tracks": tracks_count,
        "webhook": f"{RENDER_EXTERNAL_URL}/webhook"
    })

@app.route('/api/tracks')
def api_tracks():
    return jsonify(get_all_tracks())

@app.route('/webhook', methods=['POST'])
def webhook():
    """Принимает обновления от Telegram"""
    try:
        # Инициализируем бота при первом запросе
        bot, application = init_bot()
        
        # Получаем данные
        update_data = request.get_json()
        logger.info(f"🔥 Webhook: {update_data.get('update_id')}")
        
        # Создаём объект Update
        update = Update.de_json(update_data, bot)
        
        # Обрабатываем
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(application.process_update(update))
        
        return 'ok', 200
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return 'error', 500

# --- ЗАПУСК ---
if __name__ == '__main__':
    # Инициализируем БД
    init_db()
    
    # Инициализируем бота
    init_bot()
    
    # Устанавливаем вебхук
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bot.set_webhook(url=webhook_url))
        logger.info(f"✅ Вебхук: {webhook_url}")
    except Exception as e:
        logger.error(f"❌ Ошибка вебхука: {e}")
    
    # Запускаем Flask
    app.run(host='0.0.0.0', port=PORT)