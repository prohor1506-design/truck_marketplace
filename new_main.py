# new_main.py - СОЗДАЕМ НОВЫЙ ФАЙЛ (пока параллельно со старым)

import asyncio
import logging
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage

from app.shared.config import settings
from app.shared.dependencies import container
from app.shared.utils import setup_logging

logger = setup_logging()

async def setup_bot_commands(bot: Bot):
    """Настройка команд бота"""
    commands = [
        types.BotCommand(command="start", description="Запустить бота"),
        types.BotCommand(command="help", description="Помощь"),
        types.BotCommand(command="profile", description="Мой профиль"),
        types.BotCommand(command="market", description="Рынок заказов"),
        types.BotCommand(command="my_orders", description="Мои заказы"),
        types.BotCommand(command="my_equipment", description="Моя техника"),
        types.BotCommand(command="admin", description="Админ-панель"),
    ]
    await bot.set_my_commands(commands)

async def register_handlers(dp: Dispatcher):
    """Регистрация всех обработчиков"""
    # Импортируем и регистрируем роутеры
    from app.presentation.handlers import (
        user_handlers,
        order_handlers,
        equipment_handlers,
        admin_handlers
    )
    
    dp.include_router(user_handlers.router)
    dp.include_router(order_handlers.router)
    dp.include_router(equipment_handlers.router)
    dp.include_router(admin_handlers.router)

@asynccontextmanager
async def lifespan():
    """Управление жизненным циклом приложения"""
    # Старт
    logger.info("Инициализация приложения...")
    await container.init_database()
    await container.init_bot()
    
    yield
    
    # Завершение
    logger.info("Завершение приложения...")
    await container.shutdown()

async def main():
    """Основная функция запуска"""
    async with lifespan():
        bot = container._bot
        dp = container._dp
        
        # Настройка команд
        await setup_bot_commands(bot)
        
        # Регистрация обработчиков
        await register_handlers(dp)
        
        # Стартовый баннер
        print("=" * 60)
        print("🚚 TRUCK MARKETPLACE BOT")
        print("=" * 60)
        print(f"Architecture: Clean Architecture + DDD")
        print(f"Database: {settings.database.url}")
        print(f"Admin ID: {settings.bot.admin_id}")
        print("=" * 60)
        
        # Запуск бота
        logger.info("Бот запущен")
        await dp.start_polling(bot, skip_updates=settings.bot.skip_updates)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Фатальная ошибка: {e}", exc_info=True)