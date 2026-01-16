#!/usr/bin/env python3
"""
Скрипт установки и настройки проекта
"""

import os
import sys
import subprocess
from pathlib import Path


def print_header():
    """Вывод заголовка"""
    print("=" * 60)
    print("🚚 TRUCK MARKETPLACE BOT - Установка")
    print("=" * 60)


def check_python():
    """Проверка версии Python"""
    print("🔍 Проверка Python...")
    
    if sys.version_info < (3, 9):
        print(f"❌ Требуется Python 3.9+, у вас {sys.version}")
        return False
    
    print(f"✅ Python {sys.version}")
    return True


def install_dependencies():
    """Установка зависимостей"""
    print("\n📦 Установка зависимостей...")
    
    try:
        # Проверяем наличие requirements.txt
        if not Path("requirements.txt").exists():
            print("❌ Файл requirements.txt не найден")
            return False
        
        # Устанавливаем зависимости
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Зависимости установлены")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки зависимостей: {e}")
        return False


def create_env_file():
    """Создание .env файла если его нет"""
    print("\n📁 Создание .env файла...")
    
    env_path = Path(".env")
    
    if env_path.exists():
        print("✅ .env файл уже существует")
        return True
    
    # Создаем шаблон .env файла
    env_template = """# ========================================
# TRUCK MARKETPLACE BOT - КОНФИГУРАЦИЯ
# ========================================

# ТОКЕН БОТА (получите у @BotFather в Telegram)
BOT_TOKEN=ваш_реальный_токен_здесь

# ВАШ TELEGRAM ID (узнайте через @userinfobot)
BOT_ADMIN_ID=123456789

# ПРОПУСКАТЬ ОБНОВЛЕНИЯ ПРИ ЗАПУСКЕ
BOT_SKIP_UPDATES=True

# БАЗА ДАННЫХ
DB_URL=sqlite+aiosqlite:///./marketplace.db
DB_ECHO=False
DB_POOL_SIZE=10

# ЛОГИРОВАНИЕ
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
LOG_FILE=logs/bot.log

# РЕЖИМ РАБОТЫ
DEBUG=True
ENVIRONMENT=development
"""
    
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(env_template)
    
    print("✅ .env файл создан (шаблон)")
    print("⚠️  Замените 'ваш_реальный_токен_здесь' на ваш токен от @BotFather")
    return True


def create_directories():
    """Создание необходимых директорий"""
    print("\n📂 Создание структуры папок...")
    
    directories = [
        "logs",
        "app/shared",
        "app/infrastructure/database",
        "app/presentation/handlers",
        "alembic/versions",
    ]
    
    for directory in directories:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {directory}")
    
    print("✅ Структура папок создана")
    return True


def setup_database():
    """Настройка базы данных"""
    print("\n🗄️  Настройка базы данных...")
    
    try:
        # Создаем __init__.py файлы если их нет
        init_files = [
            "app/__init__.py",
            "app/shared/__init__.py", 
            "app/infrastructure/__init__.py",
            "app/infrastructure/database/__init__.py",
            "app/presentation/__init__.py",
            "app/presentation/handlers/__init__.py",
        ]
        
        for init_file in init_files:
            path = Path(init_file)
            if not path.exists():
                path.write_text("", encoding="utf-8")
        
        # Импортируем и создаем таблицы
        import asyncio
        from app.infrastructure.database.database_manager import DatabaseManager
        
        async def create_tables():
            manager = DatabaseManager()
            await manager.create_tables()
            await manager.close()
        
        asyncio.run(create_tables())
        print("✅ База данных создана")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания БД: {e}")
        return False


def print_footer():
    """Вывод заключительной информации"""
    print("\n" + "=" * 60)
    print("🎉 УСТАНОВКА ЗАВЕРШЕНА!")
    print("=" * 60)
    
    print("\n📝 СЛЕДУЮЩИЕ ШАГИ:")
    print("1. Получите токен бота у @BotFather в Telegram")
    print("2. Узнайте свой Telegram ID через @userinfobot")
    print("3. Откройте файл .env и замените:")
    print("   BOT_TOKEN=ваш_реальный_токен_здесь")
    print("   BOT_ADMIN_ID=123456789")
    print("4. Запустите проверку: python run.py check")
    print("5. Запустите бота: python run.py start")
    
    print("\n⚡ КОМАНДЫ ДЛЯ ЗАПУСКА:")
    print("  python run.py start     - запуск бота")
    print("  python run.py migrate   - обновить БД")
    print("  python run.py check     - проверка конфигурации")
    print("  python run.py shell     - интерактивная оболочка")
    
    print("\n🆘 ПОДДЕРЖКА:")
    print("  Если возникли проблемы:")
    print("  1. Проверьте токен в .env файле")
    print("  2. Убедитесь что установлены все зависимости")
    print("  3. Запустите: python setup.py для повторной установки")


def main():
    """Основная функция установки"""
    print_header()
    
    steps = [
        ("Проверка Python", check_python),
        ("Установка зависимостей", install_dependencies),
        ("Создание .env файла", create_env_file),
        ("Создание структуры папок", create_directories),
        ("Настройка базы данных", setup_database),
    ]
    
    success = True
    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        if not step_func():
            print(f"❌ {step_name} не удалась")
            success = False
            break
    
    if success:
        print_footer()
    else:
        print("\n❌ Установка не удалась. Проверьте ошибки выше.")


if __name__ == "__main__":
    main()