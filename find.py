import os
import glob
import time

def find_rf60x_temp_files():
    """Поиск временных файлов RF60x-SP"""
    search_paths = [
        os.environ.get('TEMP', ''),
        os.environ.get('TMP', ''),
        'C:\\Users\\*\\AppData\\Local\\Temp',
        'C:\\Temp',
        'C:\\Windows\\Temp',
    ]
    
    # Ищем файлы с расширениями которые могут быть временными
    patterns = ['*.tmp', '*.dat', '*.csv', '*.log', 'rf60x*', '*measure*']
    
    for path in search_paths:
        if not path: continue
        for pattern in patterns:
            search_pattern = os.path.join(path, pattern)
            files = glob.glob(search_pattern)
            for file in files:
                print(f"🔍 Найден: {file}")
                # Проверяем время изменения
                mtime = os.path.getmtime(file)
                if time.time() - mtime < 300:  # Изменен за последние 5 минут
                    print(f"🎯 ВОЗМОЖНО ЭТОТ: {file} (изменен недавно)")

# Запусти поиск
find_rf60x_temp_files()