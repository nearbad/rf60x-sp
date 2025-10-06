# -*- coding: utf-8 -*-
import serial
import csv
import datetime
import time
import struct

class RF60xReader:
    def __init__(self):
        self.ser = None
        
    def connect(self, port='COM3', baudrate=921600):
        """Подключение с правильными настройками из RF60x-SP"""
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
    
    def send_start_command(self):
        """Отправка команды Start (как в RF60x-SP)"""
        try:
            # Пробуем разные варианты команды Start
            commands = [
                b'Start\r\n',      # Текстовая команда
                b'START\r\n',      # В верхнем регистре
                b'\x01',           # Бинарная команда
                b'\x02',           # Другая бинарная команда
            ]
            
            for cmd in commands:
                print(f"🔄 Отправка команды: {cmd} (hex: {cmd.hex()})")
                self.ser.write(cmd)
                self.ser.flush()
                time.sleep(0.5)
                
                # Проверяем ответ
                if self.ser.in_waiting > 0:
                    response = self.ser.read(self.ser.in_waiting)
                    print(f"   ✅ Получен ответ: {response.hex()}")
                    return True
            
            # Если нет ответа, все равно продолжаем (возможно данные идут без команды)
            print("⚠️  Команда не дала ответа, продолжаем чтение...")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка отправки команды: {e}")
            return False
    
    def parse_rf60x_data(self, data):
        """Парсинг данных RF60x в правильном формате"""
        try:
            # Вариант 1: ASCII данные (например: "123.45")
            text = data.decode('ascii').strip()
            cleaned = ''.join(c for c in text if c.isdigit() or c in '.-')
            if cleaned:
                return float(cleaned)
        except:
            pass
        
        try:
            # Вариант 2: 4-байтовый float (little-endian)
            if len(data) >= 4:
                value = struct.unpack('<f', data[:4])[0]  # little-endian float
                # Проверяем разумные пределы (0-250mm по настройкам)
                if 0 <= value <= 300:
                    return value
        except:
            pass
        
        try:
            # Вариант 3: 4-байтовый float (big-endian)
            if len(data) >= 4:
                value = struct.unpack('>f', data[:4])[0]  # big-endian float
                if 0 <= value <= 300:
                    return value
        except:
            pass
        
        return None
    
    def continuous_read(self, filename):
        """Непрерывное чтение данных"""
        print("📡 Начало чтения данных...")
        count = 0
        
        # Создание файла
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'DateTime', 'Measurement_mm', 'RawData'])
        
        last_print_time = time.time()
        
        try:
            while True:
                if self.ser.in_waiting > 0:
                    # Читаем все доступные данные
                    data = self.ser.read(self.ser.in_waiting)
                    
                    # Разбиваем на строки/сообщения (предполагаем, что данные приходят пакетами)
                    # Пробуем разные разделители
                    for separator in [b'\r\n', b'\n', b'\r']:
                        if separator in data:
                            messages = data.split(separator)
                            break
                    else:
                        messages = [data]  # если разделитель не найден, берем весь блок
                    
                    for msg in messages:
                        if len(msg) > 0:
                            measurement = self.parse_rf60x_data(msg)
                            timestamp = time.time()
                            dt_string = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                            
                            if measurement is not None:
                                # Запись в файл
                                with open(filename, 'a', newline='', encoding='utf-8') as f:
                                    writer = csv.writer(f)
                                    writer.writerow([timestamp, dt_string, measurement, msg.hex()])
                                
                                count += 1
                                
                                # Вывод каждые 10 измерений или каждую секунду
                                if count % 10 == 0 or time.time() - last_print_time >= 1:
                                    print(f"📊 #{count}: {measurement:.3f} mm (сырые: {msg.hex()})")
                                    last_print_time = time.time()
                            else:
                                # Вывод сырых данных для отладки
                                if time.time() - last_print_time >= 2:  # Чтобы не заспамить
                                    print(f"📦 Неразобранные данные: {msg.hex()}")
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

def main():
    print("RF60x Data Logger - Правильные настройки")
    print("=" * 60)
    print("Настройки из RF60x-SP:")
    print("  Порт: COM3")
    print("  Скорость: 921600")
    print("  Адрес: 1")
    print("  Базовая дистанция: 80 mm")
    print("  Диапазон: 250 mm")
    print("=" * 60)
    
    reader = RF60xReader()
    
    if reader.connect('COM3', 921600):
        # Даем время на инициализацию
        time.sleep(1)
        
        # Очищаем буфер
        reader.ser.reset_input_buffer()
        
        # Пробуем отправить команду Start
        reader.send_start_command()
        
        # Начинаем чтение
        filename = f"rf60x_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        print(f"💾 Запись в файл: {filename}")
        print("🎯 Наведите датчик на объект для измерений")
        print("⏹ Нажмите Ctrl+C для остановки")
        print("-" * 60)
        
        reader.continuous_read(filename)
    
    reader.close()

if __name__ == "__main__":
    main()