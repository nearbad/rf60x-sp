# -*- coding: utf-8 -*-
import serial
import csv
import datetime
import time
import struct
import binascii

class RF60xBinaryReader:
    def __init__(self):
        self.ser = None
        
    def connect(self, port='COM3', baudrate=921600):
        """Подключение к датчику"""
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
    
    def send_binary_command(self, command_bytes):
        """Отправка бинарной команды"""
        try:
            print(f"🔄 Отправка команды: {command_bytes.hex()}")
            self.ser.write(command_bytes)
            self.ser.flush()
            time.sleep(0.1)
            
            # Читаем ответ
            if self.ser.in_waiting > 0:
                response = self.ser.read(self.ser.in_waiting)
                print(f"   📨 Ответ: {response.hex()}")
                return response
            return None
        except Exception as e:
            print(f"❌ Ошибка отправки команды: {e}")
            return None
    
    def parse_measurement_data(self, data):
        """Парсинг данных измерения из RF60x"""
        if len(data) < 4:
            return None
            
        try:
            # RF60x обычно использует 4-байтовый float в little-endian
            measurement = struct.unpack('<f', data[:4])[0]
            
            # Проверяем разумные пределы (0-300mm по настройкам)
            if 0 <= measurement <= 300:
                return measurement
                
            # Если значение вне диапазона, пробуем big-endian
            measurement = struct.unpack('>f', data[:4])[0]
            if 0 <= measurement <= 300:
                return measurement
                
        except:
            pass
            
        return None
    
    def start_continuous_measurement(self):
        """Запуск непрерывных измерений"""
        # Бинарные команды для RF60x (могут отличаться в зависимости от прошивки)
        commands = [
            b'\x01',  # Старт измерений
            b'\x02',  # Непрерывный режим
            b'\x53',  # 'S' - Start
            b'\x4D',  # 'M' - Measure
            b'\x52',  # 'R' - Read
        ]
        
        for cmd in commands:
            response = self.send_binary_command(cmd)
            if response and len(response) >= 4:
                measurement = self.parse_measurement_data(response)
                if measurement is not None:
                    print(f"🎯 Измерение получено: {measurement:.3f} mm")
                    return True
                    
        return False
    
    def read_continuous_data(self, filename):
        """Чтение непрерывных данных"""
        print("📡 Чтение данных...")
        count = 0
        
        # Создание файла
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'DateTime', 'Measurement_mm', 'RawData', 'DataLength'])
        
        last_data_time = time.time()
        data_timeout = 5  # Таймаут в секундах
        
        try:
            while True:
                if self.ser.in_waiting > 0:
                    # Читаем все доступные данные
                    data = self.ser.read(self.ser.in_waiting)
                    last_data_time = time.time()
                    
                    # Пробуем разные длины пакетов
                    packet_sizes = [4, 8, 16, 32]
                    
                    for size in packet_sizes:
                        if len(data) >= size:
                            # Пробуем каждые size байт как измерение
                            for i in range(0, len(data) - size + 1, size):
                                packet = data[i:i+size]
                                measurement = self.parse_measurement_data(packet)
                                
                                if measurement is not None:
                                    timestamp = time.time()
                                    dt_string = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                                    
                                    # Запись в файл
                                    with open(filename, 'a', newline='', encoding='utf-8') as f:
                                        writer = csv.writer(f)
                                        writer.writerow([timestamp, dt_string, measurement, packet.hex(), len(packet)])
                                    
                                    count += 1
                                    print(f"📊 #{count}: {measurement:.3f} mm (пакет {len(packet)} байт)")
                                    break
                            
                            # Если нашли измерения, выходим из цикла по размерам
                            if count > 0:
                                break
                    
                    # Если не нашли измерений, выводим сырые данные для отладки
                    if count == 0:
                        print(f"📦 Сырые данные ({len(data)} байт): {data.hex()}")
                        
                        # Пробуем распарсить как текст
                        try:
                            text = data.decode('ascii', errors='ignore').strip()
                            if text:
                                print(f"   Как текст: '{text}'")
                        except:
                            pass
                
                # Проверка таймаута
                if time.time() - last_data_time > data_timeout:
                    print("⏰ Таймаут, данных нет. Пробуем переотправить команду...")
                    self.start_continuous_measurement()
                    last_data_time = time.time()
                
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print(f"\n⏹ Остановлено. Всего собрано: {count} измерений")
        except Exception as e:
            print(f"❌ Ошибка чтения: {e}")
    
    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("🔌 Порт закрыт")

def main():
    print("RF60x Binary Protocol Reader")
    print("=" * 50)
    
    reader = RF60xBinaryReader()
    
    if reader.connect('COM3', 921600):
        time.sleep(1)
        reader.ser.reset_input_buffer()
        
        # Запускаем измерения
        if reader.start_continuous_measurement():
            filename = f"rf60x_binary_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            print(f"💾 Запись в файл: {filename}")
            print("🎯 Наведите датчик на объект")
            print("⏹ Ctrl+C для остановки")
            print("-" * 50)
            
            reader.read_continuous_data(filename)
        else:
            print("❌ Не удалось запустить измерения")
            print("🔍 Попробуем прослушать порт без команд...")
            filename = f"rf60x_listen_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            reader.read_continuous_data(filename)
    
    reader.close()

if __name__ == "__main__":
    main()