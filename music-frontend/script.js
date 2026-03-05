// Конфигурация
const API_URL = 'https://music-bot-backend-ng9f.onrender.com';
// Для локальной разработки раскомментируйте:
// const API_URL = 'http://localhost:5000';

// Состояние плеера
let currentTrack = null;
let tracks = [];
let audio = new Audio();

// DOM элементы
const searchInput = document.getElementById('search-input');
const searchBtn = document.getElementById('search-btn');
const tracksList = document.getElementById('tracks-list');
const playPauseBtn = document.getElementById('play-pause');
const prevBtn = document.getElementById('prev');
const nextBtn = document.getElementById('next');
const volumeSlider = document.getElementById('volume');
const currentTimeEl = document.getElementById('current-time');
const durationEl = document.getElementById('duration');
const progressBar = document.querySelector('.progress');
const trackTitle = document.getElementById('track-title');
const trackArtist = document.getElementById('track-artist');
const albumArt = document.getElementById('album-art');

// Загрузка треков при старте
async function loadTracks() {
    try {
        const response = await fetch(`${API_URL}/tracks`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        tracks = await response.json();
        displayTracks(tracks);
    } catch (error) {
        console.error('Ошибка загрузки треков:', error);
        tracksList.innerHTML = '<div class="error">Ошибка загрузки треков</div>';
    }
}

// Отображение треков
function displayTracks(tracksToShow) {
    tracksList.innerHTML = '';
    
    if (!tracksToShow || tracksToShow.length === 0) {
        tracksList.innerHTML = '<div class="loading">Треки не найдены</div>';
        return;
    }
    
    tracksToShow.forEach(track => {
        const trackElement = document.createElement('div');
        trackElement.className = 'track-item';
        if (currentTrack && currentTrack.id === track.id) {
            trackElement.classList.add('active');
        }
        
        trackElement.innerHTML = `
            <img src="${track.cover_url || 'https://via.placeholder.com/50'}" alt="cover">
            <div class="track-info">
                <div class="track-title">${track.title}</div>
                <div class="track-artist">${track.artist}</div>
            </div>
            <div class="track-duration">${formatTime(track.duration)}</div>
        `;
        
        trackElement.addEventListener('click', () => playTrack(track));
        tracksList.appendChild(trackElement);
    });
}

// Поиск треков
async function searchTracks() {
    const query = searchInput.value.trim();
    
    if (!query) {
        displayTracks(tracks);
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/search?q=${encodeURIComponent(query)}`);
        const results = await response.json();
        displayTracks(results);
    } catch (error) {
        console.error('Ошибка поиска:', error);
    }
}

// Воспроизведение трека
async function playTrack(track) {
    try {
        if (currentTrack && currentTrack.id === track.id) {
            togglePlay();
            return;
        }
        
        currentTrack = track;
        trackTitle.textContent = track.title;
        trackArtist.textContent = track.artist;
        albumArt.src = track.cover_url || 'https://via.placeholder.com/300';
        
        audio.src = `${API_URL}/track/${track.id}/play`;
        audio.load();
        
        await audio.play();
        updatePlayPauseButton(true);
        
        // Обновляем активный трек в списке
        document.querySelectorAll('.track-item').forEach(item => {
            item.classList.remove('active');
        });
        event.currentTarget.classList.add('active');
        
    } catch (error) {
        console.error('Ошибка воспроизведения:', error);
    }
}

// Переключение воспроизведения
function togglePlay() {
    if (!currentTrack) return;
    
    if (audio.paused) {
        audio.play();
        updatePlayPauseButton(true);
    } else {
        audio.pause();
        updatePlayPauseButton(false);
    }
}

// Обновление кнопки play/pause
function updatePlayPauseButton(isPlaying) {
    playPauseBtn.innerHTML = isPlaying ? '⏸️' : '▶️';
}

// Предыдущий трек
function prevTrack() {
    if (!tracks.length || !currentTrack) return;
    
    const currentIndex = tracks.findIndex(t => t.id === currentTrack.id);
    const prevIndex = currentIndex > 0 ? currentIndex - 1 : tracks.length - 1;
    playTrack(tracks[prevIndex]);
}

// Следующий трек
function nextTrack() {
    if (!tracks.length || !currentTrack) return;
    
    const currentIndex = tracks.findIndex(t => t.id === currentTrack.id);
    const nextIndex = currentIndex < tracks.length - 1 ? currentIndex + 1 : 0;
    playTrack(tracks[nextIndex]);
}

// Форматирование времени
function formatTime(seconds) {
    if (!seconds || isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Обновление прогресса
function updateProgress() {
    if (audio.duration) {
        const progress = (audio.currentTime / audio.duration) * 100;
        progressBar.style.width = `${progress}%`;
        currentTimeEl.textContent = formatTime(audio.currentTime);
        durationEl.textContent = formatTime(audio.duration);
    }
}

// Обработчики событий аудио
audio.addEventListener('timeupdate', updateProgress);
audio.addEventListener('ended', nextTrack);
audio.addEventListener('loadedmetadata', () => {
    durationEl.textContent = formatTime(audio.duration);
});

// Обработчики событий интерфейса
searchBtn.addEventListener('click', searchTracks);
searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') searchTracks();
});

playPauseBtn.addEventListener('click', togglePlay);
prevBtn.addEventListener('click', prevTrack);
nextBtn.addEventListener('click', nextTrack);

volumeSlider.addEventListener('input', (e) => {
    audio.volume = e.target.value / 100;
});

// Клик по прогресс-бару
document.querySelector('.progress-bar').addEventListener('click', (e) => {
    if (!audio.duration) return;
    
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const width = rect.width;
    const percentage = x / width;
    
    audio.currentTime = percentage * audio.duration;
});

// Загружаем треки при старте
loadTracks();