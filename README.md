# YT Downloader for Android (Termux)

YouTube video/playlist downloader for Android with video cutting and chapter splitting support.

## Features

- 📱 Works on Android via Termux
- 📋 Download playlists or single videos
- 🎵 Extract audio to MP3
- ✂️ Cut specific part of video (start/end time)
- 📑 Split video by chapters
- 🔒 Wake lock prevents phone from sleeping
- 📂 Auto-detection of playlist/video

## Installation

### 1. Install Termux

Download from [F-Droid](https://f-droid.org/packages/com.termux/) (recommended) or Play Store.

### 2. Install dependencies

```bash
pkg update && pkg upgrade
pkg install python ffmpeg
pip install yt-dlp
```

### 3. Optional: Install deno for better YouTube support

```bash
pkg install deno
```

### 4. Download script

```bash
curl -o ~/yt.py https://raw.githubusercontent.com/YOUR_USERNAME/yt-downloader/main/yt.py
```

Or copy `yt.py` to your phone storage.

### 5. Grant storage permission

```bash
termux-setup-storage
```

## Usage

```bash
python ~/yt.py
```

Or if script is in storage:

```bash
python /storage/emulated/0/yt.py
```

### Menu Options

**Quality:**

- Auto (best)
- ≤ 1080p
- ≤ 720p
- ≤ 360p
- Audio only

**For single video:**

- Download full
- Cut part (specify start/end time)
- Split by chapters

**For audio:**

- Download original
- Convert to MP3

### Time Format

When cutting video, use: `HH:MM:SS` or `MM:SS`

- Start: `5:30` (from 5 min 30 sec)
- End: `15:45` (to 15 min 45 sec)
- Press Enter for "from beginning" or "to end"

## Add to Termux Widget

```bash
mkdir -p ~/.shortcuts
echo '#!/bin/bash
python /storage/emulated/0/yt.py' > ~/.shortcuts/yt
chmod +x ~/.shortcuts/yt
```

Install Termux:Widget app from F-Droid and add widget to home screen.

## Troubleshooting

**"Requested format is not available"**

- Update yt-dlp: `pip install -U yt-dlp`
- Install deno: `pkg install deno`

**Script crashes / phone sleeps**

- Wake lock should activate automatically
- Install: `pkg install termux-api`
- Also install Termux:API app from F-Droid

**Permission denied**

```bash
termux-setup-storage
```

## License

MIT

---

# YT Downloader для Android (Termux)

Скачивание видео/плейлистов YouTube для Android с поддержкой вырезки и разделения на главы.

## Возможности

- 📱 Работает на Android через Termux
- 📋 Скачивание плейлистов и одиночных видео
- 🎵 Извлечение аудио в MP3
- ✂️ Вырезка части видео (начало/конец)
- 📑 Разделение видео по главам
- 🔒 Wake lock не даёт телефону уснуть
- 📂 Автоопределение плейлист/видео

## Установка

### 1. Установи Termux

Скачай с [F-Droid](https://f-droid.org/packages/com.termux/) (рекомендуется) или Play Store.

### 2. Установи зависимости

```bash
pkg update && pkg upgrade
pkg install python ffmpeg
pip install yt-dlp
```

### 3. Опционально: установи deno для лучшей поддержки YouTube

```bash
pkg install deno
```

### 4. Скачай скрипт

```bash
curl -o ~/yt.py https://raw.githubusercontent.com/YOUR_USERNAME/yt-downloader/main/yt.py
```

Или скопируй `yt.py` в память телефона.

### 5. Дай доступ к хранилищу

```bash
termux-setup-storage
```

## Использование

```bash
python ~/yt.py
```

Или если скрипт в хранилище:

```bash
python /storage/emulated/0/yt.py
```

### Опции меню

**Качество:**

- Авто (лучшее)
- ≤ 1080p
- ≤ 720p
- ≤ 360p
- Только аудио

**Для одиночного видео:**

- Скачать полностью
- Вырезать часть (указать начало/конец)
- Разделить по главам

**Для аудио:**

- Скачать оригинал
- Конвертировать в MP3

### Формат времени

При вырезке используй: `ЧЧ:ММ:СС` или `ММ:СС`

- Начало: `5:30` (с 5 мин 30 сек)
- Конец: `15:45` (до 15 мин 45 сек)
- Enter = "с начала" или "до конца"

## Добавить в виджет Termux

```bash
mkdir -p ~/.shortcuts
echo '#!/bin/bash
python /storage/emulated/0/yt.py' > ~/.shortcuts/yt
chmod +x ~/.shortcuts/yt
```

Установи приложение Termux:Widget из F-Droid и добавь виджет на рабочий стол.

## Решение проблем

**"Requested format is not available"**

- Обнови yt-dlp: `pip install -U yt-dlp`
- Установи deno: `pkg install deno`

**Скрипт вылетает / телефон засыпает**

- Wake lock должен включаться автоматически
- Установи: `pkg install termux-api`
- Также установи приложение Termux:API из F-Droid

**Permission denied**

```bash
termux-setup-storage
```

## Лицензия

MIT
