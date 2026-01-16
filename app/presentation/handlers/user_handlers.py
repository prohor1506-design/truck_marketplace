"""
Хендлеры для работы с пользователями
"""

from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command, CommandStart

from app.shared.logger import logger
from app.presentation.keyboards import get_main_keyboard


def register_user_handlers(dp):
    """Регистрация хендлеров пользователей"""
    router = Router()
    
    @router.message(CommandStart())
    async def cmd_start(message: Message, user=None):
        """Обработка команды /start"""
        logger.info(f"Пользователь запустил бота: {message.from_user.id}")
        
        welcome_text = (
            "🚚 Добро пожаловать в <b>Truck Marketplace</b>!\n\n"
            "<i>Биржа грузоперевозок и спецтехники</i>\n\n"
            "Используйте команды:\n"
            "/register - 📝 Регистрация в системе\n"
            "/profile - 👤 Просмотр профиля\n"
            "/help - ❓ Помощь и инструкции"
        )
        
        if user and user.role:
            welcome_text += f"\n\n✅ Вы зарегистрированы как: {user.get_role_display()}"
        
        await message.answer(
            welcome_text,
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )
    
    @router.message(Command("help"))
    async def cmd_help(message: Message):
        """Обработка команды /help"""
        help_text = """
        <b>🚚 Truck Marketplace Bot - Помощь</b>
        
        <b>Основные команды:</b>
        /start - Запустить бота
        /help - Эта справка
        /profile - Мой профиль
        /register - Регистрация в системе
        
        <b>Для зарегистрированных пользователей:</b>
        • Создавайте и ищите заказы
        • Управляйте профилем
        • Взаимодействуйте с другими участниками
        
        <i>Для начала работы выполните /register</i>
        """
        
        await message.answer(help_text, parse_mode="HTML")
    
    @router.message(Command("profile"))
    async def cmd_profile(message: Message, user=None):
        """Обработка команды /profile"""
        if not user or not user.role:
            await message.answer(
                "👤 <b>Профиль не заполнен</b>\n\n"
                "Используйте /register для регистрации в системе.",
                parse_mode="HTML"
            )
            return
        
        # Используем метод get_profile_info из модели User
        profile_text = user.get_profile_info()
        
        await message.answer(
            profile_text,
            parse_mode="HTML"
        )
    
    @router.message(F.text == "👤 Мой профиль")
    async def btn_profile(message: Message, user=None):
        """Обработка кнопки профиля"""
        await cmd_profile(message, user)
    
    @router.message(F.text == "📊 Рынок заказов")
    async def btn_market(message: Message):
        """Обработка кнопки рынка заказов"""
        await message.answer(
            "🔄 <b>Рынок заказов</b>\n\n"
            "Функциональность в разработке...\n"
            "Скоро здесь можно будет просматривать доступные заказы.",
            parse_mode="HTML"
        )
    
    @router.message(F.text == "🚛 Моя техника")
    async def btn_equipment(message: Message):
        """Обработка кнопки моей техники"""
        await message.answer(
            "🔄 <b>Моя техника</b>\n\n"
            "Функциональность в разработке...\n"
            "Скоро здесь можно будет управлять своей техникой.",
            parse_mode="HTML"
        )
    
    # Регистрируем роутер в диспетчере
    dp.include_router(router)
    logger.info("✅ Хендлеры пользователей зарегистрированы")