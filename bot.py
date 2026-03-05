import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import BOT_TOKEN, LOCAL_IP, PORT
from database import Database
import asyncio

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# База данных
db = Database()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    try:
        # Сохраняем пользователя
        db.add_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
    except Exception as e:
        logger.error(f"DB error: {e}")
    
    web_app_url = f"https://{LOCAL_IP}:{PORT}/player"
    
    text = (
        f"🎵 Привет, {user.first_name}!\n\n"
        "Я музыкальный бот. Отправь мне аудио или видео файл.\n\n"
        f"🌐 Адрес плеера: {web_app_url}\n\n"
        "👇 Нажми кнопку, чтобы открыть плеер!"
    )
    
    keyboard = [[InlineKeyboardButton("🎵 Открыть плеер", web_app={"url": web_app_url})]]
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def debug_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отладка - просто выводим всё что приходит из канала"""
    try:
        if update.channel_post:
            print("="*50)
            print("🔥 ПОЛУЧЕНО СООБЩЕНИЕ ИЗ КАНАЛА!")
            print(f"ID чата: {update.channel_post.chat_id}")
            print(f"Тип: {update.channel_post.chat.type}")
            print(f"Текст: {update.channel_post.text}")
            print(f"Есть аудио: {bool(update.channel_post.audio)}")
            print(f"Есть видео: {bool(update.channel_post.video)}")
            print(f"Есть документ: {bool(update.channel_post.document)}")
            print("="*50)
            
            # Если есть аудио - показываем информацию
            if update.channel_post.audio:
                audio = update.channel_post.audio
                print(f"🎵 АУДИО:")
                print(f"  - ID: {audio.file_id}")
                print(f"  - Название: {audio.title}")
                print(f"  - Исполнитель: {audio.performer}")
                print(f"  - Длительность: {audio.duration}")
                
    except Exception as e:
        print(f"❌ Ошибка в debug: {e}")

# Добавьте этот обработчик в bot.py (перед app.run_polling())
application.add_handler(MessageHandler(filters.ChatType.CHANNEL, debug_channel))

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка аудиофайлов"""
    try:
        audio = update.message.audio
        user_id = update.effective_user.id
        
        db.add_track(
            user_id=user_id,
            file_id=audio.file_id,
            file_name=audio.file_name or f"audio_{audio.file_id[:10]}.mp3",
            title=audio.title or "Unknown",
            artist=audio.performer or "Unknown",
            duration=audio.duration or 0,
            file_size=audio.file_size or 0,
            mime_type='audio/mpeg'
        )
        
        await update.message.reply_text(f"✅ Аудио добавлено: {audio.title or audio.file_name}")
    except Exception as e:
        logger.error(f"Error handling audio: {e}")
        await update.message.reply_text("❌ Ошибка при добавлении аудио")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка видеофайлов"""
    try:
        video = update.message.video
        user_id = update.effective_user.id
        title = update.message.caption or "Video"
        
        db.add_track(
            user_id=user_id,
            file_id=video.file_id,
            file_name=video.file_name or f"video_{video.file_id[:10]}.mp4",
            title=title,
            artist="Video",
            duration=video.duration or 0,
            file_size=video.file_size or 0,
            mime_type='video/mp4'
        )
        
        await update.message.reply_text(f"✅ Видео добавлено: {title}")
    except Exception as e:
        logger.error(f"Error handling video: {e}")
        await update.message.reply_text("❌ Ошибка при добавлении видео")

def main():
    """Запуск бота"""
    print("="*60)
    print("🎵 МУЗЫКАЛЬНЫЙ БОТ")
    print("="*60)
    print(f"✅ Конфигурация загружена")
    print(f"📱 Ваш IP: {LOCAL_IP}")
    print(f"🌐 URL плеера: https://{LOCAL_IP}:{PORT}/player")
    print(f"🤖 Токен бота: {BOT_TOKEN[:10]}...")
    print("="*60)
    
    try:
        # Создаем приложение
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.AUDIO, handle_audio))
        application.add_handler(MessageHandler(filters.VIDEO, handle_video))
        
        print("✅ Бот запущен и готов к работе!")
        print("📢 Отправьте /start в Telegram")
        print("="*60)
        
        # Запускаем бота
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        print(f"❌ Ошибка при запуске бота: {e}")
        print("\nПроверьте:")
        print("1. Токен бота в файле .env")
        print("2. Установлены ли все зависимости")
        print("3. Подключение к интернету")

if __name__ == '__main__':
    main()