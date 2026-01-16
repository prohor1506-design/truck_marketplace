#!/usr/bin/env python3
"""
🚚 Truck Marketplace Bot - точка входа

Использование:
  python run.py start     - запуск бота
  python run.py migrate   - миграции БД
  python run.py shell     - интерактивная оболочка
  python run.py check     - проверка конфигурации
"""

import asyncio
import sys
import os
from pathlib import Path

# Фикс для Windows event loop
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

def print_banner():
    """Вывод стартового баннера"""
    banner = r"""
    ╔══════════════════════════════════════════════════════╗
    ║                 🚚 TRUCK MARKETPLACE                 ║
    ║                 Telegram Bot v1.0.0                  ║
    ╚══════════════════════════════════════════════════════╝
    
    Architecture: Clean Architecture
    Database: SQLite + SQLAlchemy
    Framework: Aiogram 3.x
    
    Команды:
      start     - Запуск бота
      migrate   - Создать/обновить БД
      shell     - Интерактивная оболочка
      check     - Проверка конфигурации
    
    """
    print(banner)

async def setup_database():
    """Создание/обновление базы данных"""
    print("🔄 Настройка базы данных...")
    
    try:
        from app.infrastructure.database.database_manager import DatabaseManager
        manager = DatabaseManager()
        await manager.create_tables()
        print("✅ База данных готова")
    except Exception as e:
        print(f"❌ Ошибка настройки БД: {e}")
        import traceback
        traceback.print_exc()

async def start_bot():
    """Запуск бота"""
    print_banner()
    print("🚀 Запуск бота...")
    
    # Проверяем конфигурацию
    from app.shared.config import config
    if not config.validate():
        print("\n❌ Нельзя запустить бота с невалидной конфигурацией")
        
        # Дополнительная проверка токена
        if not config.BOT_TOKEN or "ВАШ_ТОКЕН" in config.BOT_TOKEN:
            print("\n📝 ИНСТРУКЦИЯ ПО ПОЛУЧЕНИЮ ТОКЕНА:")
            print("1. Откройте Telegram")
            print("2. Найдите @BotFather")
            print("3. Создайте бота: /newbot")
            print("4. Придумайте имя бота")
            print("5. Получите токен")
            print("6. Откройте файл .env и замените 'ваш_реальный_токен_здесь' на ваш токен")
            print("7. Запустите снова: python run.py start")
        return
    
    try:
        from app.main import main as bot_main
        await bot_main()
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Фатальная ошибка при запуске бота: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

async def interactive_shell():
    """Интерактивная оболочка для разработки"""
    print("🐚 Запуск интерактивной оболочки...")
    
    try:
        from app.shared.config import config
        
        # Создаем сессию БД
        from app.infrastructure.database.database_manager import DatabaseManager
        manager = DatabaseManager()
        
        # Доступные переменные
        import code
        locals_dict = {
            'config': config,
            'manager': manager,
        }
        
        banner = """
        🐚 Interactive Shell
        Доступные переменные:
        - config: Конфигурация приложения
        - manager: Менеджер базы данных
        
        Примеры:
          print(config.BOT_TOKEN)
          await manager.create_tables()
        """
        print(banner)
        
        code.interact(local=locals_dict, banner="")
        
    except Exception as e:
        print(f"❌ Ошибка запуска оболочки: {e}")
        import traceback
        traceback.print_exc()

def check_config():
    """Проверка конфигурации"""
    print("🔧 Проверка конфигурации...")
    
    from app.shared.config import config
    config.validate()

def main():
    """Основная функция CLI"""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "start":
        asyncio.run(start_bot())
    elif command == "migrate":
        asyncio.run(setup_database())
    elif command == "shell":
        asyncio.run(interactive_shell())
    elif command == "check":
        check_config()
    else:
        print(f"❌ Неизвестная команда: {command}")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()