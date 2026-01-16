# templates/handler_template.py
"""
Шаблон для новых обработчиков на Clean Architecture
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.shared.dependencies import container
from app.core.services.user_service import UserService
from app.core.services.order_service import OrderService
from app.core.services.equipment_service import EquipmentService
from app.core.services.offer_service import OfferService


def create_executor_router() -> Router:
    """Создать роутер для исполнителей (новый стиль)"""
    router = Router()
    
    # Получаем сервисы из DI контейнера
    user_service = container.get_user_service()
    order_service = container.get_order_service()
    equipment_service = container.get_equipment_service()
    offer_service = container.get_offer_service()
    
    @router.message(F.text == "⚙️ Мой профиль (новая)")
    async def show_executor_profile_new(message: Message):
        """Показать профиль исполнителя (новая архитектура)"""
        user_id = message.from_user.id
        
        try:
            # Используем сервис вместо прямого вызова БД
            profile_info = await user_service.get_executor_profile_info(user_id)
            
            if not profile_info["exists"]:
                await message.answer("❌ Профиль не найден. Заполните профиль через /register")
                return
            
            profile = profile_info["profile"]
            
            # Формируем текст
            text = (
                "👷 ВАШ ПРОФИЛЬ ИСПОЛНИТЕЛЯ (новая архитектура)\n\n"
                f"<b>Компания:</b> {profile.company_name or 'Не указано'}\n"
                f"<b>Телефон:</b> {profile.phone or 'Не указан'}\n"
                f"<b>Опыт:</b> {profile.experience_years} лет\n"
            )
            
            await message.answer(text, parse_mode="HTML")
            
        except Exception as e:
            await message.answer(f"❌ Ошибка: {str(e)}")
            # Логируем ошибку
    
    @router.message(F.text == "📋 Доступные заказы (новая)")
    async def show_available_orders_new(message: Message):
        """Показать доступные заказы (новая архитектура)"""
        user_id = message.from_user.id
        
        try:
            # Получаем активные заказы через сервис
            orders = await order_service.get_active_orders(exclude_user_id=user_id)
            
            if not orders:
                await message.answer("📭 Нет доступных заказов")
                return
            
            # Показываем первые 5 заказов
            text = "📦 ДОСТУПНЫЕ ЗАКАЗЫ (новая архитектура):\n\n"
            
            for i, order in enumerate(orders[:5], 1):
                text += f"{i}. #{order.order_id}\n"
                text += f"   📝 {order.description[:50]}...\n"
                text += f"   💰 {order.desired_price or 'Договорная'} руб\n"
                text += f"   📍 {order.address[:30]}...\n\n"
            
            await message.answer(text)
            
        except Exception as e:
            await message.answer(f"❌ Ошибка: {str(e)}")
    
    return router


# Декоратор для проверки исполнителя (новая версия)
def executor_required_new(func):
    """Декоратор для проверки, что пользователь - исполнитель (новая)"""
    async def wrapper(*args, **kwargs):
        from aiogram.types import Message, CallbackQuery
        
        # Извлекаем объект сообщения или callback
        message_or_callback = None
        
        for arg in args:
            if isinstance(arg, (Message, CallbackQuery)):
                message_or_callback = arg
                break
        
        if not message_or_callback:
            return await func(*args, **kwargs)
        
        user_id = message_or_callback.from_user.id
        
        try:
            # Используем сервис вместо прямой работы с БД
            user_service = container.get_user_service()
            user = await user_service.get_or_create_user(
                user_id=user_id,
                username=message_or_callback.from_user.username,
                full_name=message_or_callback.from_user.full_name
            )
            
            if not user.is_executor():
                if isinstance(message_or_callback, CallbackQuery):
                    await message_or_callback.answer(
                        "❌ Эта функция только для исполнителей",
                        show_alert=True
                    )
                else:
                    await message_or_callback.answer("❌ Вы не исполнитель")
                return None
            
            return await func(*args, **kwargs)
            
        except Exception as e:
            print(f"Ошибка в декораторе executor_required_new: {e}")
            return None
    
    return wrapper