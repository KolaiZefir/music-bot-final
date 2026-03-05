import sqlite3
import os
from datetime import datetime

class MusicDatabase:
    """Класс для работы с базой данных музыки"""
    
    def __init__(self, db_path='music_player.db'):
        """Инициализация подключения к БД"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Создание таблиц, если их нет"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица для треков
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                artist TEXT,
                file_path TEXT NOT NULL,
                duration INTEGER,
                cover_url TEXT,
                telegram_file_id TEXT,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ База данных инициализирована")
    
    def add_track(self, title, artist, file_path, duration=None, cover_url=None, telegram_file_id=None):
        """Добавление трека в базу"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tracks (title, artist, file_path, duration, cover_url, telegram_file_id, added_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (title, artist, file_path, duration, cover_url, telegram_file_id, datetime.now()))
        
        conn.commit()
        track_id = cursor.lastrowid
        conn.close()
        return track_id
    
    def get_all_tracks(self):
        """Получение всех треков"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM tracks ORDER BY added_date DESC')
        tracks = cursor.fetchall()
        conn.close()
        return tracks
    
    def get_track(self, track_id):
        """Получение трека по ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM tracks WHERE id = ?', (track_id,))
        track = cursor.fetchone()
        conn.close()
        return track
    
    def search_tracks(self, query):
        """Поиск треков по названию или исполнителю"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM tracks 
            WHERE title LIKE ? OR artist LIKE ?
            ORDER BY added_date DESC
        ''', (f'%{query}%', f'%{query}%'))
        
        tracks = cursor.fetchall()
        conn.close()
        return tracks
    
    def delete_track(self, track_id):
        """Удаление трека"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM tracks WHERE id = ?', (track_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted
    
    def update_track(self, track_id, title=None, artist=None, cover_url=None):
        """Обновление информации о треке"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if title:
            updates.append("title = ?")
            params.append(title)
        if artist:
            updates.append("artist = ?")
            params.append(artist)
        if cover_url:
            updates.append("cover_url = ?")
            params.append(cover_url)
        
        if not updates:
            conn.close()
            return False
        
        params.append(track_id)
        query = f"UPDATE tracks SET {', '.join(updates)} WHERE id = ?"
        
        cursor.execute(query, params)
        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()
        return updated
