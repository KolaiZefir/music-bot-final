import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from config import BOT_TOKEN
from database import Database

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# База данных
db = Database()

# ID вашего канала (скопируйте из логов)
YOUR_CHANNEL_ID = -1003801427378  # ВСТАВЬТЕ ВАШ ID

async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сообщений из канала"""
    try:
        # Проверяем, что сообщение из нужного канала
        if update.channel_post.chat_id != YOUR_CHANNEL_ID:
            return
        
        print("\n" + "🎵"*30)
        print("ПОЛУЧЕНО СООБЩЕНИЕ ИЗ ВАШЕГО КАНАЛА!")
        
        # Проверяем аудио
        if update.channel_post.audio:
            audio = update.channel_post.audio
            print(f"🎵 Найдено аудио!")
            print(f"Название: {audio.title}")
            print(f"Исполнитель: {audio.performer}")
            print(f"Файл: {audio.file_name}")
            
            # Сохраняем в базу (используем ваш user ID)
            # Ваш user ID из логов: 1038348220
            db.add_track(
                user_id=1038348220,  # ВАШ ID
                file_id=audio.file_id,
                file_name=audio.file_name or f"{audio.performer} - {audio.title}.mp3",
                title=audio.title or "Unknown",
                artist=audio.performer or "Unknown",
                duration=audio.duration or 0,
                file_size=audio.file_size or 0,
                mime_type='audio/mpeg'
            )
            
            print(f"✅ Аудио сохранено в базу!")
        
        # Проверяем видео
        elif update.channel_post.video:
            video = update.channel_post.video
            print(f"🎬 Найдено видео!")
            
            db.add_track(
                user_id=1038348220,
                file_id=video.file_id,
                file_name=video.file_name or f"video_{video.file_id[:10]}.mp4",
                title=update.channel_post.caption or "Video",
                artist="Video",
                duration=video.duration or 0,
                file_size=video.file_size or 0,
                mime_type='video/mp4'
            )
            
            print(f"✅ Видео сохранено в базу!")
        
        print("🎵"*30 + "\n")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def main():
    print("="*60)
    print("🎵 БОТ ДЛЯ КАНАЛА ЗАПУЩЕН")
    print("="*60)
    print(f"ID канала: {YOUR_CHANNEL_ID}")
    print("Отправляйте музыку в канал - бот будет её сохранять")
    print("="*60)
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Обработчик только для сообщений из каналов
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL, handle_channel_post))
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()