# -*- coding: utf-8 -*-
import serial
import serial.tools.list_ports
import time
import threading

class SerialBridge:
    def __init__(self, real_port, virtual_port1, virtual_port2, baudrate=9600):
        self.real_port = real_port
        self.virtual_port1 = virtual_port1  # Для RF60x-SP
        self.virtual_port2 = virtual_port2  # Для нашей программы
        self.baudrate = baudrate
        self.running = True
        
    def start_bridge(self):
        print("Запуск моста для дублирования данных...")
        print(f"Реальный порт: {self.real_port}")
        print(f"Виртуальный порт 1 (RF60x-SP): {self.virtual_port1}")
        print(f"Виртуальный порт 2 (Python): {self.virtual_port2}")
        
        try:
            # Открываем порты
            self.ser_real = serial.Serial(self.real_port, self.baudrate, timeout=1)
            self.ser_virt1 = serial.Serial(self.virtual_port1, self.baudrate, timeout=1)
            self.ser_virt2 = serial.Serial(self.virtual_port2, self.baudrate, timeout=1)
            
            print("✅ Все порты открыты успешно")
            
            # Запускаем потоки для чтения/записи
            thread1 = threading.Thread(target=self.forward_data, args=(self.ser_real, [self.ser_virt1, self.ser_virt2]))
            thread2 = threading.Thread(target=self.forward_data, args=(self.ser_virt1, [self.ser_real]))
            thread3 = threading.Thread(target=self.forward_data, args=(self.ser_virt2, [self.ser_real]))
            
            thread1.daemon = True
            thread2.daemon = True
            thread3.daemon = True
            
            thread1.start()
            thread2.start()
            thread3.start()
            
            print("Мост запущен. Нажмите Ctrl+C для остановки.")
            
            # Главный цикл
            while self.running:
                time.sleep(0.1)
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        finally:
            self.stop_bridge()
    
    def forward_data(self, source_ser, target_sers):
        """Пересылает данные из source_ser во все target_sers"""
        while self.running:
            try:
                if source_ser.in_waiting > 0:
                    data = source_ser.read(source_ser.in_waiting)
                    for target_ser in target_sers:
                        if target_ser.is_open:
                            target_ser.write(data)
                    # Вывод для отладки
                    if len(data) > 0:
                        print(f"Передано {len(data)} байт")
            except Exception as e:
                print(f"Ошибка пересылки: {e}")
                time.sleep(0.1)
    
    def stop_bridge(self):
        self.running = False
        if hasattr(self, 'ser_real') and self.ser_real.is_open:
            self.ser_real.close()
        if hasattr(self, 'ser_virt1') and self.ser_virt1.is_open:
            self.ser_virt1.close()
        if hasattr(self, 'ser_virt2') and self.ser_virt2.is_open:
            self.ser_virt2.close()
        print("Мост остановлен")

def main():
    # Настройки портов
    REAL_PORT = "COM3"           # Реальный порт датчика
    VIRTUAL_PORT_RF60X = "COM4"  # Для RF60x-SP
    VIRTUAL_PORT_PYTHON = "COM5" # Для нашей программы
    
    bridge = SerialBridge(REAL_PORT, VIRTUAL_PORT_RF60X, VIRTUAL_PORT_PYTHON)
    
    try:
        bridge.start_bridge()
    except KeyboardInterrupt:
        print("\nОстановка по команде пользователя")
        bridge.stop_bridge()

if __name__ == "__main__":
    main()
