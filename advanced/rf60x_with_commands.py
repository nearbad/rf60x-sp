# -*- coding: utf-8 -*-
import serial
import serial.tools.list_ports
import csv
import datetime
import time

class RF60xController:
    def __init__(self):
        self.ser = None
        
    def connect(self, port, baudrate=9600):
        """Подключение к порту"""
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            print(f"✅ Подключено к {port}")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False
    
    def try_commands(self):
        """Попробовать различные команды для активации датчика"""
        commands = [
            b'\r\n',           # Просто Enter
            b'?',              # Запрос статуса
            b'READ\r\n',       # Команда чтения
            b'MEAS\r\n',       # Команда измерения
            b'START\r\n',      # Команда старта
            b'DATA\r\n',       # Запрос данных
            b'\x01',           # Символ SOH (Start of Header)
            b'\x02',           # Символ STX (Start of Text)
        ]
        
        print("🔄 Попытка активации датчика командами...")
        for i, cmd in enumerate(commands):
            try:
                print(f"  Команда {i+1}: {cmd} (hex: {cmd.hex()})")
                self.ser.write(cmd)
                self.ser.flush()
                time.sleep(0.5)
                
                # Проверяем ответ
                if self.ser.in_waiting > 0:
                    response = self.ser.read(self.ser.in_waiting)
                    print(f"    ✅ Ответ: {response.hex()}")
                    try:
                        text = response.decode('ascii').strip()
                        if text:
                            print(f"       как текст: '{text}'")
                    except:
                        pass
                    return True
            except Exception as e:
                print(f"    ❌ Ошибка: {e}")
        
        return False
    
    def continuous_read(self, filename):
        """Непрерывное чтение данных"""
        print("📡 Начало непрерывного чтения...")
        count = 0
        
        # Создание файла
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'DateTime', 'Measurement', 'RawData'])
        
        try:
            while True:
                if self.ser.in_waiting > 0:
                    data = self.ser.readline()
                    
                    # Парсинг данных
                    measurement = self.parse_data(data)
                    if measurement is not None:
                        timestamp = time.time()
                        dt_string = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        # Запись в файл
                        with open(filename, 'a', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow([timestamp, dt_string, measurement, data.hex()])
                        
                        count += 1
                        print(f"📊 #{count}: {measurement} (сырые: {data.hex()})")
                    else:
                        print(f"📦 Сырые данные: {data.hex()}")
                
                # Периодически отправляем команду для поддержания связи
                if count % 20 == 0 and count > 0:
                    self.ser.write(b'\r\n')
                
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print(f"\n⏹ Остановлено. Всего собрано: {count} измерений")
        except Exception as e:
            print(f"❌ Ошибка чтения: {e}")
    
    def parse_data(self, data):
        """Парсинг данных из датчика"""
        try:
            # Пробуем ASCII
            text = data.decode('ascii').strip()
            cleaned = ''.join(c for c in text if c.isdigit() or c in '.-')
            if cleaned:
                return float(cleaned)
        except:
            pass
        
        # Пробуем бинарные форматы
        try:
            if len(data) >= 4:
                import struct
                # Попробуем float (4 байта)
                value = struct.unpack('<f', data[:4])[0]  # little-endian
                if abs(value) < 10000:  # Разумные пределы для измерений
                    return value
        except:
            pass
        
        return None

def main():
    print("RF60x Data Logger with Commands")
    print("=" * 50)
    
    # Поиск портов
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
        selected_port = input("Введите порт (COM3): ").strip()
    
    # Попробовать разные скорости
    baudrates = [921600, 19200, 38400, 57600, 115200]
    controller = RF60xController()
    
    for baudrate in baudrates:
        print(f"\n🔄 Попытка подключения на скорости {baudrate}...")
        if controller.connect(selected_port, baudrate):
            time.sleep(1)  # Дать время на инициализацию
            
            # Попробовать команды
            if controller.try_commands():
                filename = f"rf60x_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                print(f"🎯 Датчик активирован! Начинаем запись в {filename}")
                controller.continuous_read(filename)
                break
            else:
                print(f"❌ Датчик не ответил на скорости {baudrate}")
                controller.ser.close()
        else:
            print(f"❌ Не удалось подключиться на скорости {baudrate}")
    
    if controller.ser and controller.ser.is_open:
        controller.ser.close()
        print("🔌 Порт закрыт")

if __name__ == "__main__":
    main()