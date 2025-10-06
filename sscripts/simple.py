# -*- coding: utf-8 -*-
import serial
import serial.tools.list_ports
import csv
import datetime
import time

print("RF60x Simple Data Logger")
print("=" * 40)

# Поиск COM-портов
print("Поиск COM-портов...")
ports = serial.tools.list_ports.comports()

if not ports:
    print("COM-порты не найдены!")
    exit()

print("Найденные порты:")
for i, port in enumerate(ports):
    print(f"{i+1}. {port.device} - {port.description}")

# Выбор порта
try:
    choice = input("Выберите номер порта: ")
    port_index = int(choice) - 1
    selected_port = ports[port_index].device
except:
    selected_port = input("Введите название порта (например COM3): ")

# Настройки
baudrate = 921600
filename = "rf60x_data_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv"

print(f"Порт: {selected_port}")
print(f"Скорость: {baudrate}")
print(f"Файл: {filename}")
print("Нажмите Ctrl+C для остановки")

try:
    # Подключение к порту
    ser = serial.Serial(
        port=selected_port,
        baudrate=baudrate,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=1
    )
    
    # Создание CSV файла
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Timestamp', 'DateTime', 'Measurement'])
    
    print("Сбор данных начат...")
    count = 0
    
    while True:
        if ser.in_waiting > 0:
            # Чтение данных
            data = ser.readline()
            
            try:
                # Пробуем прочитать как текст
                text = data.decode('ascii').strip()
                # Очищаем от лишних символов
                cleaned = ''.join(c for c in text if c.isdigit() or c in '.-')
                
                if cleaned:
                    measurement = float(cleaned)
                    timestamp = time.time()
                    dt_string = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Запись в файл
                    with open(filename, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow([timestamp, dt_string, measurement])
                    
                    count += 1
                    if count % 10 == 0:
                        print(f"Собрано измерений: {count}")
                        
            except:
                # Если не текст, пробуем как бинарные данные
                print(f"Бинарные данные: {data.hex()}")
                
        time.sleep(0.01)
        
except KeyboardInterrupt:
    print(f"\nОстановлено. Всего собрано: {count} измерений")
except Exception as e:
    print(f"Ошибка: {e}")
finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("Порт закрыт")