# -*- coding: utf-8 -*-
import serial
import serial.tools.list_ports
import csv
import datetime
import time
import struct

class RF60xReader:
    def __init__(self, sensor_range_mm=250):
        self.ser = None
        self.sensor_range_mm = sensor_range_mm  # Диапазон датчика в мм
        
    def connect(self, port='COM3', baudrate=921600):
        """Подключение к датчику RF60x"""
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            print(f"✅ Подключено к {port} на скорости {baudrate}")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False
    
    def send_command(self, command_code, address=1):
        """Отправка команды датчику по протоколу RF60x"""
        try:
            # Формат запроса: [ADR(7:0), 1|0|0|0|COD(3:0)]
            # Байт 0: адрес устройства (старший бит = 0)
            # Байт 1: старший бит = 1, затем 000, затем код команды
            inc0 = address & 0x7F  # Адрес (бит 7 всегда 0)
            inc1 = 0x80 | (command_code & 0x0F)  # Старший бит = 1, код команды
            
            cmd_bytes = bytes([inc0, inc1])
            print(f"🔄 Отправка команды: {cmd_bytes.hex()} (код: {command_code:02X}h)")
            
            self.ser.write(cmd_bytes)
            self.ser.flush()
            return True
            
        except Exception as e:
            print(f"❌ Ошибка отправки команды: {e}")
            return False
    
    def parse_rf60x_response(self, data):
        """Парсинг ответа от датчика RF60x"""
        if len(data) < 4:
            return None
            
        try:
            # Формат ответа: 4 байта на измерение
            # Каждый байт имеет формат: 1, SB, CNT[1:0], DATA[3:0]
            bytes_list = list(data)
            
            # Проверяем что все байты имеют старший бит = 1
            if not all(b & 0x80 for b in bytes_list[:4]):
                return None
            
            # Извлекаем данные из каждого байта (младшие 4 бита)
            d0 = bytes_list[0] & 0x0F  # Младшая тетрада младшего байта
            d1 = bytes_list[1] & 0x0F  # Старшая тетрада младшего байта  
            d2 = bytes_list[2] & 0x0F  # Младшая тетрада старшего байта
            d3 = bytes_list[3] & 0x0F  # Старшая тетрада старшего байта
            
            # Собираем 16-битное значение
            low_byte = (d1 << 4) | d0
            high_byte = (d3 << 4) | d2
            raw_value = (high_byte << 8) | low_byte
            
            # Преобразуем в миллиметры по формуле из документации
            # X = D * S / 4000h (где 4000h = 16384)
            measurement = raw_value * self.sensor_range_mm / 16384.0
            
            return measurement
            
        except Exception as e:
            print(f"❌ Ошибка парсинга данных: {e}")
            return None
    
    def start_stream(self):
        """Запуск потока данных (команда 07h)"""
        return self.send_command(0x07)
    
    def stop_stream(self):
        """Остановка потока данных (команда 08h)"""
        return self.send_command(0x08)
    
    def single_measurement(self):
        """Одиночное измерение (команда 06h)"""
        return self.send_command(0x06)
    
    def read_data_stream(self, filename):
        """Чтение потока данных от датчика"""
        print("📡 Начало чтения потока данных...")
        count = 0
        
        # Создание CSV файла
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'DateTime', 'Measurement_mm', 'RawData_Hex'])
        
        buffer = b''
        last_print_time = time.time()
        
        try:
            while True:
                if self.ser.in_waiting > 0:
                    # Читаем все доступные данные
                    data = self.ser.read(self.ser.in_waiting)
                    buffer += data
                    
                    # Обрабатываем полные пакеты по 4 байта
                    while len(buffer) >= 4:
                        packet = buffer[:4]
                        buffer = buffer[4:]
                        
                        measurement = self.parse_rf60x_response(packet)
                        timestamp = time.time()
                        dt_string = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                        
                        if measurement is not None:
                            # Запись в файл
                            with open(filename, 'a', newline='', encoding='utf-8') as f:
                                writer = csv.writer(f)
                                writer.writerow([timestamp, dt_string, f"{measurement:.3f}", packet.hex()])
                            
                            count += 1
                            
                            # Вывод каждые 10 измерений или каждую секунду
                            if count % 10 == 0 or time.time() - last_print_time >= 1:
                                print(f"📊 #{count}: {measurement:.3f} mm")
                                last_print_time = time.time()
                        else:
                            # Вывод сырых данных для отладки
                            if time.time() - last_print_time >= 2:
                                print(f"📦 Неразобранные данные: {packet.hex()}")
                                last_print_time = time.time()
                
                time.sleep(0.001)  # Короткая пауза
                
        except KeyboardInterrupt:
            print(f"\n⏹ Остановлено. Всего собрано: {count} измерений")
        except Exception as e:
            print(f"❌ Ошибка чтения: {e}")
    
    def close(self):
        """Закрытие соединения"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("🔌 Порт закрыт")

def select_com_port():
    """Выбор COM-порта"""
    print("Поиск COM-портов...")
    ports = serial.tools.list_ports.comports()
    
    if not ports:
        print("COM-порты не найдены!")
        return None
    
    print("Найденные порты:")
    for i, port in enumerate(ports):
        print(f"{i+1}. {port.device} - {port.description}")
    
    try:
        choice = input("Выберите номер порта: ")
        port_index = int(choice) - 1
        selected_port = ports[port_index].device
        return selected_port
    except:
        selected_port = input("Введите название порта (например COM3): ")
        return selected_port

def main():
    print("RF60x Data Logger - Правильный протокол")
    print("=" * 60)
    
    # Выбор порта
    port = select_com_port()
    if not port:
        return
    
    # Настройки датчика
    try:
        sensor_range = float(input("Введите диапазон датчика в мм (по умолчанию 250): ") or "250")
    except:
        sensor_range = 250
        print(f"Используется диапазон по умолчанию: {sensor_range} мм")
    
    reader = RF60xReader(sensor_range_mm=sensor_range)
    
    if reader.connect(port, 921600):
        # Даем время на инициализацию
        time.sleep(1)
        
        # Очищаем буфер
        reader.ser.reset_input_buffer()
        
        # Запускаем поток данных
        if reader.start_stream():
            print("✅ Поток данных запущен")
            
            # Начинаем чтение
            filename = f"rf60x_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            print(f"💾 Запись в файл: {filename}")
            print("🎯 Наведите датчик на объект для измерений")
            print("⏹ Нажмите Ctrl+C для остановки")
            print("-" * 60)
            
            reader.read_data_stream(filename)
            
            # Останавливаем поток после завершения
            reader.stop_stream()
        else:
            print("❌ Не удалось запустить поток данных")
    
    reader.close()

if __name__ == "__main__":
    main()