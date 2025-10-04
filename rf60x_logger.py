import serial
import csv
import datetime
import time
import logging
from threading import Thread, Event

class RF60xDataLogger:
    def __init__(self, port='COM1', baudrate=9600, csv_filename='rf60x_data.csv'):
        self.port = port
        self.baudrate = baudrate
        self.csv_filename = csv_filename
        self.serial_conn = None
        self.is_running = Event()
        self.is_running.set()
        
        # Настройка логирования
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
    def connect_serial(self):
        """Подключение к последовательному порту"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            self.logger.info(f"Успешное подключение к {self.port}")
            return True
        except serial.SerialException as e:
            self.logger.error(f"Ошибка подключения к {self.port}: {e}")
            return False
    
    def parse_rf60x_data(self, raw_data):
        """
        Парсинг данных от датчика RF60x
        Нужно адаптировать под конкретный формат данных вашего датчика
        """
        try:
            # Пример для ASCII формата: "123.45\r\n"
            data_str = raw_data.decode('ascii').strip()
            measurement = float(data_str)
            return measurement
        except (ValueError, UnicodeDecodeError) as e:
            self.logger.warning(f"Не удалось распарсить данные: {raw_data}, ошибка: {e}")
            return None
    
    def read_serial_data(self):
        """Чтение данных из последовательного порта"""
        if self.serial_conn and self.serial_conn.in_waiting > 0:
            try:
                raw_data = self.serial_conn.readline()
                if raw_data:
                    return self.parse_rf60x_data(raw_data)
            except serial.SerialException as e:
                self.logger.error(f"Ошибка чтения данных: {e}")
        return None
    
    def create_csv_header(self):
        """Создание заголовка CSV файла"""
        try:
            with open(self.csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Timestamp', 'Measurement', 'DateTime'])
            self.logger.info(f"Создан CSV файл: {self.csv_filename}")
        except IOError as e:
            self.logger.error(f"Ошибка создания файла: {e}")
    
    def save_to_csv(self, measurement):
        """Сохранение измерения в CSV файл"""
        try:
            timestamp = time.time()
            dt_string = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            
            with open(self.csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([timestamp, measurement, dt_string])
                
            self.logger.debug(f"Сохранено измерение: {measurement}")
            
        except IOError as e:
            self.logger.error(f"Ошибка записи в файл: {e}")
    
    def start_logging(self):
        """Запуск процесса сбора данных"""
        if not self.connect_serial():
            return False
        
        self.create_csv_header()
        self.logger.info("Начат сбор данных...")
        
        try:
            while self.is_running.is_set():
                measurement = self.read_serial_data()
                if measurement is not None:
                    self.save_to_csv(measurement)
                time.sleep(0.01)  # Короткая пауза для снижения нагрузки на CPU
                
        except KeyboardInterrupt:
            self.logger.info("Остановлено пользователем")
        finally:
            self.stop_logging()
    
    def stop_logging(self):
        """Остановка процесса сбора данных"""
        self.is_running.clear()
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.logger.info("Последовательный порт закрыт")
        self.logger.info("Сбор данных остановлен")

def main():
    # ⚙️ НАСТРОЙКИ - ИЗМЕНИТЬ ПОД СИСТЕМУ
    CONFIG = {
        'port': 'COM3',           # Порт: COM1, COM2, ... (Windows) или /dev/ttyUSB0, /dev/ttyACM0 (Linux)
        'baudrate': 9600,         # Скорость передачи (должна совпадать с настройками датчика)
        'csv_filename': f'rf60x_data_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    }
    
    logger = RF60xDataLogger(**CONFIG)
    
    print("=" * 50)
    print("RF60x Data Logger - Автоматический сбор данных")
    print("=" * 50)
    print(f"Порт: {CONFIG['port']}")
    print(f"Скорость: {CONFIG['baudrate']}")
    print(f"Файл данных: {CONFIG['csv_filename']}")
    print("Нажмите Ctrl+C для остановки")
    print("=" * 50)
    
    try:
        logger.start_logging()
    except Exception as e:
        logger.logger.error(f"Критическая ошибка: {e}")

if __name__ == "__main__":
    main()


# # Если данные приходят в двоичном формате
# def parse_binary_data(self, raw_data):
#     """Парсинг бинарных данных (пример)"""
#     try:
#         # Пример для 4-байтового float (адаптация под нужный формат)
#         if len(raw_data) >= 4:
#             measurement = struct.unpack('f', raw_data[:4])[0]  # float
#             return measurement
#     except struct.error as e:
#         self.logger.warning(f"Ошибка парсинга бинарных данных: {e}")
#     return None