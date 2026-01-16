@echo off
chcp 65001 >nul
title Создание конфигурации .env
color 0D

echo ==================================================
echo 🔧 СОЗДАНИЕ КОНФИГУРАЦИОННОГО ФАЙЛА .env
echo ==================================================
echo.

if exist ".env" (
    echo Файл .env уже существует.
    echo Хотите перезаписать? (y/n)
    set /p choice=
    if /i not "%choice%"=="y" (
        echo Отмена.
        pause
        exit /b 0
    )
)

echo.
echo Введите токен бота (получите у @BotFather):
echo Пример: 8479005883:AAHNZc8OTs-DRVZ1CpaVpZ2dYkJzhQdqV0E
set /p BOT_TOKEN=Токен: 

echo.
echo Введите ваш Telegram ID (получите у @userinfobot):
echo Пример: 378824723
set /p ADMIN_ID=ID администратора: 

echo.
echo Создание файла .env...
(
echo BOT_TOKEN=%BOT_TOKEN%
echo ADMIN_ID=%ADMIN_ID%
) > .env

echo.
echo ✅ Файл .env создан успешно!
echo.
echo Содержимое файла:
echo =================
type .env
echo =================
echo.
pause