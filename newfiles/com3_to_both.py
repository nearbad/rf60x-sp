# -*- coding: utf-8 -*-
import serial
import time
import threading

class COM3ToBothBridge:
    def __init__(self):
        self.running = True
        
    def start_bridge(self):
        print("🚀 Запуск расширенного моста COM3 → COM4 + COM5")
        
        try:
            # Открываем все порты
            self.com3 = serial.Serial('COM3', 9600, timeout=1)  # Реальный датчик
            self.com4 = serial.Serial('COM4', 9600, timeout=1)  # Для RF60x-SP
            self.com5 = serial.Serial('COM5', 9600, timeout=1)  # Для нашей программы
            
            print("✅ Все порты открыты:")
            print("   COM3 - реальный датчик")
            print("   COM4 - для RF60x-SP") 
            print("   COM5 - для Python программы")
            
            # Поток: COM3 → COM4 + COM5
            thread1 = threading.Thread(target=self.broadcast_from_com3)
            # Поток: COM4 → COM3 (команды от RF60x-SP)
            thread2 = threading.Thread(target=self.forward_to_com3, args=(self.com4, "COM4"))
            # Поток: COM5 → COM3 (команды от нашей программы)
            thread3 = threading.Thread(target=self.forward_to_com3, args=(self.com5, "COM5"))
            
            for thread in [thread1, thread2, thread3]:
                thread.daemon = True
                thread.start()
            
            print("📡 Мост запущен! Данные дублируются:")
            print("   COM3 → COM4 + COM5")
            print("   COM4 → COM3")
            print("   COM5 → COM3")
            print("   Нажмите Ctrl+C для остановки")
            
            while self.running:
                time.sleep(0.1)
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            self.stop_bridge()
    
    def broadcast_from_com3(self):
        """Пересылает данные с COM3 на COM4 и COM5"""
        while self.running:
            try:
                if self.com3.in_waiting > 0:
                    data = self.com3.read(self.com3.in_waiting)
                    if self.com4.is_open:
                        self.com4.write(data)
                    if self.com5.is_open:
                        self.com5.write(data)
                    if len(data) > 0:
                        print(f"COM3→COM4+COM5: {len(data)} байт")
            except Exception as e:
                print(f"Ошибка broadcast: {e}")
                time.sleep(0.1)
    
    def forward_to_com3(self, source, source_name):
        """Пересылает данные в COM3"""
        while self.running:
            try:
                if source.in_waiting > 0:
                    data = source.read(source.in_waiting)
                    if self.com3.is_open:
                        self.com3.write(data)
                    if len(data) > 0:
                        print(f"{source_name}→COM3: {len(data)} байт")
            except Exception as e:
                print(f"Ошибка {source_name}→COM3: {e}")
                time.sleep(0.1)
    
    def stop_bridge(self):
        self.running = False
        for port, name in [(self.com3, "COM3"), (self.com4, "COM4"), (self.com5, "COM5")]:
            if port and port.is_open:
                port.close()
                print(f"🔌 {name} закрыт")
        print("🛑 Мост остановлен")

def main():
    bridge = COM3ToBothBridge()
    try:
        bridge.start_bridge()
    except KeyboardInterrupt:
        print("\n⏹ Остановка по команде пользователя")
        bridge.stop_bridge()

if __name__ == "__main__":
    main()