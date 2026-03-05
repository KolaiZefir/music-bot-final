import os
from dotenv import load_dotenv

load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv('BOT_TOKEN', '8496222715:AAF5Yrq4VqWS9KNixjjT_wKInY1OBF9p0lk')

# ВАШ РЕАЛЬНЫЙ IP ИЗ IPCONFIG (ЗАМЕНИТЕ НА СВОЙ!)
LOCAL_IP = '192.168.0.2'  # ВСТАВЬТЕ СЮДА ВАШ IP

PORT = 8443  # Порт для HTTPS

# URL для Mini App
APP_URL = f'https://{LOCAL_IP}:{PORT}'

# Пути к SSL сертификатам
SSL_CERT = 'cert.pem'
SSL_KEY = 'key.pem'

print("="*50)
print(f"✅ Локальный IP: {LOCAL_IP}")
print(f"🌐 URL плеера: {APP_URL}/player")
print("="*50)
RENDER_EXTERNAL_URL = "https://music-bot-final-51qb.onrender.com"