"""
Основной модуль запуска бота
"""

import asyncio
import sys
from pathlib import Path

# Фикс для Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.shared.config import config
from app.shared.logger import logger


async def main():
    """Основная функция запуска бота"""
    logger.info("=" * 60)
    logger.info("🚚 TRUCK MARKETPLACE BOT - Запуск")
    logger.info("=" * 60)
    
    logger.info(f"Режим: {config.ENVIRONMENT}")
    logger.info(f"База данных: {config.DATABASE_URL}")
    
    # Проверяем токен
    if not config.BOT_TOKEN:
        logger.error("❌ Токен бота не установлен!")
        logger.error("   Получите токен у @BotFather в Telegram")
        logger.error("   Добавьте его в .env файл: BOT_TOKEN=ваш_токен")
        return
    
    if "ВАШ_ТОКЕН" in config.BOT_TOKEN or "ваш_реальный_токен" in config.BOT_TOKEN:
        logger.error("❌ Токен бота содержит placeholder!")
        logger.error("   Замените 'ваш_реальный_токен_здесь' в .env файле на реальный токен")
        return
    
    logger.info(f"Токен бота: ...{config.BOT_TOKEN[-10:]}")
    logger.info(f"ID администратора: {config.ADMIN_ID}")
    
    # Создаем базу данных если нужно
    try:
        from app.infrastructure.database.database_manager import DatabaseManager
        manager = DatabaseManager()
        await manager.create_tables()
        logger.info("✅ База данных готова")
    except Exception as e:
        logger.error(f"❌ Ошибка создания БД: {e}")
        return
    
    # Инициализируем бота
    logger.info("🤖 Инициализация бота...")
    
    try:
        from aiogram import Bot, Dispatcher
        from aiogram.fsm.storage.memory import MemoryStorage
        from aiogram.client.default import DefaultBotProperties
        
        # НОВЫЙ СПОСОБ для aiogram 3.7.0+
        bot = Bot(
            token=config.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode="HTML")
        )
        
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Регистрируем хендлеры
        from app.presentation.handlers.user_handlers import register_user_handlers
        register_user_handlers(dp)
        
        logger.info("✅ Бот инициализирован")
        
        # Команды для меню
        from aiogram.types import BotCommand
        commands = [
            BotCommand(command="start", description="🚀 Запустить бота"),
            BotCommand(command="help", description="❓ Помощь"),
            BotCommand(command="profile", description="👤 Мой профиль"),
            BotCommand(command="market", description="📊 Рынок заказов"),
        ]
        await bot.set_my_commands(commands)
        
        # Запускаем бота
        logger.info("🔄 Запуск polling...")
        await dp.start_polling(bot, skip_updates=config.SKIP_UPDATES)
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Фатальная ошибка: {e}", exc_info=True)