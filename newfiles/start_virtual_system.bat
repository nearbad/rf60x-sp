@echo off
chcp 65001
title RF60x Virtual Port System

echo ========================================
echo    RF60x Virtual Port System
echo ========================================
echo.
echo Шаг 1: Настройка com0com
echo    - Установите com0com
echo    - Создайте пару: COM4 <-> COM5
echo.
echo Шаг 2: Подключение оборудования
echo    - Датчик подключен к COM3
echo    - RF60x-SP настроен на COM4
echo.
echo Шаг 3: Запуск системы
echo.

echo Запуск моста COM3 -> COM4...
start python com3_bridge.py

timeout /t 3

echo Запуск программы записи данных...
python rf60x_from_virtual.py

pause