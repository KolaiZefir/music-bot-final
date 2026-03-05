import logging
import os
import json
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- НАСТРОЙКА ЛОГИРОВАНИЯ ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- КОНФИГУРАЦИЯ (из переменных окружения) ---
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8496222715:AAF5Yrq4VqWS9KNixjjT_wKInY1OBF9p0lk')
CHANNEL_ID = int(os.environ.get('CHANNEL_ID', '-1003801427378'))
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://music-frontend.vercel.app')
RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL', 'https://music-bot-final-51qb.onrender.com')
PORT = int(os.environ.get('PORT', 10000))

# --- БАЗА ДАННЫХ (SQLite) ---
DB_PATH = 'music.db'

def init_db():
    """Создаёт таблицу для хранения музыки из канала"""
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
    logger.info("✅ База данных инициализирована")

def save_track(file_id, file_name, caption, message_id):
    """Сохраняет трек в базу данных"""
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
        logger.error(f"Ошибка сохранения трека: {e}")
        return False

def get_all_tracks():
    """Возвращает все треки из базы"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, file_id, file_name, caption FROM tracks ORDER BY added_at DESC')
    tracks = [{'id': row[0], 'file_id': row[1], 'title': row[2] or 'Без названия', 'caption': row[3]} for row in c.fetchall()]
    conn.close()
    return tracks

# --- СОЗДАЁМ БОТА И ПРИЛОЖЕНИЕ ---
bot = Bot(token=BOT_TOKEN)
application = Application.builder().token(BOT_TOKEN).build()

# --- ОБРАБОТЧИК КОМАНДЫ /start ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет кнопку с плеером"""
    user = update.effective_user
    web_app_url = f"{FRONTEND_URL}?user_id={user.id}"
    
    await update.message.reply_text(
        f"🎵 Привет, {user.first_name}!\n\n"
        f"Это музыкальный плеер. Нажми кнопку ниже, чтобы слушать музыку из канала.\n\n"
        f"📌 Бот должен быть админом канала!",
        reply_markup={
            "inline_keyboard": [[
                {"text": "🎧 ОТКРЫТЬ ПЛЕЕР", "web_app": {"url": web_app_url}}
            ]]
        }
    )
    logger.info(f"✅ Ответ на /start отправлен пользователю {user.id}")

# --- ОБРАБОТЧИК СООБЩЕНИЙ ИЗ КАНАЛА ---
async def channel_post_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет аудиофайлы из канала в базу данных"""
    message = update.channel_post
    
    # Проверяем, что сообщение из нужного канала
    if message.chat.id != CHANNEL_ID:
        return
    
    # Проверяем, есть ли аудио
    if message.audio:
        file_id = message.audio.file_id
        file_name = message.audio.file_name or message.audio.title or f"audio_{message.message_id}.mp3"
        caption = message.caption or ""
        
        if save_track(file_id, file_name, caption, message.message_id):
            logger.info(f"✅ Сохранён трек: {file_name}")
            await message.reply_text(f"✅ Трек сохранён: {file_name}")
    
    # Проверяем, есть ли документ (возможно, mp3)
    elif message.document and message.document.mime_type == 'audio/mpeg':
        file_id = message.document.file_id
        file_name = message.document.file_name or f"doc_{message.message_id}.mp3"
        caption = message.caption or ""
        
        if save_track(file_id, file_name, caption, message.message_id):
            logger.info(f"✅ Сохранён документ: {file_name}")
            await message.reply_text(f"✅ Трек сохранён: {file_name}")

# --- РЕГИСТРИРУЕМ ОБРАБОТЧИКИ ---
application.add_handler(CommandHandler("start", start_command))
application.add_handler(MessageHandler(filters.Chat(chat_id=CHANNEL_ID) & filters.AUDIO, channel_post_handler))
application.add_handler(MessageHandler(filters.Chat(chat_id=CHANNEL_ID) & filters.Document.MP3, channel_post_handler))

# --- СОЗДАЁМ FLASK-ПРИЛОЖЕНИЕ ---
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# --- МАРШРУТЫ FLASK ---
@app.route('/')
def index():
    """Главная страница"""
    return jsonify({
        "status": "работает! 🎵",
        "bot": "@my_music_player_2024_bot",
        "channel_id": CHANNEL_ID,
        "tracks_count": len(get_all_tracks()),
        "webhook": f"{RENDER_EXTERNAL_URL}/webhook"
    })

@app.route('/api/tracks')
def api_tracks():
    """API для фронтенда: возвращает список треков"""
    return jsonify(get_all_tracks())

@app.route('/webhook', methods=['POST'])
def webhook():
    """Принимает обновления от Telegram"""
    try:
        update_data = request.get_json()
        logger.info(f"🔥 Получен webhook: {update_data.get('update_id')}")
        
        # Обрабатываем обновление асинхронно
        update = Update.de_json(update_data, bot)
        
        # Запускаем обработку в существующем цикле
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(application.process_update(update))
        
        return 'ok', 200
    except Exception as e:
        logger.error(f"❌ Ошибка webhook: {e}")
        return 'error', 500

# --- ЗАПУСК ---
if __name__ == '__main__':
    # Инициализируем базу данных
    init_db()
    
    # Инициализируем приложение Telegram
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(application.initialize())
    
    # Устанавливаем вебхук
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
    try:
        loop.run_until_complete(bot.set_webhook(url=webhook_url))
        logger.info(f"✅ Вебхук установлен: {webhook_url}")
    except Exception as e:
        logger.error(f"❌ Ошибка установки вебхука: {e}")
    
    # Запускаем Flask
    logger.info(f"🚀 Сервер запущен на порту {PORT}")
    app.run(host='0.0.0.0', port=PORT)