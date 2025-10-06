# -*- coding: utf-8 -*-
import serial
import time
import struct

def detect_protocol():
    print("🎯 Определение протокола RF60x")
    print("=" * 50)
    
    try:
        ser = serial.Serial('COM3', 9600, timeout=2)
        print("✅ Подключено к COM3")
        
        # Тестовые команды для разных протоколов
        test_sequences = [
            # Modbus RTU команды
            b'\x01\x03\x00\x00\x00\x01\x84\x0A',  # Read holding registers
            b'\x01\x04\x00\x00\x00\x01\x31\xCA',  # Read input registers
            
            # Простые ASCII команды
            b'*IDN?\r\n',
            b'READ\r\n',
            b'MEASURE\r\n',
            b'DATA?\r\n',
            b'\r\n',
            
            # Бинарные команды
            b'\x01',  # SOH
            b'\x02',  # STX  
            b'\x05',  # ENQ
        ]
        
        for i, cmd in enumerate(test_sequences):
            print(f"\n🔧 Тест {i+1}: Команда {cmd.hex()}")
            try:
                ser.write(cmd)
                ser.flush()
                time.sleep(1)
                
                if ser.in_waiting > 0:
                    response = ser.read(ser.in_waiting)
                    print(f"   ✅ Ответ: {response.hex()}")
                    
                    # Анализ ответа
                    if len(response) == 1:
                        print(f"      Один байт: {response[0]:02x}")
                    elif len(response) >= 4:
                        # Пробуем распарсить как float
                        try:
                            value = struct.unpack('<f', response[:4])[0]
                            print(f"      Как float: {value}")
                        except:
                            pass
                    
                    # Пробуем как текст
                    try:
                        text = response.decode('ascii').strip()
                        if text:
                            print(f"      Как текст: '{text}'")
                    except:
                        pass
                else:
                    print("   ❌ Нет ответа")
                    
            except Exception as e:
                print(f"   ❌ Ошибка: {e}")
                
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()

if __name__ == "__main__":
    detect_protocol()
    input("\nНажмите Enter для выхода...")