import os
from dotenv import load_dotenv

load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv('BOT_TOKEN', '8496222715:AAF5Yrq4VqWS9KNixjjT_wKInY1OBF9p0lk')

# Порт для сервера (Render сам задаёт PORT)
PORT = int(os.environ.get('PORT', 8443))

# URL фронтенда (Vercel)
FRONTEND_URL = "https://music-frontend.vercel.app"

# URL бэкенда на Render
RENDER_EXTERNAL_URL = "https://music-bot-final-51qb.onrender.com"

# Эти переменные больше не нужны для Render, оставляем для локальной разработки
# LOCAL_IP = '192.168.0.2'
# APP_URL = f"https://music-bot-final-51qb.onrender.com"
# SSL_CERT = 'cert.pem'
# SSL_KEY = 'key.pem'