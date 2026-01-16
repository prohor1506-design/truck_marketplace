@echo off
chcp 65001 >nul
title Установка зависимостей - Биржа грузоперевозок
color 0B

echo ==================================================
echo 📦 УСТАНОВКА ЗАВИСИМОСТЕЙ ДЛЯ БОТА
echo ==================================================
echo.

echo Проверка Python...
python --version
if errorlevel 1 (
    echo ❌ Python не найден!
    echo Установите Python 3.8+ с python.org
    pause
    exit /b 1
)

echo.
echo Обновление pip...
python -m pip install --upgrade pip

echo.
echo Установка зависимостей из requirements.txt...
if exist "requirements.txt" (
    pip install -r requirements.txt
) else (
    echo ❌ Файл requirements.txt не найден!
    echo Создание requirements.txt...
    (
echo aiogram==3.10.0
echo python-dotenv==1.0.0
echo aiofiles==23.2.1
    ) > requirements.txt
    
    pip install -r requirements.txt
)

echo.
echo ✅ Зависимости установлены!
echo.
echo Создайте файл .env со следующими переменными:
echo BOT_TOKEN=ваш_токен_бота
echo ADMIN_ID=ваш_id_телеграм
echo.
echo Затем запустите start.bat
pause