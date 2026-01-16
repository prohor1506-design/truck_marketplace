# handlers/customer.py

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import db
from keyboards import main_menu, services_keyboard
from states import OrderStates
from config import SERVICES, BOT_TOKEN, ADMIN_ID
from utils import generate_order_id

# Создаем роутер для заказчиков
router = Router()

# Создаем экземпляр бота для отправки уведомлений
bot = Bot(token=BOT_TOKEN)

# ========== ОБРАБОТКА КНОПОК ГЛАВНОГО МЕНЮ (заказчик) ==========

@router.message(F.text == "📦 Создать заказ")
async def create_order_start(message: Message, state: FSMContext):
    """Начало создания заказа"""
    user_info = db.get_user(message.from_user.id)
    if user_info and user_info['role'] == 'executor':
        await message.answer("❌ Вы исполнитель. Перейдите в заказчики для создания заказов.")
        return
    
    await state.set_state(OrderStates.select_service)
    await message.answer(
        "📦 **ВЫБЕРИТЕ ТИП УСЛУГИ:**\n\nКакую услуги вам нужно?",
        reply_markup=services_keyboard()
    )

@router.message(F.text == "👷 Стать исполнителем")
async def become_executor(message: Message, state: FSMContext):
    """Стать исполнителем"""
    user_id = message.from_user.id
    db.update_user_role(user_id, 'executor')
    
    await message.answer(
        "✅ Вы теперь исполнитель!\n\n"
        "📝 Чтобы начать получать заказы, заполните профиль.\n"
        "Используйте команду /register или нажмите '⚙️ Мой профиль'",
        reply_markup=main_menu('executor')
    )

@router.message(F.text == "👤 Профиль")
async def show_profile_button(message: Message):
    """Показать профиль (переадресация на команду)"""
    from handlers.commands import cmd_profile
    await cmd_profile(message)

@router.message(F.text == "ℹ️ Помощь")
async def show_help_button(message: Message):
    """Показать помощь (переадресация на команду)"""
    from handlers.commands import cmd_help
    await cmd_help(message)

# ========== CALLBACK ОБРАБОТЧИКИ ДЛЯ СОЗДАНИЯ ЗАКАЗА ==========

@router.callback_query(F.data.startswith("service_"))
async def handle_service_selection(callback: CallbackQuery, state: FSMContext):
    """Выбор услуги"""
    service_key = callback.data.replace("service_", "")
    
    await state.update_data(service=service_key)
    await state.set_state(OrderStates.enter_description)
    
    await callback.answer(f"Выбрано: {SERVICES.get(service_key)}")
    await callback.message.answer(
        f"✅ Вы выбрали: {SERVICES.get(service_key)}\n\n"
        "📝 Теперь опишите вашу задачу подробно.\n"
        "Напишите описание одним сообщением:"
    )

# ========== ОБРАБОТКА СОСТОЯНИЙ (FSM) - Создание заказа ==========

@router.message(OrderStates.enter_description)
async def process_description(message: Message, state: FSMContext):
    """Обработка описания заказа"""
    if len(message.text) < 10:
        await message.answer("❌ Описание слишком короткое. Напишите подробнее (минимум 10 символов).")
        return
    
    await state.update_data(description=message.text)
    await state.set_state(OrderStates.enter_address)
    
    await message.answer("📍 Теперь укажите АДРЕС:")

@router.message(OrderStates.enter_address)
async def process_address(message: Message, state: FSMContext):
    """Обработка адреса"""
    await state.update_data(address=message.text)
    await state.set_state(OrderStates.enter_price)
    
    await message.answer("💰 Укажите ЖЕЛАЕМУЮ ЦЕНУ:\n\nНапишите сумму в рублях или 0 если цена договорная.")

@router.message(OrderStates.enter_price)
async def process_price(message: Message, state: FSMContext):
    """Обработка цены заказа"""
    try:
        price = int(message.text)
        if price < 0:
            await message.answer("❌ Цена не может быть отрицательной")
            return
    except:
        await message.answer("❌ Введите целое число")
        return
    
    # Получаем данные из состояния
    data = await state.get_data()
    service = data.get('service')
    description = data.get('description')
    address = data.get('address')
    
    # Создаем заказ
    order_id = generate_order_id()
    desired_price = price if price > 0 else None
    
    success = db.create_order(order_id, message.from_user.id, service, description, address, desired_price)
    
    if success:
        response = f"""
✅ ЗАКАЗ СОЗДАН!

📦 Номер заказа: #{order_id}
📋 Услуга: {SERVICES.get(service, service)}
📍 Адрес: {address[:50]}
"""
        if desired_price:
            response += f"💰 Желаемая цена: {desired_price} ₽\n"
        
        response += "\n📊 Что дальше:\n1. Заказ увидят исполнители\n2. Они будут присылать предложения\n3. Вы получите уведомления"
        
        await message.answer(response)
        
        # Уведомление админу
        if ADMIN_ID:
            try:
                admin_msg = f"🆕 НОВЫЙ ЗАКАЗ #{order_id}\nОт: @{message.from_user.username or 'без username'}\nУслуга: {SERVICES.get(service, service)}"
                await bot.send_message(ADMIN_ID, admin_msg)
            except:
                pass
        
        # Получаем роль пользователя для меню
        user_info = db.get_user(message.from_user.id)
        role = user_info.get('role', 'customer') if user_info else 'customer'
        
        await message.answer("Главное меню:", reply_markup=main_menu(role))
    else:
        await message.answer("❌ Ошибка при создании заказа. Попробуйте еще раз.")
    
    # Очищаем состояние
    await state.clear()

# ========== ОБРАБОТКА ОТМЕНЫ ==========

@router.message(F.text == "❌ Отмена")
async def cancel_action(message: Message, state: FSMContext):
    """Отмена текущего действия"""
    await state.clear()
    
    user_info = db.get_user(message.from_user.id)
    role = user_info.get('role', 'customer') if user_info else 'customer'
    
    await message.answer(
        "❌ Действие отменено.",
        reply_markup=main_menu(role)
    )