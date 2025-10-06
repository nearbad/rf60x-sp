# -*- coding: utf-8 -*-
import os
import time
import csv
import datetime

def monitor_rf60x_files():
    """Мониторинг файлов, создаваемых RF60x-SP"""
    print("Мониторинг файлов RF60x-SP...")
    
    # Папка где RF60x-SP сохраняет файлы (измените под ваш путь)
    watch_folder = "C:/Program Files/Riftek/RF60x-SP/Data/"
    output_file = f"rf60x_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    if not os.path.exists(watch_folder):
        print(f"Папка {watch_folder} не найдена!")
        return
    
    print(f"📁 Мониторю папку: {watch_folder}")
    print(f"💾 Экспорт в: {output_file}")
    print("Нажмите Ctrl+C для остановки")
    
    processed_files = set()
    
    try:
        while True:
            # Ищем новые файлы
            for filename in os.listdir(watch_folder):
                if filename.endswith('.csv') and filename not in processed_files:
                    filepath = os.path.join(watch_folder, filename)
                    print(f"📨 Обнаружен новый файл: {filename}")
                    
                    # Копируем данные
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f_in:
                            with open(output_file, 'a', newline='', encoding='utf-8') as f_out:
                                reader = csv.reader(f_in)
                                writer = csv.writer(f_out)
                                
                                # Если файл пустой, добавляем заголовок
                                if os.path.getsize(output_file) == 0:
                                    writer.writerow(['SourceFile', 'Timestamp', 'Data'])
                                
                                for row in reader:
                                    writer.writerow([filename, datetime.datetime.now().isoformat()] + row)
                        
                        processed_files.add(filename)
                        print(f"✅ Файл {filename} обработан")
                        
                    except Exception as e:
                        print(f"❌ Ошибка обработки {filename}: {e}")
            
            time.sleep(5)  # Проверка каждые 5 секунд
            
    except KeyboardInterrupt:
        print(f"\nОстановлено. Обработано файлов: {len(processed_files)}")

if __name__ == "__main__":
    monitor_rf60x_files()