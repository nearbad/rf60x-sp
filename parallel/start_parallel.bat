@echo off
chcp 65001
echo Запуск параллельной работы с RF60x-SP
echo.

echo Шаг 1: Настройте виртуальные порты в com0com
echo    Реальный порт датчика -> COM3 (виртуальный)
echo    COM3 -> COM4 (для RF60x-SP)
echo    COM3 -> COM5 (для Python программы)
echo.
echo Шаг 2: Запустите RF60x-SP и подключите к COM4
echo.
echo Шаг 3: Запустите этот файл для начала записи
echo.

pause

echo Запуск программы записи...
python rf60x_parallel.py

pause