// Инициализация Telegram Web App
const tg = window.Telegram.WebApp;
tg.expand();
tg.enableClosingConfirmation();

const user = tg.initDataUnsafe?.user;
const userId = user?.id || 1038348220; // Ваш ID из логов

// Глобальные переменные
let tracks = [];
let currentTrack = null;
let audioPlayer = document.getElementById('audioPlayer');
let isPlaying = false;
let currentTab = 'tracks';

// При загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    loadTracks();
    setupEventListeners();
    showTab('tracks');
});

// Настройка обработчиков событий
function setupEventListeners() {
    audioPlayer.addEventListener('play', () => {
        isPlaying = true;
        updatePlayButtons('pause');
        updateNowPlayingDisplay();
    });
    
    audioPlayer.addEventListener('pause', () => {
        isPlaying = false;
        updatePlayButtons('play');
    });
    
    audioPlayer.addEventListener('ended', () => {
        playNext();
    });
    
    audioPlayer.addEventListener('timeupdate', updateProgress);
}

// Загрузка треков
async function loadTracks() {
    try {
        showLoading(true);
        const response = await fetch(`/api/tracks/${userId}`);
        tracks = await response.json();
        displayTracks();
    } catch (error) {
        console.error('Error loading tracks:', error);
        showError('Ошибка загрузки треков');
    } finally {
        showLoading(false);
    }
}

// Отображение треков
function displayTracks() {
    const tracksList = document.getElementById('tracksList');
    
    if (tracks.length === 0) {
        tracksList.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🎵</div>
                <div class="empty-text">Пока нет медиафайлов</div>
                <div class="empty-subtext">Отправьте музыку боту или в канал</div>
            </div>
        `;
        return;
    }
    
    tracksList.innerHTML = tracks.map(track => {
        const isVideo = track.media_type === 'video';
        const icon = isVideo ? '🎬' : '🎵';
        const isCurrentTrack = currentTrack?.track_id === track.track_id;
        
        return `
            <div class="track-item ${isCurrentTrack ? 'playing' : ''}" 
                 onclick="playTrack(${track.track_id})">
                <div class="track-cover-mini">
                    ${icon}
                </div>
                <div class="track-info">
                    <div class="track-name">${track.title || track.file_name}</div>
                    <div class="track-artist">${track.artist || 'Неизвестный исполнитель'}</div>
                </div>
                <div class="track-meta">
                    <span class="track-duration">${formatDuration(track.duration)}</span>
                    ${isVideo ? '<span class="video-badge">видео</span>' : ''}
                </div>
                ${isCurrentTrack ? '<div class="playing-indicator">🔊</div>' : ''}
            </div>
        `;
    }).join('');
}

// Воспроизведение трека
async function playTrack(trackId) {
    const track = tracks.find(t => t.track_id === trackId);
    if (!track) return;
    
    try {
        currentTrack = track;
        
        // Обновляем URL плеера
        audioPlayer.src = `/api/track/${trackId}/stream`;
        
        // Пытаемся воспроизвести
        await audioPlayer.play();
        
        // Обновляем интерфейс
        updateNowPlaying(track);
        showMiniPlayer(track);
        displayTracks();
        
        // Показываем полноэкранный плеер на мобильных
        if (window.innerWidth <= 768) {
            showFullPlayer();
        }
        
    } catch (error) {
        console.error('Playback error:', error);
        showError('Ошибка воспроизведения');
    }
}

// Обновление блока "Сейчас играет"
function updateNowPlaying(track) {
    document.getElementById('currentTitle').textContent = track.title || track.file_name;
    document.getElementById('currentArtist').textContent = track.artist || 'Неизвестный исполнитель';
    
    const isVideo = track.media_type === 'video';
    document.getElementById('mediaIcon').textContent = isVideo ? '🎬' : '🎵';
}

// Обновление отображения текущего трека
function updateNowPlayingDisplay() {
    if (currentTrack) {
        const playPauseBtn = document.getElementById('fullPlayPause');
        if (playPauseBtn) {
            playPauseBtn.textContent = isPlaying ? '⏸' : '▶';
        }
    }
}

// Показ мини-плеера
function showMiniPlayer(track) {
    const miniPlayer = document.getElementById('miniPlayer');
    if (miniPlayer) {
        document.getElementById('miniTitle').textContent = track.title || track.file_name;
        document.getElementById('miniArtist').textContent = track.artist || 'Неизвестный исполнитель';
        miniPlayer.style.display = 'flex';
    }
}

// Переключение воспроизведения
function togglePlay(event) {
    if (event) event.stopPropagation();
    
    if (!currentTrack) {
        if (tracks.length > 0) {
            playTrack(tracks[0].track_id);
        }
        return;
    }
    
    if (isPlaying) {
        audioPlayer.pause();
    } else {
        audioPlayer.play().catch(e => console.log('Play failed:', e));
    }
}

// Следующий трек
function playNext() {
    if (!currentTrack || tracks.length === 0) return;
    
    const currentIndex = tracks.findIndex(t => t.track_id === currentTrack.track_id);
    const nextIndex = (currentIndex + 1) % tracks.length;
    playTrack(tracks[nextIndex].track_id);
}

// Предыдущий трек
function playPrevious() {
    if (!currentTrack || tracks.length === 0) return;
    
    const currentIndex = tracks.findIndex(t => t.track_id === currentTrack.track_id);
    const prevIndex = (currentIndex - 1 + tracks.length) % tracks.length;
    playTrack(tracks[prevIndex].track_id);
}

// Форматирование длительности
function formatDuration(seconds) {
    if (!seconds || seconds === 0) return '--:--';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Обновление прогресса
function updateProgress() {
    const progress = document.getElementById('progress');
    const currentTime = document.getElementById('currentTime');
    const totalTime = document.getElementById('totalTime');
    
    if (progress && currentTime && totalTime) {
        const percent = (audioPlayer.currentTime / audioPlayer.duration) * 100;
        progress.style.width = `${percent}%`;
        
        currentTime.textContent = formatDuration(audioPlayer.currentTime);
        totalTime.textContent = formatDuration(audioPlayer.duration);
    }
}

// Перемотка
function seek(event) {
    const progressBar = document.querySelector('.progress-bar');
    const rect = progressBar.getBoundingClientRect();
    const pos = (event.clientX - rect.left) / rect.width;
    audioPlayer.currentTime = pos * audioPlayer.duration;
}

// Переключение вкладок
function showTab(tabName) {
    currentTab = tabName;
    
    // Обновляем активную кнопку
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.currentTarget.classList.add('active');
    
    // Скрываем все секции
    document.querySelectorAll('.tab-content').forEach(content => {
        content.style.display = 'none';
    });
    
    // Показываем нужную секцию
    const activeSection = document.getElementById(`${tabName}Section`);
    if (activeSection) {
        activeSection.style.display = 'block';
    }
    
    // Загружаем данные для вкладки
    if (tabName === 'playlists') {
        loadPlaylists();
    } else if (tabName === 'tracks') {
        displayTracks();
    }
}

// Загрузка плейлистов
async function loadPlaylists() {
    // Здесь будет загрузка плейлистов
    const playlistsSection = document.getElementById('playlistsSection');
    if (playlistsSection) {
        playlistsSection.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📋</div>
                <div class="empty-text">Плейлистов пока нет</div>
                <button class="create-playlist-btn" onclick="createPlaylist()">
                    + Создать плейлист
                </button>
            </div>
        `;
    }
}

// Создание плейлиста
function createPlaylist() {
    const name = prompt('Введите название плейлиста:');
    if (name) {
        // Здесь будет создание плейлиста
        alert(`Плейлист "${name}" создан!`);
    }
}

// Показать полноэкранный плеер
function showFullPlayer() {
    const fullPlayer = document.getElementById('fullPlayer');
    if (fullPlayer) {
        fullPlayer.style.display = 'flex';
    }
}

// Скрыть полноэкранный плеер
function hideFullPlayer() {
    const fullPlayer = document.getElementById('fullPlayer');
    if (fullPlayer) {
        fullPlayer.style.display = 'none';
    }
}

// Показать загрузку
function showLoading(show) {
    // Реализация индикатора загрузки
}

// Показать ошибку
function showError(message) {
    alert(message);
}

// Обновление кнопок play/pause
function updatePlayButtons(state) {
    const miniPlayPause = document.getElementById('miniPlayPause');
    const fullPlayPause = document.getElementById('fullPlayPause');
    
    if (miniPlayPause) {
        miniPlayPause.textContent = state === 'play' ? '▶' : '⏸';
    }
    if (fullPlayPause) {
        fullPlayPause.textContent = state === 'play' ? '▶' : '⏸';
    }
}

// Переключение повтора
function toggleRepeat() {
    audioPlayer.loop = !audioPlayer.loop;
    const repeatBtn = document.getElementById('repeatBtn');
    if (repeatBtn) {
        repeatBtn.style.opacity = audioPlayer.loop ? '1' : '0.5';
    }
}

// Переключение перемешивания
function toggleShuffle() {
    // Здесь будет логика перемешивания
    const shuffleBtn = document.getElementById('shuffleBtn');
    if (shuffleBtn) {
        const isShuffle = shuffleBtn.style.opacity === '1';
        shuffleBtn.style.opacity = isShuffle ? '0.5' : '1';
    }
}

// Громкость
function setVolume(value) {
    audioPlayer.volume = value / 100;
}

// Глобальные переменные
let playlists = [];
let currentPlaylist = null;

// Загрузка плейлистов
async function loadPlaylists() {
    try {
        const response = await fetch(`/api/playlists/${userId}`);
        playlists = await response.json();
        displayPlaylists();
    } catch (error) {
        console.error('Error loading playlists:', error);
    }
}

// Отображение плейлистов
function displayPlaylists() {
    const playlistsSection = document.getElementById('playlistsSection');
    
    if (playlists.length === 0) {
        playlistsSection.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📋</div>
                <div class="empty-text">У вас нет плейлистов</div>
                <div class="empty-subtext">Создайте плейлист и добавляйте в него треки</div>
                <button class="create-playlist-btn" onclick="showCreatePlaylistDialog()">
                    + Создать плейлист
                </button>
            </div>
        `;
        return;
    }
    
    playlistsSection.innerHTML = `
        <div class="playlists-header">
            <h3>Мои плейлисты</h3>
            <button class="create-playlist-btn" onclick="showCreatePlaylistDialog()">+</button>
        </div>
        <div class="playlists-grid">
            ${playlists.map(playlist => `
                <div class="playlist-card" onclick="showPlaylistDetails(${playlist.playlist_id})">
                    <div class="playlist-cover">📋</div>
                    <div class="playlist-info">
                        <div class="playlist-name">${playlist.name}</div>
                        <div class="playlist-meta">${playlist.tracks_count || 0} треков</div>
                    </div>
                    <button class="playlist-menu-btn" onclick="showPlaylistMenu(${playlist.playlist_id}, event)">⋮</button>
                </div>
            `).join('')}
        </div>
    `;
}

// Показать диалог создания плейлиста
function showCreatePlaylistDialog() {
    const name = prompt('Введите название плейлиста:');
    if (name && name.trim()) {
        createPlaylist(name.trim());
    }
}

// Создание плейлиста
async function createPlaylist(name) {
    try {
        const response = await fetch('/api/playlist/create', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({user_id: userId, name: name})
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                alert(`✅ Плейлист "${name}" создан!`);
                loadPlaylists(); // Перезагружаем список
            }
        }
    } catch (error) {
        console.error('Error creating playlist:', error);
        alert('❌ Ошибка создания плейлиста');
    }
}

// Показать детали плейлиста
async function showPlaylistDetails(playlistId) {
    try {
        const response = await fetch(`/api/playlist/${playlistId}/tracks`);
        const tracks = await response.json();
        
        currentPlaylist = playlists.find(p => p.playlist_id === playlistId);
        
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>${currentPlaylist.name}</h3>
                    <button class="close-modal" onclick="this.closest('.modal').remove()">✕</button>
                </div>
                <div class="modal-body">
                    ${tracks.length === 0 ? `
                        <div class="empty-state">
                            <div class="empty-text">В плейлисте нет треков</div>
                            <div class="empty-subtext">Добавьте треки из общего списка</div>
                        </div>
                    ` : `
                        <div class="tracks-list">
                            ${tracks.map(track => `
                                <div class="track-item playlist-track">
                                    <div class="track-cover-mini">🎵</div>
                                    <div class="track-info">
                                        <div class="track-name">${track.title}</div>
                                        <div class="track-artist">${track.artist}</div>
                                    </div>
                                    <button class="remove-track-btn" onclick="removeFromPlaylist(${playlistId}, ${track.track_id}, event)">✕</button>
                                </div>
                            `).join('')}
                        </div>
                    `}
                    
                    <div class="add-tracks-section">
                        <h4>Добавить треки</h4>
                        <div class="available-tracks">
                            ${tracks.filter(t => !tracks.some(pt => pt.track_id === t.track_id))
                                .map(track => `
                                    <div class="track-item available-track" onclick="addToPlaylist(${playlistId}, ${track.track_id})">
                                        <div class="track-cover-mini">🎵</div>
                                        <div class="track-info">
                                            <div class="track-name">${track.title}</div>
                                            <div class="track-artist">${track.artist}</div>
                                        </div>
                                        <button class="add-track-btn">+</button>
                                    </div>
                                `).join('')}
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="delete-playlist-btn" onclick="deletePlaylist(${playlistId})">Удалить плейлист</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    } catch (error) {
        console.error('Error loading playlist tracks:', error);
    }
}

// Добавление трека в плейлист
async function addToPlaylist(playlistId, trackId) {
    try {
        const response = await fetch(`/api/playlist/${playlistId}/add`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({track_id: trackId})
        });
        
        if (response.ok) {
            alert('✅ Трек добавлен в плейлист');
            // Обновляем отображение
            document.querySelector('.modal').remove();
            showPlaylistDetails(playlistId);
        }
    } catch (error) {
        console.error('Error adding to playlist:', error);
        alert('❌ Ошибка добавления трека');
    }
}

// Удаление трека из плейлиста
async function removeFromPlaylist(playlistId, trackId, event) {
    event.stopPropagation();
    
    if (!confirm('Удалить трек из плейлиста?')) return;
    
    try {
        const response = await fetch(`/api/playlist/${playlistId}/remove`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({track_id: trackId})
        });
        
        if (response.ok) {
            alert('✅ Трек удален из плейлиста');
            // Обновляем отображение
            document.querySelector('.modal').remove();
            showPlaylistDetails(playlistId);
        }
    } catch (error) {
        console.error('Error removing from playlist:', error);
        alert('❌ Ошибка удаления трека');
    }
}

// Удаление плейлиста
async function deletePlaylist(playlistId) {
    if (!confirm('Вы уверены, что хотите удалить плейлист?')) return;
    
    try {
        const response = await fetch(`/api/playlist/${playlistId}/delete`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            alert('✅ Плейлист удален');
            document.querySelector('.modal')?.remove();
            loadPlaylists();
        }
    } catch (error) {
        console.error('Error deleting playlist:', error);
        alert('❌ Ошибка удаления плейлиста');
    }
}

// Показать меню плейлиста
function showPlaylistMenu(playlistId, event) {
    event.stopPropagation();
    // Здесь можно добавить контекстное меню
}

// Переключение треков (предыдущий/следующий)
function playNext() {
    if (!currentTrack || tracks.length === 0) return;
    
    const currentIndex = tracks.findIndex(t => t.track_id === currentTrack.track_id);
    const nextIndex = (currentIndex + 1) % tracks.length;
    playTrack(tracks[nextIndex].track_id);
}

function playPrevious() {
    if (!currentTrack || tracks.length === 0) return;
    
    const currentIndex = tracks.findIndex(t => t.track_id === currentTrack.track_id);
    const prevIndex = (currentIndex - 1 + tracks.length) % tracks.length;
    playTrack(tracks[prevIndex].track_id);
}

// Перемотка
function seek(event) {
    const progressBar = event.currentTarget;
    const rect = progressBar.getBoundingClientRect();
    const pos = (event.clientX - rect.left) / rect.width;
    audioPlayer.currentTime = pos * audioPlayer.duration;
}

// Обработка клавиш
document.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && !e.target.matches('input, textarea')) {
        e.preventDefault();
        togglePlay();
    } else if (e.code === 'ArrowRight') {
        playNext();
    } else if (e.code === 'ArrowLeft') {
        playPrevious();
    }
});

// Инициализация Telegram Bot API
tg.ready();