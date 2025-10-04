import pandas as pd
import matplotlib.pyplot as plt
import time
from datetime import datetime

def live_monitor(csv_file, update_interval=2):
    """Просмотр данных в реальном времени"""
    plt.ion()
    fig, ax = plt.subplots()
    
    while True:
        try:
            df = pd.read_csv(csv_file)
            if len(df) > 0:
                ax.clear()
                ax.plot(df['Timestamp'], df['Measurement'])
                ax.set_xlabel('Время')
                ax.set_ylabel('Измерение')
                ax.set_title(f'Данные RF60x - {datetime.now().strftime("%H:%M:%S")}')
                plt.pause(update_interval)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            print("Ожидание данных...")
            time.sleep(update_interval)
        except KeyboardInterrupt:
            print("Мониторинг остановлен")
            break

if __name__ == "__main__":
    live_monitor('rf60x_data.csv')