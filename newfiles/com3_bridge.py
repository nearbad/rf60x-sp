# -*- coding: utf-8 -*-
import serial
import time
import threading

class COM3Bridge:
    def __init__(self):
        self.running = True
        # Реальный порт датчика
        self.com3 = None
        # Виртуальный порт для RF60x-SP
        self.com4 = None
        
    def start_bridge(self):
        print("🚀 Запуск моста COM3 → COM4")
        print("COM3 - реальный порт датчика")
        print("COM4 - виртуальный порт для RF60x-SP")
        print("=" * 50)
        
        try:
            # Открываем реальный COM3 (порт датчика)
            self.com3 = serial.Serial(
                port='COM3',
                baudrate=9600,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            
            # Открываем виртуальный COM4 (для RF60x-SP)
            self.com4 = serial.Serial(
                port='COM4',
                baudrate=9600,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            
            print("✅ Порт COM3 открыт (реальный датчик)")
            print("✅ Порт COM4 открыт (виртуальный для RF60x-SP)")
            print("\n📡 Мост запущен. Данные передаются COM3 → COM4")
            print("   RF60x-SP должен быть подключен к COM4")
            print("   Нажмите Ctrl+C для остановки")
            
            # Запускаем потоки для передачи данных в обе стороны
            thread1 = threading.Thread(target=self.forward_data, args=(self.com3, self.com4, "COM3→COM4"))
            thread2 = threading.Thread(target=self.forward_data, args=(self.com4, self.com3, "COM4→COM3"))
            
            thread1.daemon = True
            thread2.daemon = True
            
            thread1.start()
            thread2.start()
            
            # Главный цикл
            while self.running:
                time.sleep(0.1)
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            self.stop_bridge()
    
    def forward_data(self, source, target, direction):
        """Пересылает данные из source в target"""
        while self.running:
            try:
                if source.in_waiting > 0:
                    data = source.read(source.in_waiting)
                    if target.is_open:
                        target.write(data)
                    # Логируем передачу (можно закомментировать)
                    if len(data) > 0:
                        print(f"{direction}: {len(data)} байт")
            except Exception as e:
                print(f"Ошибка в {direction}: {e}")
                time.sleep(0.1)
    
    def stop_bridge(self):
        self.running = False
        if self.com3 and self.com3.is_open:
            self.com3.close()
            print("🔌 COM3 закрыт")
        if self.com4 and self.com4.is_open:
            self.com4.close()
            print("🔌 COM4 закрыт")
        print("🛑 Мост остановлен")

def main():
    bridge = COM3Bridge()
    try:
        bridge.start_bridge()
    except KeyboardInterrupt:
        print("\n⏹ Остановка по команде пользователя")
        bridge.stop_bridge()

if __name__ == "__main__":
    main()