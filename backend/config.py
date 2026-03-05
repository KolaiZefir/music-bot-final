import os

# Токен бота (получен от @BotFather)
BOT_TOKEN = "8496222715:AAF5Yrq4VqWS9KNixjjT_wKInY1OBF9p0lk"

# ID канала, откуда бот берет музыку
CHANNEL_ID = -1003801427378

# ID администратора (ваш Telegram ID)
ADMIN_ID = 1038348220

# URL фронтенда на Vercel
FRONTEND_URL = "https://music-frontend.vercel.app"

# Путь к базе данных
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "music_player.db")

# Папка для загрузок
DOWNLOADS_FOLDER = os.path.join(os.path.dirname(__file__), "downloads")

# Режим отладки (для разработки)
DEBUG = False

# Порт для локального запуска
PORT = int(os.environ.get("PORT", 5000))