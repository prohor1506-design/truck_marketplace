# main.py

import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import BOT_TOKEN, ADMIN_ID
from database import db
from handlers import commands, customer, executor, equipment

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def set_bot_commands(bot: Bot):
    """Установка команд бота"""
    commands_list = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="help", description="Помощь"),
        BotCommand(command="profile", description="Мой профиль"),
        BotCommand(command="executor", description="Стать исполнителем"),
        BotCommand(command="customer", description="Стать заказчиком"),
        BotCommand(command="register", description="Быстрая регистрация"),
        BotCommand(command="fill_profile", description="Заполнить профиль"),
        BotCommand(command="status", description="Статус системы"),
        BotCommand(command="debug_profile", description="Отладка профиля"),
        BotCommand(command="recreate_db", description="Пересоздать БД (админ)"),
    ]
    
    await bot.set_my_commands(commands_list)

async def main():
    """Основная функция запуска бота"""
    
    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Устанавливаем команды бота
    await set_bot_commands(bot)
    
    # Подключение роутеров (ВАЖНЫЙ ПОРЯДОК!)
    dp.include_router(executor.router)     # Сначала обработчики исполнителя
    dp.include_router(equipment.router)    # Потом оборудование
    dp.include_router(customer.router)     # Затем заказчики
    dp.include_router(commands.router)     # И только потом общие команды
    
    # Приветственное сообщение
    print("=" * 60)
    print("🤖 БИРЖА ГРУЗОПЕРЕВОЗОК И СПЕЦТЕХНИКИ ЗАПУЩЕНА")
    print("=" * 60)
    print(f"✅ База данных инициализирована")
    print(f"✅ Токен бота: {'...' + BOT_TOKEN[-10:] if BOT_TOKEN else '❌ НЕТ'}")
    print(f"✅ Администратор: {ADMIN_ID}")
    print(f"✅ Режим: Polling")
    print("=" * 60)
    print("📱 Ищите бота в Telegram")
    print("🔄 Бот работает...")
    print("=" * 60)
    
    try:
        # Запуск бота в режиме long-polling
        await dp.start_polling(bot, skip_updates=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        print(f"❌ Ошибка: {e}")
        print("🔄 Перезапустите бота вручную")
    finally:
        await bot.session.close()
        print("✅ Сессия бота закрыта")

if __name__ == "__main__":
    try:
        # Запускаем асинхронную функцию
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 До свидания!")
    except Exception as e:
        print(f"❌ Фатальная ошибка: {e}")
        print("Попробуйте:")
        print("1. Проверить токен бота в .env файле")
        print("2. Проверить интернет-соединение")
        print("3. Удалить marketplace.db и перезапустить")