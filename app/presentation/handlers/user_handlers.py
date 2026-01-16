"""
Хендлеры для работы с пользователями
"""

from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command, CommandStart

from app.shared.logger import logger


def register_user_handlers(dp):
    """Регистрация хендлеров пользователей"""
    router = Router()
    
    @router.message(CommandStart())
    async def cmd_start(message: Message):
        """Обработка команды /start"""
        logger.info(f"Новый пользователь: {message.from_user.id}")
        
        # Создаем клавиатуру
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="👤 Мой профиль")],
                [KeyboardButton(text="📊 Рынок заказов"), KeyboardButton(text="🚛 Моя техника")],
                [KeyboardButton(text="➕ Создать заказ"), KeyboardButton(text="🔍 Найти заказ")],
            ],
            resize_keyboard=True,
            one_time_keyboard=False
        )
        
        await message.answer(
            "🚚 Добро пожаловать в <b>Truck Marketplace</b>!\n\n"
            "<i>Биржа грузоперевозок и спецтехники</i>\n\n"
            "Выберите действие:",
            reply_markup=keyboard,
            parse_mode="HTML"
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
        
        <b>Для заказчиков:</b>
        • Создать заказ на перевозку
        • Найти исполнителя
        • Управлять своими заказами
        
        <b>Для исполнителей:</b>
        • Найти заказы
        • Откликнуться на заказ
        • Управлять техникой
        
        <b>Для владельцев техники:</b>
        • Добавить технику в аренду
        • Управлять арендой
        
        <i>Выберите роль в меню или используйте кнопки ниже.</i>
        """
        
        await message.answer(help_text, parse_mode="HTML")
    
    @router.message(Command("profile"))
    async def cmd_profile(message: Message):
        """Обработка команды /profile"""
        user = message.from_user
        
        profile_text = f"""
        <b>👤 Ваш профиль</b>
        
        <b>ID:</b> {user.id}
        <b>Имя:</b> {user.first_name or ''} {user.last_name or ''}
        <b>Username:</b> @{user.username if user.username else 'не установлен'}
        
        <i>Профиль еще не заполнен. Используйте кнопки для настройки.</i>
        """
        
        await message.answer(profile_text, parse_mode="HTML")
    
    @router.message(F.text == "👤 Мой профиль")
    async def btn_profile(message: Message):
        """Обработка кнопки профиля"""
        await cmd_profile(message)
    
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
