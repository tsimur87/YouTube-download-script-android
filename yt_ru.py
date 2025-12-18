import yt_dlp
import os
import re
import subprocess
import json
import sys
import signal
import atexit
import traceback
import datetime
import gc  # Garbage Collector для очистки памяти
import time # Для пауз
from pathlib import Path


# === WAKE LOCK ===
wake_lock_active = False

def acquire_wake_lock():
    """Включить wake lock"""
    global wake_lock_active
    try:
        result = subprocess.run(['termux-wake-lock'], capture_output=True, timeout=5)
        if result.returncode == 0:
            wake_lock_active = True
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return False

def release_wake_lock():
    """Отключить wake lock"""
    global wake_lock_active
    if wake_lock_active:
        try:
            subprocess.run(['termux-wake-unlock'], capture_output=True, timeout=5)
            wake_lock_active = False
        except:
            pass

def handle_exit(sig=None, frame=None):
    """Обработка выхода — освобождаем wake lock"""
    release_wake_lock()
    if sig:
        sys.exit(1)

# Регистрируем обработчики
atexit.register(release_wake_lock)
signal.signal(signal.SIGTERM, handle_exit)
signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGHUP, handle_exit)


# === COOKIES ===
def get_cookies_path():
    """Ищет файл cookies.txt рядом со скриптом или в стандартных местах"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [
        os.path.join(script_dir, 'cookies.txt'),
        '/storage/emulated/0/cookies.txt',
        '/storage/emulated/0/Download/cookies.txt',
        '/storage/emulated/0/Downloads/cookies.txt',
        os.path.expanduser('~/cookies.txt'),
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return p
    return None


def sanitize_filename(filename):
    """Очищает имя файла от недопустимых символов."""
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

def extract_chapter_number(filename):
    """Извлекает номер главы из названия файла."""
    patterns = [
        r'^(\d+)\s*[-–—]\s*',  # "01 - название"
        r'^(\d+)\.\s*',         # "01. название"
        r'^\[(\d+)\]',          # "[01] название"
        r'Часть\s*(\d+)',       # "Часть 01"
        r'Part\s*(\d+)',        # "Part 01"
        r'#(\d+)',              # "#01"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            return match.group(1).zfill(2) + " - "
    
    return ""

def clean_filename_from_playlist(filename):
    """Очищает имя файла от префикса плейлиста."""
    name, ext = os.path.splitext(filename)
    chapter_prefix = extract_chapter_number(name)
    
    if " - " in name:
        parts = name.split(" - ", 1)
        if len(parts) > 1:
            if parts[0].strip().isdigit() or re.match(r'^\d+$', parts[0].strip()):
                clean_name = chapter_prefix + parts[1].strip()
            else:
                clean_name = chapter_prefix + parts[1].strip()
        else:
            clean_name = name
    else:
        clean_name = name
    
    return clean_name + ext

def get_android_download_path():
    """Определяет путь для скачивания на Android с проверкой доступности."""
    possible_paths = [
        "/storage/emulated/0/Download",
        "/storage/emulated/0/Downloads", 
        "/sdcard/Download",
        "/sdcard/Downloads",
        os.path.expanduser("~/Downloads"),
        os.getcwd()
    ]
    
    for path in possible_paths:
        try:
            if os.path.exists(path) and os.access(path, os.W_OK):
                return path
        except Exception as e:
            continue
    
    current_dir = os.getcwd()
    download_dir = os.path.join(current_dir, "Downloads")
    try:
        os.makedirs(download_dir, exist_ok=True)
        return download_dir
    except Exception as e:
        return current_dir

def get_numeric_choice(prompt, options, allow_enter_for_default=False, default_index=0):
    """Отображает нумерованный список опций."""
    print(prompt)
    for i, option in enumerate(options):
        if allow_enter_for_default and i == default_index:
            print(f"  {i}) {option} [DEFAULT]")
        else:
            print(f"  {i}) {option}")
    
    while True:
        try:
            choice_str = input("Ваш выбор (номер): ").strip()
            if allow_enter_for_default and not choice_str:
                return default_index
            
            choice = int(choice_str)
            if 0 <= choice < len(options):
                return choice
            else:
                print(f"Неверный номер. Выберите от 0 до {len(options)-1}.")
        except ValueError:
            print("Пожалуйста, введите число.")
        except KeyboardInterrupt:
            print("\nПрерывание пользователем.")
            sys.exit(0)

def load_model_config():
    """Загружает конфигурацию моделей."""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "model_config.json")
        
        if not os.path.exists(config_path):
            return get_default_config()
            
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return get_default_config()

def get_default_config():
    return {
        "arabic": {"default": "openai/whisper-large-v3", "models": ["openai/whisper-large-v3"]},
        "russian": {"default": "openai/whisper-large-v3", "models": ["openai/whisper-large-v3"]},
        "english": {"default": "openai/whisper-large-v3", "models": ["openai/whisper-large-v3"]},
        "turkish": {"default": "openai/whisper-large-v3", "models": ["openai/whisper-large-v3"]},
        "azerbaijani": {"default": "openai/whisper-large-v3", "models": ["openai/whisper-large-v3"]},
    }

def check_dependencies():
    """Проверяет наличие зависимостей."""
    print("Проверка зависимостей...")
    
    try:
        import yt_dlp
        print("✓ yt-dlp найден")
    except ImportError:
        print("✗ yt-dlp не найден. Установите: pip install yt-dlp")
        return False
    
    try:
        # env=os.environ.copy() критически важен для Termux
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, env=os.environ.copy())
        if result.returncode == 0:
            print("✓ ffmpeg найден")
        else:
            print("⚠ ffmpeg найден, но вернул ошибку")
    except FileNotFoundError:
        print("⚠ ffmpeg не найден. Конвертация работать не будет. (pkg install ffmpeg)")
    
    # Проверка cookies
    cookies = get_cookies_path()
    if cookies:
        print(f"✓ cookies.txt найден: {cookies}")
    else:
        print("⚠ cookies.txt не найден (опционально)")
    
    return True

def detect_url_type(url):
    playlist_indicators = ['playlist?list=', '/playlists/', '&list=', '/playlist/']
    for indicator in playlist_indicators:
        if indicator in url.lower():
            return 'playlist'
    return 'video'

def get_base_ydl_opts(cookies_path=None):
    """Базовые опции yt-dlp с cookies и стабильностью"""
    opts = {
        'quiet': True,
        'nocheckcertificate': True,
        'no_warnings': True,
        'socket_timeout': 30,
        'retries': 10,
        'fragment_retries': 10,
        'extractor_retries': 5,
        'file_access_retries': 5,
        'ignoreerrors': True,
    }
    if cookies_path:
        opts['cookiefile'] = cookies_path
    return opts

def get_media_info(url, is_playlist_hint=False, quiet_mode=True, cookies_path=None):
    ydl_opts = {
        'quiet': quiet_mode, 
        'nocheckcertificate': True,
        'no_warnings': True,
        'ignoreerrors': True,
    }
    if is_playlist_hint:
        ydl_opts['extract_flat'] = 'in_playlist'
    if cookies_path:
        ydl_opts['cookiefile'] = cookies_path
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    except Exception as e:
        print(f"Ошибка: {e}")
        return None

def get_video_specific_info(video_url, quiet_mode=True, cookies_path=None):
    ydl_opts = {
        'quiet': quiet_mode, 
        'nocheckcertificate': True, 
        'no_warnings': True,
        'ignoreerrors': True,
    }
    if cookies_path:
        ydl_opts['cookiefile'] = cookies_path
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return info
    except Exception as e:
        print(f"Ошибка при получении информации о видео: {e}")
        return None

def get_quality_format(formats, quality_choice):
    if quality_choice == 0:
        return 'bestvideo+bestaudio/best', None
    elif quality_choice == 1:
        return 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best', None
    elif quality_choice == 2:
        return 'bestvideo[height<=720]+bestaudio/best[height<=720]/best', None
    elif quality_choice == 3:
        return 'bestvideo[height<=360]+bestaudio/best[height<=360]/best', None
    elif quality_choice == 4:
        return 'bestaudio/best', True

def parse_chapters_from_description(description):
    if not description: return []
    chapters = []
    lines = description.split('\n')
    line_counter = 1
    
    for line in lines:
        result = re.search(r"\(?(\d{1,2}[:]?\d{1,2}[:]\d{2})\)?", line)
        if not result: continue
            
        try:
            time_str = result.group(1)
            try:
                time_count = datetime.datetime.strptime(time_str, '%H:%M:%S')
            except ValueError:
                time_count = datetime.datetime.strptime(time_str, '%M:%S')
            
            chap_name = line.replace(result.group(0), "").strip(' :\n-–—')
            if not chap_name: chap_name = f"Часть {line_counter}"
            
            chap_pos = datetime.datetime.strftime(time_count, '%H:%M:%S')
            chapters.append((str(line_counter).zfill(2), chap_pos, chap_name))
            line_counter += 1
        except Exception: continue
    
    return chapters

def parse_time_input(time_str):
    time_str = time_str.strip()
    try:
        if time_str.count(':') == 2:
            time_obj = datetime.datetime.strptime(time_str, '%H:%M:%S')
        elif time_str.count(':') == 1:
            time_obj = datetime.datetime.strptime(time_str, '%M:%S')
        else:
            seconds = int(time_str)
            time_obj = datetime.datetime.strptime(f'00:{seconds}', '%M:%S')
        return datetime.datetime.strftime(time_obj, '%H:%M:%S')
    except Exception: return None

def manual_timecode_input():
    print("\n=== Ручной ввод таймкодов ===")
    print("Формат: ЧЧ:ММ:СС или ММ:СС (примеры: 5:30 или 5:30-10:45)")
    
    while True:
        try:
            input_str = input("\nВведите таймкоды: ").strip()
            if not input_str: return []
            segments = []
            
            if '-' in input_str and ',' not in input_str:
                parts = input_str.split('-')
                if len(parts) == 2:
                    start = parse_time_input(parts[0])
                    end = parse_time_input(parts[1])
                    if start and end:
                        segments.append({'start': start, 'end': end, 'name': f'Отрезок {start}-{end}'})
                        return segments
            
            points = [p.strip() for p in input_str.split(',')]
            parsed_points = []
            for point in points:
                parsed = parse_time_input(point)
                if parsed: parsed_points.append(parsed)
            
            if not parsed_points:
                print("Не удалось распарсить.")
                continue
            
            for i, start_time in enumerate(parsed_points):
                segment = {'start': start_time, 'end': None, 'name': f'Часть {i + 1:02d}'}
                segments.append(segment)
            return segments
        except KeyboardInterrupt: return []
        except Exception as e: print(f"Ошибка: {e}")

def parse_chapter_selection(input_str, total_chapters):
    selected = set()
    try:
        parts = input_str.split(',')
        for part in parts:
            part = part.strip()
            if '-' in part:
                start, end = part.split('-')
                start, end = int(start.strip()), int(end.strip())
                if 1 <= start <= total_chapters and 1 <= end <= total_chapters and start <= end:
                    selected.update(range(start, end + 1))
            else:
                num = int(part)
                if 1 <= num <= total_chapters: selected.add(num)
        return sorted(list(selected))
    except Exception: return []

def get_video_duration(video_path):
    try:
        # Важно: env=os.environ.copy() для Termux
        result = subprocess.run(
            ['ffprobe', '-i', video_path, '-show_entries', 'format=duration', '-v', 'quiet'],
            capture_output=True, text=True, encoding='utf-8', env=os.environ.copy()
        )
        duration_match = re.search(r'duration=(\d+\.?\d*)', result.stdout)
        if duration_match:
            duration_seconds = float(duration_match.group(1))
            m, s = divmod(duration_seconds, 60)
            h, m = divmod(m, 60)
            return ':'.join([str(int(h)), str(int(m)), str(s)])
        return None
    except Exception as e:
        print(f"Ошибка получения длительности: {e}")
        return None

def split_video_by_segments(video_path, segments, output_dir):
    if not segments: return False
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    current_duration = get_video_duration(video_path)
    
    if not current_duration:
        print("Не определена длительность видео.")
        return False
    
    print(f"\nРазделение видео на {len(segments)} частей...")
    successful = 0
    
    for idx, segment in enumerate(segments, 1):
        try:
            start_time = segment['start']
            end_time = segment.get('end', current_duration)
            name = segment.get('name', f'Часть {idx:02d}')
            
            segment_name = sanitize_filename(name)
            output_name = f'{video_name} - {segment_name}.mp4'
            output_path = os.path.join(output_dir, output_name)
            
            print(f"Обработка {idx}/{len(segments)}: {start_time} - {end_time}")
            
            cmd = [
                "ffmpeg", "-ss", start_time, "-to", end_time,
                "-i", video_path,
                "-c", "copy",
                "-avoid_negative_ts", "1",
                output_path
            ]
            
            # env=os.environ.copy()
            result = subprocess.run(cmd, capture_output=True, text=True, env=os.environ.copy())
            
            if result.returncode == 0:
                successful += 1
                print(f"✓ Создан: {output_name}")
            else:
                print(f"✗ Ошибка ffmpeg: {output_name}")
        except Exception as e:
            print(f"✗ Ошибка сегмента {idx}: {e}")
    
    print(f"\nРазделение завершено: {successful}/{len(segments)} успешно")
    return successful > 0

def select_mp3_quality(source_abr=None, auto_best=False):
    qualities = [320, 256, 192, 128, 96, 64, 32, 16]
    if auto_best:
        if source_abr and source_abr > 0:
            for q_val in qualities:
                if source_abr >= q_val:
                    print(f"Авто-выбор MP3: {q_val} kbps")
                    return str(q_val)
            return str(qualities[-1])
        else:
            return str(qualities[0])

    print("\nВыберите качество MP3:")
    for i, q_val in enumerate(qualities):
        print(f"  {i}) {q_val} kbps")
    
    while True:
        try:
            choice = int(input("Ваш выбор: "))
            if 0 <= choice < len(qualities): return str(qualities[choice])
        except ValueError: pass

def run_transcription(mp3_path, language="arabic", model_name="default"):
    """Запускает транскрипцию с защитой от вылетов по памяти."""
    
    # Очистка памяти перед запуском
    gc.collect()
    print(f"\n--- Охлаждение (2 сек) ---")
    time.sleep(2) 

    try:
        print(f"\nЗапуск транскрипции: {os.path.basename(mp3_path)}")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        transcribe_script_path = os.path.join(script_dir, "transcribe.py")

        # Проверка размера файла
        if os.path.exists(mp3_path):
            size_mb = os.path.getsize(mp3_path) / (1024*1024)
            if size_mb > 50:
                print(f"⚠ Файл большой ({int(size_mb)} MB). Возможен вылет на слабых устройствах.")

        if not os.path.exists(transcribe_script_path):
            print(f"Скрипт транскрипции не найден: {transcribe_script_path}")
            return False

        command = [sys.executable, transcribe_script_path, mp3_path, language]
        if model_name != "default":
            command.append(model_name)
        
        # env=os.environ.copy() - критически важно для передачи путей в Termux
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=3600,
            encoding='utf-8',
            errors='replace',
            env=os.environ.copy() 
        )
        
        # Очистка памяти после запуска
        gc.collect()
        
        if result.returncode == 0:
            print("Транскрипция завершена успешно")
            if result.stdout: print("Вывод:", result.stdout[:200] + "...") # Не печатаем весь вывод
            return True
        else:
            print(f"Ошибка транскрипции (код: {result.returncode})")
            if result.returncode == -9:
                print("💥 CRASH: Система убила процесс (нехватка RAM). Попробуйте модель tiny/base.")
            if result.stderr:
                print("Ошибка:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("Транскрипция прервана по таймауту")
        return False
    except Exception as e:
        print(f"Ошибка при запуске транскрипции: {e}")
        return False

def main():
    print("=== YouTube Downloader (Android Fixed) ===")
    
    # Активация wake lock
    print("🔒 Активация wake lock...", end=' ')
    if acquire_wake_lock():
        print("✅")
    else:
        print("⚠️ Недоступен (pkg install termux-api)")
    
    if not check_dependencies(): 
        release_wake_lock()
        return
    
    # Получаем путь к cookies
    cookies_path = get_cookies_path()
    
    try:
        model_configurations = load_model_config()
        url = input("\nВведите ссылку: ").strip()
        if not url: 
            release_wake_lock()
            return

        auto_detected_type = detect_url_type(url)
        print(f"Тип: {'Плейлист' if auto_detected_type == 'playlist' else 'Видео'}")
        
        confirm_choice = get_numeric_choice(
            "Правильно?", ["Да", "Нет, это плейлист", "Нет, это видео"], True, 0
        )
        
        if confirm_choice == 1: url_type = 'playlist'
        elif confirm_choice == 2: url_type = 'video'
        else: url_type = auto_detected_type

        playlist_info = None
        video_info_for_formats = None
        download_title = "YT_Download"
        is_playlist_download = False
        total_items = 1

        if url_type == 'playlist':
            is_playlist_download = True
            print("Анализ плейлиста...")
            playlist_info = get_media_info(url, is_playlist_hint=True, quiet_mode=False, cookies_path=None)
            if not playlist_info or 'entries' not in playlist_info: 
                release_wake_lock()
                return
            
            entries = [e for e in playlist_info['entries'] if e is not None]
            if not entries: 
                release_wake_lock()
                return
            
            download_title = sanitize_filename(playlist_info.get('title', 'YT_Playlist'))
            total_items = len(entries)
            print(f"Плейлист: {download_title} ({total_items} видео)")
            
            # Для плейлиста не получаем форматы первого видео - используем стандартные
            video_info_for_formats = None
            all_formats = []

        else:
            print("Анализ видео...")
            video_info_for_formats = get_media_info(url, quiet_mode=False, cookies_path=None)
            if not video_info_for_formats: 
                release_wake_lock()
                return
            download_title = sanitize_filename(video_info_for_formats.get('title', 'YT_Video'))
            print(f"Видео: {download_title}")
            all_formats = video_info_for_formats.get('formats', [])
        
        print("\nКачество:")
        quality_choice = get_numeric_choice(
            "", ["Авто", "≤ 1080p", "≤ 720p", "≤ 360p", "Только аудио"], True, 0
        )
        
        selected_format, is_audio_only = get_quality_format(all_formats, quality_choice)
        postprocessors_opts = []
        split_mode = False
        cut_segment = None

        if is_audio_only:
            extra_choice = get_numeric_choice(
                "\nДействие с аудио?", ["Скачать", "В MP3"], True, 0
            )
            if extra_choice == 1:
                mp3_quality = select_mp3_quality(auto_best=False)
                postprocessors_opts = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': mp3_quality}]
        else:
            if not is_playlist_download:
                action_choice = get_numeric_choice("\nДействие с видео?", ["Скачать полностью", "Вырезать часть", "Разделить на главы"], True, 0)
                if action_choice == 1:
                    # Вырезать часть видео
                    print("\nФормат времени: ЧЧ:ММ:СС или ММ:СС")
                    cut_start = input("Начало (Enter = с начала): ").strip()
                    cut_end = input("Конец (Enter = до конца): ").strip()
                    
                    if cut_start:
                        cut_start = parse_time_input(cut_start)
                    if cut_end:
                        cut_end = parse_time_input(cut_end)
                    
                    if cut_start or cut_end:
                        split_mode = 'cut'
                        cut_segment = {'start': cut_start or '0:00:00', 'end': cut_end}
                    
                elif action_choice == 2:
                    split_mode = 'chapters'

        start_index = 0
        end_index = None
        if is_playlist_download:
            r_input = input(f"Диапазон (Enter=все, пример 1-5): ").strip()
            if r_input:
                sel = parse_chapter_selection(r_input, total_items)
                if sel:
                    start_index = sel[0] - 1
                    end_index = sel[-1]

        save_dir_base = get_android_download_path()
        save_dir = os.path.join(save_dir_base, download_title)
        try: os.makedirs(save_dir, exist_ok=True)
        except: save_dir = save_dir_base
        
        print(f"\nСохранение в: {save_dir}")

        output_tmpl = '%(title)s'
        if is_playlist_download:
            output_tmpl = f'%(playlist_index)0{len(str(total_items))}d - %(title)s'
        
        # Основные опции БЕЗ cookies - они могут ломать запрос
        ydl_opts = {
            'format': selected_format,
            'outtmpl': os.path.join(save_dir, output_tmpl + '.%(ext)s'),
            'retries': 10,
            'fragment_retries': 20,
            'continuedl': True,
            'nopart': True,
            'postprocessors': postprocessors_opts,
            'quiet': False,
            'nocheckcertificate': True,
            'ignoreerrors': True,
        }

        if is_playlist_download:
            ydl_opts['playliststart'] = start_index + 1
            if end_index: ydl_opts['playlistend'] = end_index
            ydl_opts['noplaylist'] = False
        else:
            ydl_opts['noplaylist'] = True

        if quality_choice < 4 and not postprocessors_opts:
            ydl_opts['merge_output_format'] = 'mp4'

        downloaded_mp3_files = []
        downloaded_video_file = None

        def download_hook(d):
            if d['status'] == 'finished':
                filepath = d.get('filepath') or d.get('filename')
                if not filepath: return
                
                # Короткая пауза для освобождения ресурсов
                time.sleep(0.5) 

                if postprocessors_opts and any(p.get('preferredcodec') == 'mp3' for p in postprocessors_opts):
                    base, _ = os.path.splitext(filepath)
                    mp3_filepath = base + ".mp3"
                    # Логика переименования опущена для краткости, но файлы добавляются
                    downloaded_mp3_files.append(mp3_filepath)
                    print(f"\nГотово: {os.path.basename(mp3_filepath)}")
                else:
                    nonlocal downloaded_video_file
                    downloaded_video_file = filepath
                    print(f"\nГотово: {os.path.basename(filepath)}")
            
            elif d['status'] == 'downloading':
                p = d.get('_percent_str', 'N/A')
                if p != 'N/A': print(f"\rСкачивание: {p}", end='', flush=True)

        ydl_opts['progress_hooks'] = [download_hook]

        print("\nНачинаю скачивание...")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # --- Блок вырезки части видео ---
        if split_mode == 'cut' and downloaded_video_file and cut_segment:
            print("\n=== Вырезка части видео ===")
            start_time = cut_segment['start']
            end_time = cut_segment.get('end')
            
            if not end_time:
                end_time = get_video_duration(downloaded_video_file)
            
            video_name = os.path.splitext(os.path.basename(downloaded_video_file))[0]
            output_name = f'{video_name}_cut.mp4'
            output_path = os.path.join(save_dir, output_name)
            
            print(f"Вырезаю: {start_time} - {end_time}")
            
            cmd = ['ffmpeg', '-y', '-ss', start_time]
            if end_time:
                cmd.extend(['-to', end_time])
            cmd.extend(['-i', downloaded_video_file, '-c', 'copy', '-avoid_negative_ts', '1', output_path])
            
            result = subprocess.run(cmd, capture_output=True, text=True, env=os.environ.copy())
            
            if result.returncode == 0:
                print(f"✓ Создан: {output_name}")
                # Удаляем оригинал, оставляем вырезку
                os.remove(downloaded_video_file)
            else:
                print(f"✗ Ошибка ffmpeg")

        # --- Блок разделения на главы ---
        if split_mode == 'chapters' and downloaded_video_file:
            print("\n=== Разделение на главы ===")
            segments = []
            
            # Попытка авто-поиска глав
            if video_info_for_formats:
                caps = video_info_for_formats.get('chapters', [])
                if caps:
                    for i, c in enumerate(caps, 1):
                        t_str = str(datetime.timedelta(seconds=int(c['start_time'])))
                        segments.append({'start': t_str, 'end': None, 'name': c['title']})
                else:
                    segments = parse_chapters_from_description(video_info_for_formats.get('description', ''))
            
            if not segments:
                print("Главы не найдены.")
                if get_numeric_choice("Ввести вручную?", ["Да", "Нет"], True, 0) == 0:
                    segments = manual_timecode_input()
            
            if segments:
                if len(segments) > 1:
                    sel_in = input("\nВыбрать сегменты (Enter=все): ").strip()
                    if sel_in:
                        inds = parse_chapter_selection(sel_in, len(segments))
                        if inds: segments = [segments[i-1] for i in inds]
                
                # Расчет конца сегментов
                dur_str = get_video_duration(downloaded_video_file)
                for i, s in enumerate(segments):
                    if not s['end']:
                        if i + 1 < len(segments): s['end'] = segments[i+1]['start']
                        else: s['end'] = dur_str
                
                split_video_by_segments(downloaded_video_file, segments, os.path.join(save_dir, "chapters"))

        # Освобождаем wake lock
        release_wake_lock()
        print("\n🔓 Wake lock отключён")
        print("\n=== Готово ===")

    except KeyboardInterrupt:
        print("\nОтменено.")
        release_wake_lock()
    except UnicodeEncodeError:
        print("\nОшибка кодировки консоли (не могу напечатать символ).")
        release_wake_lock()
    except Exception as e:
        print(f"\nКритическая ошибка: {e}")
        traceback.print_exc()
        release_wake_lock()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nОтменено пользователем.")
        release_wake_lock()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        release_wake_lock()
        sys.exit(1)