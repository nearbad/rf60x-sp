# -*- coding: utf-8 -*-
import serial
import serial.tools.list_ports
import csv
import datetime
import time
import sys

def check_port_availability(port_name):
    """Проверка доступности порта"""
    try:
        # Быстрая проверка без длительного timeout
        ser = serial.Serial(port_name, timeout=0.1)
        ser.close()
        return True
    except:
        return False

def wait_for_port(port_name, max_attempts=10):
    """Ожидание освобождения порта"""
    print(f"Ожидание освобождения порта {port_name}...")
    for attempt in range(max_attempts):
        if check_port_availability(port_name):
            print(f"✅ Порт {port_name} доступен!")
            return True
        print(f"  Попытка {attempt + 1}/{max_attempts}...")
        time.sleep(1)
    return False

def main():
    print("RF60x Improved Data Logger")
    print("=" * 50)
    
    # Поиск портов
    print("Поиск COM-портов...")
    ports = list(serial.tools.list_ports.comports())
    
    if not ports:
        print("COM-порты не найдены!")
        return
    
    print("Найденные порты:")
    for i, port in enumerate(ports):
        print(f"{i+1}. {port.device} - {port.description}")
    
    # Выбор порта
    try:
        choice = input("Выберите номер порта: ")
        port_index = int(choice) - 1
        selected_port = ports[port_index].device
    except:
        selected_port = input("Введите название порта (COM3): ").strip()
    
    # Ожидание освобождения порта
    if not wait_for_port(selected_port):
        print(f"❌ Порт {selected_port} занят! Закройте другие программы.")
        input("Нажмите Enter после закрытия других программ...")
    
    # Настройки
    baudrate = 9600
    filename = f"rf60x_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    print(f"Настройки:")
    print(f"  Порт: {selected_port}")
    print(f"  Скорость: {baudrate}")
    print(f"  Файл: {filename}")
    print("  Нажмите Ctrl+C для остановки")
    print("-" * 50)
    
    try:
        # Подключение с обработкой ошибок
        print("Подключение к порту...")
        ser = serial.Serial(
            port=selected_port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1
        )
        
        print("✅ Успешное подключение!")
        
        # Создание файла
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'DateTime', 'Measurement', 'RawData'])
        
        print("Сбор данных начат...")
        count = 0
        
        while True:
            if ser.in_waiting > 0:
                data = ser.readline()
                
                try:
                    # Пробуем прочитать как текст
                    text = data.decode('ascii').strip()
                    cleaned = ''.join(c for c in text if c.isdigit() or c in '.-')
                    
                    if cleaned:
                        measurement = float(cleaned)
                        timestamp = time.time()
                        dt_string = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        # Запись в файл
                        with open(filename, 'a', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow([timestamp, dt_string, measurement, data.hex()])
                        
                        count += 1
                        if count % 10 == 0:
                            print(f"Собрано измерений: {count}")
                            
                except Exception as e:
                    print(f"Бинарные данные: {data.hex()}")
                    
            time.sleep(0.01)
            
    except serial.SerialException as e:
        print(f"❌ Ошибка подключения: {e}")
        print("\nВозможные причины:")
        print("1. Порт занят другой программой")
        print("2. Неправильные настройки порта")
        print("3. Проблемы с драйвером")
        print("\nРешение:")
        print("- Закройте RF60x-SP, Putty и другие терминальные программы")
        print("- Перезагрузите компьютер")
        print("- Проверьте драйвер устройства")
        
    except KeyboardInterrupt:
        print(f"\n⏹ Остановлено. Всего собрано: {count} измерений")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("🔌 Порт закрыт")

if __name__ == "__main__":
    main()