import os
import json
import requests
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from .database import MusicDatabase
from .config import BOT_TOKEN, FRONTEND_URL, DOWNLOADS_FOLDER, DEBUG, PORT

# Создаем Flask приложение
app = Flask(__name__)

# Настройка CORS для работы с фронтендом
CORS(app, origins=[
    FRONTEND_URL,
    "http://localhost:3000",
    "http://localhost:5000",
    "http://127.0.0.1:5000"
])

# Инициализация базы данных
db = MusicDatabase()

# ---------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------
def send_telegram_message(chat_id, text, reply_markup=None):
    """Отправка сообщения в Telegram через API"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")
        return None

# ---------- API ДЛЯ ПЛЕЕРА ----------
@app.route('/', methods=['GET'])
def index():
    """Главная страница API"""
    return jsonify({
        'status': 'ok',
        'message': 'Music Bot API is running',
        'version': '1.0.0',
        'endpoints': [
            '/tracks - получить все треки',
            '/track/<id> - получить информацию о треке',
            '/track/<id>/play - воспроизвести трек',
            '/track/<id>/download - скачать трек',
            '/search?q=<query> - поиск треков',
            '/webhook - вебхук для Telegram (POST)'
        ]
    })

@app.route('/tracks', methods=['GET'])
def get_tracks():
    """Получить все треки"""
    try:
        tracks = db.get_all_tracks()
        tracks_list = []
        for track in tracks:
            tracks_list.append({
                'id': track[0],
                'title': track[1],
                'artist': track[2] or 'Неизвестный исполнитель',
                'duration': track[4] or 0,
                'cover_url': track[5] or f"{request.host_url}static/default-cover.jpg"
            })
        return jsonify(tracks_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/track/<int:track_id>', methods=['GET'])
def get_track(track_id):
    """Получить информацию о треке"""
    try:
        track = db.get_track(track_id)
        if track:
            return jsonify({
                'id': track[0],
                'title': track[1],
                'artist': track[2] or 'Неизвестный исполнитель',
                'duration': track[4] or 0,
                'cover_url': track[5] or f"{request.host_url}static/default-cover.jpg"
            })
        return jsonify({'error': 'Track not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/track/<int:track_id>/play', methods=['GET'])
def play_track(track_id):
    """Воспроизвести трек (стриминг)"""
    try:
        track = db.get_track(track_id)
        if not track:
            return jsonify({'error': 'Track not found'}), 404

        file_path = track[3]
        
        # Проверяем существование файла
        if not os.path.exists(file_path):
            # Ищем в папке downloads
            filename = os.path.basename(file_path)
            possible_path = os.path.join(DOWNLOADS_FOLDER, filename)
            if os.path.exists(possible_path):
                file_path = possible_path
            else:
                return jsonify({'error': 'File not found'}), 404

        return send_file(
            file_path,
            mimetype='audio/mpeg',
            as_attachment=False,
            download_name=f"{track[1]} - {track[2]}.mp3"
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/track/<int:track_id>/download', methods=['GET'])
def download_track(track_id):
    """Скачать трек"""
    try:
        track = db.get_track(track_id)
        if not track:
            return jsonify({'error': 'Track not found'}), 404

        file_path = track[3]
        
        if not os.path.exists(file_path):
            filename = os.path.basename(file_path)
            possible_path = os.path.join(DOWNLOADS_FOLDER, filename)
            if os.path.exists(possible_path):
                file_path = possible_path
            else:
                return jsonify({'error': 'File not found'}), 404

        return send_file(
            file_path,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name=f"{track[1]} - {track[2]}.mp3"
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/search', methods=['GET'])
def search_tracks():
    """Поиск треков"""
    try:
        query = request.args.get('q', '')
        if not query or len(query) < 2:
            return jsonify([])

        tracks = db.search_tracks(query)
        tracks_list = []
        for track in tracks:
            tracks_list.append({
                'id': track[0],
                'title': track[1],
                'artist': track[2] or 'Неизвестный исполнитель',
                'duration': track[4] or 0,
                'cover_url': track[5] or f"{request.host_url}static/default-cover.jpg"
            })
        return jsonify(tracks_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ---------- ВЕБХУК ДЛЯ TELEGRAM ----------
@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработчик сообщений от Telegram"""
    try:
        data = request.get_json()
        
        # Проверяем, что это сообщение
        if data and 'message' in data:
            msg = data['message']
            chat_id = msg['chat']['id']
            
            # Обработка команды /start
            if 'text' in msg and msg['text'] == '/start':
                # Создаем кнопку для Mini App
                keyboard = {
                    "inline_keyboard": [[
                        {
                            "text": "🎵 Открыть плеер",
                            "web_app": {"url": FRONTEND_URL}
                        }
                    ]]
                }
                
                # Отправляем приветственное сообщение с кнопкой
                send_telegram_message(
                    chat_id,
                    "👋 <b>Добро пожаловать в Music Player!</b>\n\n"
                    "Нажми кнопку ниже, чтобы открыть плеер и слушать музыку.",
                    keyboard
                )
            
            # Обработка аудиофайлов (если нужно)
            elif 'audio' in msg or 'document' in msg:
                send_telegram_message(
                    chat_id,
                    "📥 Функция загрузки музыки будет добавлена позже."
                )
        
        return 'ok', 200
        
    except Exception as e:
        print(f"Ошибка в вебхуке: {e}")
        return 'ok', 200  # Всегда возвращаем 200, чтобы Telegram не повторял

# ---------- СТАТИЧЕСКИЕ ФАЙЛЫ ----------
@app.route('/static/default-cover.jpg')
def default_cover():
    """Заглушка для обложки (можно заменить на реальное изображение)"""
    return '', 404

# ---------- ЗАПУСК СЕРВЕРА ----------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=DEBUG)