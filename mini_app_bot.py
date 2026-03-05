import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from config import BOT_TOKEN, LOCAL_IP, PORT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет кнопку с Mini App"""
    
    # URL Mini App
    web_app_url = f"https://{LOCAL_IP}:{PORT}/player"
    
    # Создаем кнопку
    keyboard = [
        [InlineKeyboardButton("🎵 ОТКРЫТЬ ПЛЕЕР", web_app={"url": web_app_url})]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем сообщение с кнопкой
    await update.message.reply_text(
        "🎵 Нажми кнопку, чтобы открыть музыкальный плеер!\n\n"
        f"🌐 Адрес: {web_app_url}",
        reply_markup=reply_markup
    )

def main():
    print("="*60)
    print("🎵 MINI APP БОТ")
    print("="*60)
    print(f"📱 IP: {LOCAL_IP}")
    print(f"🌐 URL плеера: https://{LOCAL_IP}:{PORT}/player")
    print("="*60)
    print("✅ Бот запущен. Напишите /start в Telegram")
    print("="*60)
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == '__main__':
    main()