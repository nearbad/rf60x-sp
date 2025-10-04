# Настройки соединения с RF60x
SERIAL_CONFIG = {
    'port': 'COM3',              # Последовательный порт
    'baudrate': 9600,           # Скорость (9600, 19200, 38400, 115200)
    'timeout': 1,               # Таймаут чтения (секунды)
    'bytesize': serial.EIGHTBITS,
    'parity': serial.PARITY_NONE,
    'stopbits': serial.STOPBITS_ONE
}

# Настройки логирования
LOGGING_CONFIG = {
    'level': 'INFO',            # DEBUG, INFO, WARNING, ERROR
    'format': '%(asctime)s - %(levelname)s - %(message)s'
}

# Настройки файла данных
DATA_CONFIG = {
    'auto_timestamp': True,     # Автоматическая метка времени
    'buffer_size': 100,         # Размер буфера перед записью
    'flush_interval': 5         # Интервал сброса буфера (секунды)
}