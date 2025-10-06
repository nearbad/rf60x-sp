# -*- coding: utf-8 -*-
import serial
import serial.tools.list_ports
import csv
import datetime
import time
import struct
import threading

class RF60xDataProxy:
    def __init__(self, sensor_range_mm=250):
        self.sensor_range_mm = sensor_range_mm
        self.ser_sensor = None  # Для датчика (COM4)
        self.ser_rf60x_sp = None  # Для программы RF60x-SP (COM3)
        self.running = False
        self.data_count = 0
        
    def connect_sensor(self, port='COM4', baudrate=921600):
        """Подключение к датчику на COM4"""
        try:
            self.ser_sensor = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            print(f"✅ Датчик подключен к {port}")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения к датчику: {e}")
            return False
    
    def connect_rf60x_sp(self, port='COM3', baudrate=921600):
        """Подключение к программе RF60x-SP на COM3"""
        try:
            self.ser_rf60x_sp = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            print(f"✅ RF60x-SP подключен к {port}")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения к RF60x-SP: {e}")
            return False
    
    def send_command_to_sensor(self, command_code, address=1):
        """Отправка команды датчику"""
        try:
            inc0 = address & 0x7F
            inc1 = 0x80 | (command_code & 0x0F)
            
            cmd_bytes = bytes([inc0, inc1])
            print(f"🔄 Команда датчику: {cmd_bytes.hex()} (код: {command_code:02X}h)")
            
            self.ser_sensor.write(cmd_bytes)
            self.ser_sensor.flush()
            return True
            
        except Exception as e:
            print(f"❌ Ошибка отправки команды: {e}")
            return False
    
    def parse_rf60x_data(self, data):
        """Парсинг данных от датчика"""
        if len(data) < 4:
            return None
            
        try:
            bytes_list = list(data)
            
            # Проверяем формат пакета (старший бит = 1)
            if not all(b & 0x80 for b in bytes_list[:4]):
                return None
            
            # Извлекаем данные
            d0 = bytes_list[0] & 0x0F
            d1 = bytes_list[1] & 0x0F  
            d2 = bytes_list[2] & 0x0F
            d3 = bytes_list[3] & 0x0F
            
            # Собираем 16-битное значение
            low_byte = (d1 << 4) | d0
            high_byte = (d3 << 4) | d2
            raw_value = (high_byte << 8) | low_byte
            
            # Преобразуем в миллиметры
            measurement = raw_value * self.sensor_range_mm / 16384.0
            
            return measurement
            
        except Exception as e:
            print(f"❌ Ошибка парсинга: {e}")
            return None
    
    def forward_to_rf60x_sp(self, data):
        """Пересылка данных в RF60x-SP"""
        try:
            if self.ser_rf60x_sp and self.ser_rf60x_sp.is_open:
                self.ser_rf60x_sp.write(data)
                return True
        except Exception as e:
            print(f"❌ Ошибка пересылки в RF60x-SP: {e}")
        return False
    
    def start_data_stream(self):
        """Запуск потока данных с датчика"""
        return self.send_command_to_sensor(0x07)
    
    def stop_data_stream(self):
        """Остановка потока данных"""
        return self.send_command_to_sensor(0x08)
    
    def run_proxy(self, csv_filename):
        """Основной цикл прокси"""
        print("🚀 Запуск прокси...")
        print(f"📡 COM4 → 📊 CSV + 📡 COM3")
        
        # Создание CSV файла
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'DateTime', 'Measurement_mm', 'RawData_Hex'])
        
        buffer = b''
        self.running = True
        last_print_time = time.time()
        
        try:
            # Запускаем поток данных
            if not self.start_data_stream():
                print("❌ Не удалось запустить поток данных")
                return
            
            print("✅ Поток данных запущен")
            print("⏹ Нажмите Ctrl+C для остановки")
            print("-" * 60)
            
            while self.running:
                if self.ser_sensor.in_waiting > 0:
                    # Читаем данные с датчика
                    data = self.ser_sensor.read(self.ser_sensor.in_waiting)
                    
                    # Немедленно пересылаем в RF60x-SP
                    self.forward_to_rf60x_sp(data)
                    
                    # Обрабатываем для CSV
                    buffer += data
                    
                    # Парсим полные пакеты по 4 байта
                    while len(buffer) >= 4:
                        packet = buffer[:4]
                        buffer = buffer[4:]
                        
                        measurement = self.parse_rf60x_data(packet)
                        timestamp = time.time()
                        dt_string = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                        
                        if measurement is not None:
                            # Запись в CSV
                            with open(csv_filename, 'a', newline='', encoding='utf-8') as f:
                                writer = csv.writer(f)
                                writer.writerow([timestamp, dt_string, f"{measurement:.3f}", packet.hex()])
                            
                            self.data_count += 1
                            
                            # Вывод статистики
                            if self.data_count % 10 == 0 or time.time() - last_print_time >= 1:
                                print(f"📊 #{self.data_count}: {measurement:.3f} mm")
                                last_print_time = time.time()
                        else:
                            # Отладочная информация
                            if time.time() - last_print_time >= 2:
                                print(f"📦 Неразобранные данные: {packet.hex()}")
                                last_print_time = time.time()
                
                time.sleep(0.001)
                
        except KeyboardInterrupt:
            print(f"\n⏹ Остановлено пользователем")
        except Exception as e:
            print(f"❌ Ошибка в основном цикле: {e}")
        finally:
            self.running = False
            self.stop_data_stream()
            print(f"💾 Всего записано измерений: {self.data_count}")
    
    def close(self):
        """Закрытие всех соединений"""
        self.running = False
        
        if self.ser_sensor and self.ser_sensor.is_open:
            self.ser_sensor.close()
            print("🔌 Порт датчика закрыт")
        
        if self.ser_rf60x_sp and self.ser_rf60x_sp.is_open:
            self.ser_rf60x_sp.close()
            print("🔌 Порт RF60x-SP закрыт")

def select_com_port(prompt, default_port):
    """Выбор COM-порта с подсказкой"""
    print(f"\n{prompt}")
    ports = serial.tools.list_ports.comports()
    
    if not ports:
        print("COM-порты не найдены!")
        return default_port
    
    print("Найденные порты:")
    for i, port in enumerate(ports):
        print(f"  {i+1}. {port.device} - {port.description}")
    
    try:
        choice = input(f"Выберите номер порта (Enter для {default_port}): ").strip()
        if choice:
            port_index = int(choice) - 1
            selected_port = ports[port_index].device
            return selected_port
    except:
        pass
    
    return default_port

def main():
    print("RF60x Data Proxy - COM4 → CSV + COM3")
    print("=" * 60)
    
    # Выбор портов
    sensor_port = select_com_port("Выбор порта ДАТЧИКА:", "COM4")
    rf60x_sp_port = select_com_port("Выбор порта для RF60x-SP:", "COM3")
    
    # Настройки датчика
    try:
        sensor_range = float(input("Диапазон датчика в мм (по умолчанию 250): ") or "250")
    except:
        sensor_range = 250
        print(f"Используется диапазон: {sensor_range} мм")
    
    # Создание прокси
    proxy = RF60xDataProxy(sensor_range_mm=sensor_range)
    
    try:
        # Подключение к датчику
        if not proxy.connect_sensor(sensor_port, 921600):
            return
        
        # Подключение к RF60x-SP
        if not proxy.connect_rf60x_sp(rf60x_sp_port, 921600):
            proxy.close()
            return
        
        # Пауза для инициализации
        time.sleep(1)
        proxy.ser_sensor.reset_input_buffer()
        
        # Запуск прокси
        filename = f"rf60x_proxy_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        print(f"\n💾 Файл для записи: {filename}")
        
        proxy.run_proxy(filename)
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
    finally:
        proxy.close()

if __name__ == "__main__":
    main()