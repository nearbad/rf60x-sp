# -*- coding: utf-8 -*-
import serial
import time
import serial.tools.list_ports

def diagnostic_check():
    print("🔍 Диагностика COM3 порта")
    print("=" * 50)
    
    # Проверка портов
    ports = list(serial.tools.list_ports.comports())
    print("Найденные порты:")
    for port in ports:
        print(f"  {port.device} - {port.description}")
        if 'COM3' in port.device:
            print(f"    ✅ COM3 найден: {port.description}")
    
    try:
        # Подключение к COM3
        print("\nПодключение к COM3...")
        ser = serial.Serial(
            port='COM3',
            baudrate=921600,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=2
        )
        
        print("✅ Успешное подключение к COM3")
        print("📡 Ожидание данных в течение 10 секунд...")
        
        start_time = time.time()
        data_received = False
        
        while time.time() - start_time < 10:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                print(f"📨 Получены данные: {data.hex()} (hex)")
                try:
                    text = data.decode('ascii')
                    print(f"      как текст: '{text}'")
                except:
                    print(f"      не ASCII текст")
                data_received = True
            
            # Пробуем отправить команду
            if time.time() - start_time > 3 and not data_received:
                print("🔄 Попытка отправки команды...")
                # Простые команды для теста
                test_commands = [b'\r\n', b'?', b'READ', b'MEAS', b'\x01']
                for cmd in test_commands:
                    try:
                        ser.write(cmd)
                        print(f"  Отправлена команда: {cmd.hex()}")
                        time.sleep(0.5)
                    except:
                        pass
            
            time.sleep(0.1)
        
        if not data_received:
            print("❌ Данные не получены. Возможные причины:")
            print("   1. Датчик не включен")
            print("   2. Неправильная скорость (попробуйте 19200, 38400, 115200)")
            print("   3. Датчик требует специальных команд")
            print("   4. Проблема с кабелем/драйвером")
        else:
            print("✅ Данные получены успешно!")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("🔌 Порт закрыт")

if __name__ == "__main__":
    diagnostic_check()
    input("\nНажмите Enter для выхода...")