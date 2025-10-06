# -*- coding: utf-8 -*-
import serial
import csv
import datetime
import time

def main():
    print("RF60x Data Logger from Virtual Port")
    print("=" * 50)
    print("Эта программа читает данные с виртуального COM5")
    print("Убедитесь, что запущен мост COM3→COM4")
    print("=" * 50)
    
    # Виртуальный порт для нашей программы
    VIRTUAL_PORT = "COM5"
    BAUDRATE = 9600
    FILENAME = f"rf60x_virtual_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    try:
        print(f"Подключение к {VIRTUAL_PORT}...")
        ser = serial.Serial(VIRTUAL_PORT, BAUDRATE, timeout=1)
        print("✅ Успешное подключение к виртуальному порту!")
        
        # Создание файла
        with open(FILENAME, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'DateTime', 'Measurement', 'RawData'])
        
        print(f"📄 Файл: {FILENAME}")
        print("Сбор данных начат... (Ctrl+C для остановки)")
        print("-" * 50)
        
        count = 0
        
        while True:
            if ser.in_waiting > 0:
                data = ser.readline()
                
                try:
                    # Парсинг ASCII данных
                    text = data.decode('ascii').strip()
                    cleaned = ''.join(c for c in text if c.isdigit() or c in '.-')
                    
                    if cleaned:
                        measurement = float(cleaned)
                        timestamp = time.time()
                        dt_string = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        # Запись в файл
                        with open(FILENAME, 'a', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow([timestamp, dt_string, measurement, data.hex()])
                        
                        count += 1
                        if count % 10 == 0:
                            print(f"📊 Собрано: {count} измерений - {measurement}")
                            
                except Exception as e:
                    print(f"📦 Сырые данные: {data.hex()}")
                    
            time.sleep(0.01)
            
    except serial.SerialException as e:
        print(f"❌ Ошибка подключения: {e}")
        print("\nРешения:")
        print("1. Запустите com3_bridge.py сначала")
        print("2. Проверьте настройки com0com")
        print("3. Убедитесь, что COM5 свободен")
        
    except KeyboardInterrupt:
        print(f"\n⏹ Остановлено. Всего: {count} измерений")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("🔌 Порт закрыт")

if __name__ == "__main__":
    main()