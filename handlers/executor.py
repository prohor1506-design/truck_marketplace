# handlers/executor.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from functools import wraps
from aiogram import Bot
from config import BOT_TOKEN

from database import db
from keyboards import (
    main_menu, 
    executor_profile_keyboard,
    order_filters_keyboard,
    equipment_types_keyboard,
    back_to_profile_keyboard,
    cancel_keyboard,
    skip_keyboard,
    executor_registration_steps,
    services_keyboard,
    executor_categories_keyboard
)
from states import (
    ExecutorRegistrationStates, 
    OrderFilterStates, 
    ProfileEditSimpleStates,
    OfferStates
)
from utils import validate_phone
from aiogram.filters import Command

# Создаем роутер для исполнителей
router = Router()

# Инициализация бота
bot = Bot(token=BOT_TOKEN)

# ========== ДЕКОРАТОР ДЛЯ ПРОВЕРКИ ИСПОЛНИТЕЛЯ ==========

def executor_required(func):
    """Декоратор для проверки, что пользователь - исполнитель"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Извлекаем объект сообщения или callback
        message_or_callback = None
        
        for arg in args:
            if hasattr(arg, 'from_user'):
                message_or_callback = arg
                break
        
        if not message_or_callback:
            for key, value in kwargs.items():
                if hasattr(value, 'from_user'):
                    message_or_callback = value
                    break
        
        if not message_or_callback:
            return await func(*args, **kwargs)
        
        user_id = message_or_callback.from_user.id
        user_info = db.get_user(user_id)
        
        if not user_info:
            if isinstance(message_or_callback, CallbackQuery):
                await message_or_callback.answer(
                    "❌ Вы не зарегистрированы. Используйте /start",
                    show_alert=True
                )
            elif isinstance(message_or_callback, Message):
                await message_or_callback.answer("❌ Вы не зарегистрированы. Используйте /start")
            return None
        
        if user_info['role'] != 'executor':
            if isinstance(message_or_callback, CallbackQuery):
                await message_or_callback.answer(
                    "❌ Эта функция только для исполнителей",
                    show_alert=True
                )
            elif isinstance(message_or_callback, Message):
                await message_or_callback.answer("❌ Вы не исполнитель")
            return None
        
        # Проверяем наличие профиля, если нужно
        if func.__name__ in ['show_filter_settings', 'filter_service_handler', 
                           'filter_price_handler', 'filter_distance_handler']:
            executor_profile = db.get_executor_profile(user_id)
            if not executor_profile:
                db.create_executor_profile(user_id)
        
        return await func(*args, **kwargs)
    
    return wrapper


# ========== РЕГИСТРАЦИЯ ИСПОЛНИТЕЛЯ (8 шагов) ==========

@router.callback_query(F.data.startswith("executor_register_"))
async def start_executor_registration(callback: CallbackQuery, state: FSMContext):
    """Начало регистрации исполнителя"""
    user_id = callback.from_user.id
    
    # Проверяем, не заполнен ли уже профиль
    profile = db.get_executor_profile(user_id)
    if profile and profile.get('company_name'):
        await callback.message.answer(
            "✅ У вас уже заполнен профиль исполнителя!\n"
            "Используйте '✏️ Редактировать профиль' для изменений.",
            reply_markup=executor_profile_keyboard(user_id, has_profile=True)
        )
        await callback.answer()
        return
    
    await callback.message.answer(
        "👷 РЕГИСТРАЦИЯ ИСПОЛНИТЕЛЯ\n\n"
        "Заполните информацию о вашей компании/сервисе.\n"
        "Это поможет заказчикам доверять вам.\n\n"
        "<b>Шаг 1 из 8:</b> Введите название вашей компании или ИП:",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )
    
    # Устанавливаем первое состояние
    await state.set_state(ExecutorRegistrationStates.enter_company_name)
    await callback.answer()


@router.message(F.text == "❌ Отмена")
async def cancel_registration(message: Message, state: FSMContext):
    """Отмена регистрации или любого другого процесса"""
    current_state = await state.get_state()
    
    if current_state:
        # Проверяем, какая именно регистрация/процесс отменяется
        if "ExecutorRegistrationStates" in str(current_state):
            await message.answer(
                "❌ Регистрация исполнителя отменена.",
                reply_markup=main_menu('executor')
            )
        elif "OrderStates" in str(current_state):
            await message.answer(
                "❌ Создание заказа отменено.",
                reply_markup=main_menu('customer')
            )
        elif "EquipmentRegistrationStates" in str(current_state):
            await message.answer(
                "❌ Добавление техники отменено.",
                reply_markup=main_menu('executor')
            )
        else:
            await message.answer(
                "❌ Действие отменено.",
                reply_markup=main_menu('customer')
            )
        
        await state.clear()


# ШАГ 1: Название компании
@router.message(ExecutorRegistrationStates.enter_company_name)
async def process_company_name(message: Message, state: FSMContext):
    """Обработка названия компании"""
    company_name = message.text.strip()
    
    # Валидация
    if len(company_name) < 2:
        await message.answer(
            "❌ Название слишком короткое. Введите название (минимум 2 символа):",
            reply_markup=cancel_keyboard()
        )
        return
    
    # Сохраняем в состояние
    await state.update_data(company_name=company_name)
    
    # Переходим к следующему шагу
    await message.answer(
        "<b>Шаг 2 из 8:</b> Введите контактный телефон:\n\n"
        "Формат: +7XXXXXXXXXX или 8XXXXXXXXXX",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(ExecutorRegistrationStates.enter_phone)


# ШАГ 2: Телефон
@router.message(ExecutorRegistrationStates.enter_phone)
async def process_phone(message: Message, state: FSMContext):
    """Обработка телефона"""
    phone = message.text.strip()
    is_valid, result = validate_phone(phone)
    
    if not is_valid:
        await message.answer(result, reply_markup=cancel_keyboard())
        return
    
    # Сохраняем в состояние
    await state.update_data(phone=result)
    
    await message.answer(
        "<b>Шаг 3 из 8:</b> Опишите ваши услуги:\n\n"
        "Пример: 'Грузоперевозки по городу и области. Есть газели, фуры, рефрижераторы.'\n"
        "Минимум 20 символов.",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(ExecutorRegistrationStates.enter_description)


# ШАГ 3: Описание услуг
@router.message(ExecutorRegistrationStates.enter_description)
async def process_description(message: Message, state: FSMContext):
    """Обработка описания услуг"""
    description = message.text.strip()
    
    if len(description) < 20:
        await message.answer(
            "❌ Описание слишком короткое. Минимум 20 символов.\n"
            "Опишите подробнее, какие услуги вы предоставляете:",
            reply_markup=cancel_keyboard()
        )
        return
    
    await state.update_data(description=description)
    
    await message.answer(
        "<b>Шаг 4 из 8:</b> Какой у вас опыт работы?\n\n"
        "Выберите или введите количество лет:",
        parse_mode="HTML",
        reply_markup=executor_registration_steps("experience")
    )
    await state.set_state(ExecutorRegistrationStates.enter_experience)


# ШАГ 4: Опыт работы
@router.message(ExecutorRegistrationStates.enter_experience)
async def process_experience(message: Message, state: FSMContext):
    """Обработка опыта работы"""
    experience = message.text.strip()
    
    # Парсим опыт из текста
    experience_years = 0
    if "Меньше года" in experience:
        experience_years = 0
    elif "1-3 года" in experience:
        experience_years = 2
    elif "3-5 лет" in experience:
        experience_years = 4
    elif "5-10 лет" in experience:
        experience_years = 7
    elif "Более 10 лет" in experience:
        experience_years = 10
    else:
        # Пытаемся извлечь число
        try:
            import re
            numbers = re.findall(r'\d+', experience)
            if numbers:
                experience_years = int(numbers[0])
            else:
                experience_years = 0
        except:
            experience_years = 0
    
    await state.update_data(experience_years=experience_years)
    
    await message.answer(
        "<b>Шаг 5 из 8:</b> Если есть, введите номер лицензии:\n\n"
        "Можно пропустить (необязательно)",
        parse_mode="HTML",
        reply_markup=skip_keyboard()
    )
    await state.set_state(ExecutorRegistrationStates.enter_license)


# ШАГ 5: Лицензия (необязательно)
@router.message(ExecutorRegistrationStates.enter_license)
async def process_license(message: Message, state: FSMContext):
    """Обработка лицензии"""
    if message.text == "⏭️ Пропустить":
        license_number = None
    else:
        license_number = message.text.strip() or None
    
    await state.update_data(license_number=license_number)
    
    await message.answer(
        "<b>Шаг 6 из 8:</b> Если есть, введите информацию о страховке:\n\n"
        "Можно пропустить (необязательно)",
        parse_mode="HTML",
        reply_markup=skip_keyboard()
    )
    await state.set_state(ExecutorRegistrationStates.enter_insurance)


# ШАГ 6: Страховка (необязательно)
@router.message(ExecutorRegistrationStates.enter_insurance)
async def process_insurance(message: Message, state: FSMContext):
    """Обработка страховки"""
    if message.text == "⏭️ Пропустить":
        insurance_info = None
    else:
        insurance_info = message.text.strip() or None
    
    await state.update_data(insurance_info=insurance_info)
    
    await message.answer(
        "<b>Шаг 7 из 8:</b> Укажите ваш адрес/местоположение:\n\n"
        "Это нужно для фильтрации заказов по расстоянию.",
        parse_mode="HTML",
        reply_markup=executor_registration_steps("location")
    )
    await state.set_state(ExecutorRegistrationStates.enter_location)


# ШАГ 7: Местоположение
@router.message(ExecutorRegistrationStates.enter_location)
async def process_location(message: Message, state: FSMContext):
    """Обработка местоположения"""
    if message.text == "⏭️ Пропустить":
        location_text = None
        await state.update_data(location_text=None, location_type='skipped')
    elif message.text == "📍 Отправить местоположение":
        await message.answer(
            "Пожалуйста, отправьте вашу геолокацию через кнопку ниже.",
            reply_markup=cancel_keyboard()
        )
        return
    elif message.text == "📝 Ввести адрес текстом":
        await message.answer(
            "Введите ваш адрес (например: Москва, ул. Ленина, д. 10):",
            reply_markup=cancel_keyboard()
        )
        return
    else:
        location_text = message.text.strip()
        # Сохраняем как текстовый адрес
        await state.update_data(
            location_text=location_text,
            location_type='address'
        )
    
    # Если это геолокация (location из сообщения с геопозицией)
    if message.location:
        latitude = message.location.latitude
        longitude = message.location.longitude
        await state.update_data(
            latitude=latitude,
            longitude=longitude,
            location_type='coordinates',
            location_text=f"Координаты: {latitude}, {longitude}"
        )
    
    # Проверяем, есть ли данные о местоположении
    data = await state.get_data()
    
    if 'location_text' not in data and 'latitude' not in data:
        await message.answer(
            "📍 Укажите ваше местоположение одним из способов:",
            reply_markup=executor_registration_steps("location")
        )
        return
    
    await message.answer(
        "<b>Шаг 8 из 8:</b> Укажите радиус работы (в км):\n\n"
        "Заказы будут показываться только в этом радиусе от вашего местоположения.",
        parse_mode="HTML",
        reply_markup=executor_registration_steps("radius")
    )
    await state.set_state(ExecutorRegistrationStates.enter_work_radius)


# ШАГ 8: Радиус работы
@router.message(ExecutorRegistrationStates.enter_work_radius)
async def process_work_radius(message: Message, state: FSMContext):
    """Обработка радиуса работы"""
    if message.text == "⏭️ Пропустить":
        work_radius = 20  # значение по умолчанию
    elif message.text == "📝 Свой вариант":
        await message.answer(
            "Введите радиус работы в километрах (например: 25):",
            reply_markup=cancel_keyboard()
        )
        return
    elif "км" in message.text:
        try:
            work_radius = int(message.text.replace(" км", ""))
        except:
            await message.answer(
                "❌ Неверный формат. Введите число (например: 25):",
                reply_markup=cancel_keyboard()
            )
            return
    else:
        try:
            work_radius = int(message.text)
        except:
            await message.answer(
                "❌ Неверный формат. Введите число (например: 25):",
                reply_markup=cancel_keyboard()
            )
            return
    
    # Проверка
    if work_radius <= 0:
        work_radius = 1
    elif work_radius > 1000:
        work_radius = 1000
    
    await state.update_data(work_radius_km=work_radius)
    
    # Завершаем регистрацию
    await finish_executor_registration(message, state)


async def finish_executor_registration(message: Message, state: FSMContext):
    """Завершение регистрации и сохранение данных"""
    user_id = message.from_user.id
    
    # Получаем все данные из состояния
    data = await state.get_data()
    
    # Определяем допустимые поля для профиля исполнителя
    profile_data = {}
    
    # Основные поля профиля
    basic_fields = [
        'company_name', 'phone', 'description', 'experience_years',
        'license_number', 'insurance_info', 'work_radius_km'
    ]
    
    # Собираем только допустимые поля
    for field in basic_fields:
        if field in data:
            profile_data[field] = data[field]
    
    # Геолокационные данные
    location_data = {}
    if 'location_text' in data:
        location_data['location_text'] = data['location_text']
    if 'latitude' in data:
        location_data['latitude'] = data['latitude']
    if 'longitude' in data:
        location_data['longitude'] = data['longitude']
    if 'location_type' in data:
        location_data['location_type'] = data['location_type']
    
    # Объединяем все данные
    all_profile_data = {**profile_data, **location_data}
    
    # Сохраняем в БД (безопасный метод)
    if all_profile_data:
        success = db.update_executor_profile(user_id, **all_profile_data)
        if not success:
            print(f"⚠️ Ошибка обновления профиля для user_id={user_id}")
    
    # Также сохраняем геолокацию в отдельную таблицу
    if 'latitude' in data and 'longitude' in data:
        db.update_user_location(
            user_id=user_id,
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            address=data.get('location_text')
        )
    
    # Получаем обновленный профиль
    profile = db.get_executor_profile(user_id)
    
    if not profile:
        await message.answer(
            "❌ Ошибка сохранения профиля. Попробуйте еще раз или обратитесь к администратору.",
            reply_markup=main_menu('executor')
        )
        await state.clear()
        return
    
    # Формируем сообщение с результатом
    result_text = (
        "✅ РЕГИСТРАЦИЯ ЗАВЕРШЕНА!\n\n"
        f"<b>Компания:</b> {profile.get('company_name', 'Не указано')}\n"
        f"<b>Телефон:</b> {profile.get('phone', 'Не указан')}\n"
        f"<b>Опыт:</b> {profile.get('experience_years', 0)} лет\n"
        f"<b>Радиус работы:</b> {profile.get('work_radius_km', 20)} км\n\n"
        "Теперь вы можете:\n"
        "1. 🚛 Добавить технику\n"
        "2. 🔍 Настроить фильтры поиска заказов\n"
        "3. 📋 Просматривать доступные заказы"
    )
    
    # Показываем клавиатуру профиля
    await message.answer(
        result_text,
        parse_mode="HTML",
        reply_markup=executor_profile_keyboard(user_id, has_profile=True)
    )
    
    # Очищаем состояние
    await state.clear()


@router.callback_query(F.data.startswith("executor_view_"))
async def view_executor_profile(callback: CallbackQuery):
    """Просмотр профиля исполнителя"""
    user_id = callback.from_user.id
    profile = db.get_executor_profile(user_id)
    
    if not profile:
        await callback.answer("❌ Профиль не найден")
        return
    
    # Формируем текст профиля
    text = (
        "👷 ВАШ ПРОФИЛЬ ИСПОЛНИТЕЛЯ\n\n"
        f"<b>Компания:</b> {profile.get('company_name', 'Не указано')}\n"
        f"<b>Телефон:</b> {profile.get('phone', 'Не указан')}\n"
        f"<b>Описание:</b> {profile.get('description', 'Не указано')[:100]}...\n"
        f"<b>Опыт:</b> {profile.get('experience_years', 0)} лет\n"
        f"<b>Радиус работы:</b> {profile.get('work_radius_km', 20)} км\n"
        f"<b>Минимальная цена:</b> {profile.get('min_price', 1000)} ₽\n"
        f"<b>Максимальная цена:</b> {profile.get('max_price', 50000)} ₽\n\n"
        f"<i>Зарегистрирован: {profile.get('created_at', 'Неизвестно')[:10]}</i>"
    )
    
    await callback.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=executor_profile_keyboard(user_id, has_profile=True)
    )
    await callback.answer()


# ========== ОБРАБОТКА КНОПОК ГЛАВНОГО МЕНЮ (исполнитель) ==========

@router.message(F.text == "⚙️ Мой профиль")
async def show_executor_profile(message: Message):
    """Показать профиль исполнителя"""
    user_id = message.from_user.id
    user_info = db.get_user(user_id)
    
    if user_info and user_info['role'] == 'executor':
        executor_profile = db.get_executor_profile(user_id)
        has_profile = bool(executor_profile and executor_profile.get('company_name'))
        
        await message.answer(
            "👷 ВАШ ПРОФИЛЬ ИСПОЛНИТЕЛЯ",
            reply_markup=executor_profile_keyboard(user_id, has_profile)
        )
    else:
        await message.answer("❌ Вы не исполнитель")


@router.message(F.text == "🚛 Моя техника")
@executor_required
async def show_equipment_menu(message: Message):
    """Меню управления техникой - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    user_id = message.from_user.id
    
    equipment = db.get_executor_equipment(user_id)
    
    if not equipment:
        # Используем InlineKeyboardBuilder для inline-кнопок
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(
            text="✅ Да, добавить", 
            callback_data="eq_add_first"
        ))
        builder.add(InlineKeyboardButton(
            text="❌ Нет, позже", 
            callback_data="back_to_profile"
        ))
        
        text = "🚛 У вас пока нет добавленной техники.\n\nХотите добавить первую единицу техники?"
        
        # ВСЕГДА используем answer для сообщений из главного меню
        await message.answer(text, reply_markup=builder.as_markup())
    else:
        text = "🚛 ВАША ТЕХНИКА:\n\n"
        for i, item in enumerate(equipment[:5], 1):
            status = "🟢" if item['is_available'] else "🔴"
            text += f"{status} {i}. {item['brand']} {item['model']} ({item['equipment_type']})\n"
        
        if len(equipment) > 5:
            text += f"\n... и ещё {len(equipment) - 5} единиц"
        
        # Используем InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(
            text="➕ Добавить ещё", 
            callback_data="eq_add_new"
        ))
        builder.add(InlineKeyboardButton(
            text="📋 Управлять", 
            callback_data="eq_manage_list"
        ))
        builder.row(InlineKeyboardButton(
            text="⬅️ Назад", 
            callback_data="back_to_profile"
        ))
        
        # ВСЕГДА используем answer для сообщений из главного меню
        await message.answer(text, reply_markup=builder.as_markup())


@router.message(F.text == "🔍 Настройки фильтров")
@executor_required
async def show_filter_settings(message: Message):
    """Настройка фильтров поиска заказов - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    user_id = message.from_user.id
    
    # Получаем текущие настройки профиля
    executor_profile = db.get_executor_profile(user_id)
    
    # Если профиль не найден, создаем его
    if not executor_profile:
        db.create_executor_profile(user_id)
        executor_profile = db.get_executor_profile(user_id)
        
        if not executor_profile:
            await message.answer("❌ Ошибка создания профиля. Попробуйте /register")
            return
    
    # Проверяем, заполнен ли профиль (хотя бы название компании)
    if not executor_profile.get('company_name'):
        await message.answer(
            "📝 Ваш профиль не заполнен!\n\n"
            "Для работы фильтров нужно:\n"
            "1. 📌 Указать название компании\n"
            "2. 📍 Указать местоположение (для фильтра по расстоянию)\n\n"
            "Заполните профиль через '⚙️ Мой профиль' → '📝 Заполнить профиль'",
            reply_markup=main_menu('executor')
        )
        return
    
    # Формируем тексты для фильтров
    service_filter = executor_profile.get('service_filter')
    if service_filter:
        category = db.get_category_by_code(service_filter)
        service_text = category['name'] if category else service_filter
    else:
        service_text = "Все"
    
    min_price = executor_profile.get('min_price')
    max_price = executor_profile.get('max_price')
    if min_price or max_price:
        min_text = f"{min_price}" if min_price else "любая"
        max_text = f"{max_price}" if max_price else "любая"
        price_text = f"{min_text}-{max_text} руб"
    else:
        price_text = "Любая"
    
    distance = executor_profile.get('work_radius_km', 20)
    distance_text = f"{distance} км" if distance else "Любое"
    
    current_filters = {
        'service_type': service_text,
        'price': price_text,
        'distance': distance_text
    }
    
    await message.answer(
        "🔍 НАСТРОЙКИ ФИЛЬТРОВ ПОИСКА\n\n"
        "Текущие настройки:\n"
        f"• 📦 Услуга: {service_text}\n"
        f"• 💰 Цена: {price_text}\n"
        f"• 📍 Расстояние: {distance_text}\n\n"
        "Выберите фильтр для настройки:",
        reply_markup=order_filters_keyboard(current_filters)
    )


@router.message(F.text == "💼 Мои предложения")
@executor_required
async def show_my_offers(message: Message):
    """Показать предложения исполнителя"""
    user_id = message.from_user.id
    offers = db.get_offers_by_executor(user_id)
    
    if not offers:
        await message.answer("📭 У вас пока нет предложений.")
        return
    
    text = "💼 ВАШИ ПРЕДЛОЖЕНИЯ:\n\n"
    for offer in offers[:5]:
        order = db.get_order(offer['order_id'])
        if order:
            text += f"📦 Заказ #{offer['order_id'][:8]}...\n"
            text += f"   Цена: {offer['price']} ₽\n"
            text += f"   Статус заказа: {order['status']}\n"
            text += f"   Дата: {offer['created_at'][:10]}\n\n"
    
    await message.answer(text)


# ========== ПРОСМОТР ДОСТУПНЫХ ЗАКАЗОВ ==========

@router.message(F.text == "📋 Доступные заказы")
@executor_required
async def show_available_orders(message: Message, state: FSMContext):
    """Показать доступные заказы для исполнителя"""
    user_id = message.from_user.id
    
    # Получаем отфильтрованные заказы
    orders = db.get_filtered_orders_for_executor(user_id)
    
    if not orders:
        await message.answer(
            "📭 Нет доступных заказов по вашим фильтрам.\n\n"
            "Попробуйте:\n"
            "1. 🔍 Настроить фильтры (сделать их шире)\n"
            "2. Подождать новых заказов\n"
            "3. 📦 Создать свой заказ (как заказчик)",
            reply_markup=main_menu('executor')
        )
        return
    
    # Сохраняем заказы в состояние для навигации
    await state.update_data(available_orders=orders, current_order_index=0)
    
    # Показываем первый заказ
    await show_order_details(message, state, 0)


async def show_order_details(message: Message, state: FSMContext, order_index: int):
    """Показать детали конкретного заказа"""
    data = await state.get_data()
    orders = data.get('available_orders', [])
    
    if not orders or order_index >= len(orders):
        await message.answer("❌ Заказы не найдены")
        await state.clear()
        return
    
    order = orders[order_index]
    
    # Формируем текст заказа
    text = f"""📦 ЗАКАЗ #{order['order_id']}

📋 Услуга: {order['service_type']}
📍 Адрес: {order.get('address', 'Не указан')}
👤 Заказчик: {order.get('full_name', 'Аноним')}

📝 Описание:
{order.get('description', 'Без описания')[:200]}{'...' if len(order.get('description', '')) > 200 else ''}

"""
    
    if order.get('desired_price'):
        text += f"💰 Желаемая цена: {order['desired_price']} ₽\n\n"
    else:
        text += "💰 Цена: Договорная\n\n"
    
    text += f"📅 Создан: {order.get('created_at', '')[:10]}\n"
    
    # Количество предложений
    offers_count = db.get_order_offers_count(order['order_id'])
    if offers_count > 0:
        text += f"📊 Предложений уже: {offers_count}\n"
    
    # Кнопки
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    
    # Кнопка "Предложить цену"
    builder.add(InlineKeyboardButton(
        text="💰 Предложить цену",
        callback_data=f"make_offer_{order['order_id']}"
    ))
    
    # Навигация если больше 1 заказа
    if len(orders) > 1:
        nav_buttons = []
        
        if order_index > 0:
            nav_buttons.append(InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=f"order_nav_{order_index-1}"
            ))
        
        nav_buttons.append(InlineKeyboardButton(
            text=f"{order_index+1}/{len(orders)}",
            callback_data="order_page"
        ))
        
        if order_index < len(orders) - 1:
            nav_buttons.append(InlineKeyboardButton(
                text="Вперед ▶️",
                callback_data=f"order_nav_{order_index+1}"
            ))
        
        builder.row(*nav_buttons)
    
    # Кнопка возврата
    builder.row(InlineKeyboardButton(
        text="⬅️ Назад в меню",
        callback_data="back_to_main_menu"
    ))
    
    await message.answer(text, reply_markup=builder.as_markup())


@router.message(F.text == "📦 Вернуться в заказчики")
async def back_to_customer(message: Message):
    """Вернуться в режим заказчика"""
    user_id = message.from_user.id
    db.update_user_role(user_id, 'customer')
    
    await message.answer(
        "✅ Вы вернулись в режим заказчика!",
        reply_markup=main_menu('customer')
    )


@router.message(F.text == "ℹ️ Помощь")
async def show_help_button(message: Message):
    """Показать помощь (переадресация на команду)"""
    from handlers.commands import cmd_help
    await cmd_help(message)


# ========== ОБРАБОТКА ФИЛЬТРОВ ==========

@router.callback_query(F.data == "filter_service")
@executor_required
async def filter_service_handler(callback: CallbackQuery, state: FSMContext):
    """Фильтр по услуге - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    user_id = callback.from_user.id
    
    # Получаем категории
    categories = db.get_categories()
    
    # Создаем клавиатуру
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="📦 Все услуги", 
        callback_data="filter_service_all"
    ))
    
    for category in categories[:12]:  # Ограничиваем 12 категориями
        builder.add(InlineKeyboardButton(
            text=category['name'],
            callback_data=f"filter_service_{category['code']}"
        ))
    
    builder.add(InlineKeyboardButton(
        text="⬅️ Назад", 
        callback_data="filters_back"
    ))
    builder.adjust(2)
    
    # Отвечаем
    try:
        await callback.message.answer(
            "📦 ВЫБЕРИТЕ ТИП УСЛУГИ ДЛЯ ФИЛЬТРАЦИИ:\n\n"
            "Выберите конкретную услугу или 'Все услуги'",
            reply_markup=builder.as_markup()
        )
    except Exception as e:
        # Если не удалось отправить сообщение, пробуем редактировать
        try:
            await callback.message.edit_text(
                "📦 ВЫБЕРИТЕ ТИП УСЛУГИ ДЛЯ ФИЛЬТРАЦИИ:\n\n"
                "Выберите конкретную услугу или 'Все услуги'",
                reply_markup=builder.as_markup()
            )
        except:
            await callback.answer("❌ Ошибка обновления сообщения")
    
    await callback.answer()


@router.callback_query(F.data.startswith("filter_service_"))
@executor_required
async def select_service_filter(callback: CallbackQuery, state: FSMContext):
    """Выбор конкретной услуги для фильтра - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    user_id = callback.from_user.id
    
    service_code = callback.data.replace("filter_service_", "")
    
    # Сохраняем в профиле
    if service_code == "all":
        # Сбрасываем фильтр по услуге
        db.update_executor_profile(user_id, service_filter=None)
        service_name = "Все услуги"
    else:
        category = db.get_category_by_code(service_code)
        if category:
            db.update_executor_profile(user_id, service_filter=service_code)
            service_name = category['name']
        else:
            service_name = "Неизвестная услуга"
    
    # Показываем уведомление
    await callback.answer(f"✅ Выбрано: {service_name}")
    
    # Возвращаемся к фильтрам
    try:
        # Пытаемся отредактировать текущее сообщение
        await show_filter_settings_with_update(callback, state)
    except:
        # Если не удалось, отправляем новое сообщение
        await callback.message.answer(
            f"✅ Фильтр по услуге установлен: {service_name}\n\n"
            "Используйте '🔍 Настройки фильтров' для дальнейших настроек.",
            reply_markup=back_to_profile_keyboard()
        )
    
    # Очищаем состояние
    await state.clear()


@router.callback_query(F.data == "filter_price")
@executor_required
async def filter_price_handler(callback: CallbackQuery, state: FSMContext):
    """Фильтр по цене"""
    await callback.message.answer(
        "💰 НАСТРОЙКА ФИЛЬТРА ПО ЦЕНЕ:\n\n"
        "Введите диапазон цен в формате:\n"
        "<strong>мин-макс</strong>\n\n"
        "Примеры:\n"
        "• 1000-5000 (от 1000 до 5000 руб)\n"
        "• 5000- (от 5000 руб)\n"
        "• -20000 (до 20000 руб)\n\n"
        "Или введите 0 для сброса фильтра.",
        parse_mode="HTML"
    )
    
    # Устанавливаем состояние для ожидания ввода
    await state.set_state(OrderFilterStates.set_price_range)
    await callback.answer()


@router.message(F.text, OrderFilterStates.set_price_range)
@executor_required
async def process_price_filter(message: Message, state: FSMContext):
    """Обработка ввода ценового диапазона"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    if text == "0":
        # Сброс фильтра
        db.update_executor_profile(user_id, min_price=None, max_price=None)
        await message.answer("✅ Фильтр по цене сброшен")
    else:
        try:
            # Парсим диапазон
            if '-' in text:
                parts = text.split('-')
                if len(parts) == 2:
                    min_price = int(parts[0].strip()) if parts[0].strip() else None
                    max_price = int(parts[1].strip()) if parts[1].strip() else None
                    
                    # Валидация
                    if min_price and min_price < 0:
                        await message.answer("❌ Минимальная цена не может быть отрицательной")
                        return
                    
                    if max_price and max_price < 0:
                        await message.answer("❌ Максимальная цена не может быть отрицательной")
                        return
                    
                    if min_price and max_price and min_price > max_price:
                        await message.answer("❌ Минимальная цена не может быть больше максимальной")
                        return
                    
                    # Сохраняем
                    db.update_executor_profile(user_id, min_price=min_price, max_price=max_price)
                    
                    min_text = f"{min_price}" if min_price else "любая"
                    max_text = f"{max_price}" if max_price else "любая"
                    
                    await message.answer(f"✅ Фильтр по цене установлен: {min_text}-{max_text} руб")
                else:
                    await message.answer("❌ Неверный формат. Используйте: мин-макс")
            else:
                await message.answer("❌ Неверный формат. Используйте: мин-макс")
        except ValueError:
            await message.answer("❌ Введите числа или 0 для сброса")
    
    # Очищаем состояние и показываем обновленные фильтры
    await state.clear()
    await show_filter_settings(message)


@router.callback_query(F.data == "filters_apply")
@executor_required
async def apply_filters(callback: CallbackQuery):
    """Применить фильтры - УПРОЩЕННАЯ ВЕРСИЯ"""
    user_id = callback.from_user.id
    
    # УБИРАЕМ ПРОВЕРКУ ГЕОЛОКАЦИИ - она больше не нужна!
    profile = db.get_executor_profile(user_id)
    
    # Получаем отфильтрованные заказы
    orders = db.get_filtered_orders_for_executor(user_id)
    
    await callback.message.answer(
        f"✅ Фильтры применены!\n\n"
        f"📋 Найдено заказов: {len(orders)}\n\n"
        f"Используйте '📋 Доступные заказы' для просмотра.",
        reply_markup=back_to_profile_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "filters_reset")
@executor_required
async def reset_filters(callback: CallbackQuery):
    """Сбросить все фильтры"""
    user_id = callback.from_user.id
    
    # Сбрасываем только фильтры услуги и цены (радиус больше не сбрасываем)
    db.update_executor_profile(user_id, 
        service_filter=None,
        min_price=None,
        max_price=None
        # work_radius_km больше не сбрасываем - он не используется
    )
    
    await callback.message.answer(
        "🔄 Все фильтры сброшены до значений по умолчанию!",
        reply_markup=back_to_profile_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "filters_back")
@executor_required
async def back_to_filters(callback: CallbackQuery, state: FSMContext):
    """Вернуться к фильтрам"""
    await state.clear()
    await show_filter_settings(callback.message)
    await callback.answer()


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

async def show_filter_settings_with_update(callback: CallbackQuery, state: FSMContext):
    """Показать обновленные настройки фильтров"""
    await state.clear()
    
    # Получаем текущие настройки профиля
    user_id = callback.from_user.id
    executor_profile = db.get_executor_profile(user_id)
    
    if not executor_profile:
        await callback.answer("❌ Профиль не найден", show_alert=True)
        return
    
    # Формируем тексты для фильтров (ТОЛЬКО 2 ФИЛЬТРА - без расстояния)
    service_filter = executor_profile.get('service_filter')
    if service_filter and service_filter != 'all':
        category = db.get_category_by_code(service_filter)
        service_text = category['name'] if category else service_filter
    else:
        service_text = "Все"
    
    min_price = executor_profile.get('min_price')
    max_price = executor_profile.get('max_price')
    if min_price or max_price:
        min_text = f"{min_price}" if min_price else "любая"
        max_text = f"{max_price}" if max_price else "любая"
        price_text = f"{min_text}-{max_text} руб"
    else:
        price_text = "Любая"
    
    # Радиос больше не показываем
    current_filters = {
        'service_type': service_text,
        'price': price_text
        # Расстояние удалено!
    }
    
    try:
        await callback.message.edit_text(
            "🔍 НАСТРОЙКИ ФИЛЬТРОВ ПОИСКА\n\n"
            "Текущие настройки:\n"
            f"• 📦 Услуга: {service_text}\n"
            f"• 💰 Цена: {price_text}\n\n"
            "Выберите фильтр для настройки:",
            reply_markup=order_filters_keyboard(current_filters)
        )
    except:
        await callback.message.answer(
            "🔍 НАСТРОЙКИ ФИЛЬТРОВ ПОИСКА\n\n"
            "Текущие настройки:\n"
            f"• 📦 Услуга: {service_text}\n"
            f"• 💰 Цена: {price_text}\n\n"
            "Выберите фильтр для настройки:",
            reply_markup=order_filters_keyboard(current_filters)
        )


# ========== ОБРАБОТКА КНОПОК ПРОФИЛЯ ==========

@router.callback_query(F.data == "executor_edit_menu")
@executor_required
async def executor_edit_menu_handler(callback: CallbackQuery):
    """Меню редактирования профиля"""
    user_id = callback.from_user.id
    
    # Создаем меню редактирования
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="🏢 Название компании",
        callback_data="edit_company_simple"
    ))
    builder.add(InlineKeyboardButton(
        text="📞 Телефон", 
        callback_data="edit_phone_simple"
    ))
    builder.add(InlineKeyboardButton(
        text="📝 Описание услуг",
        callback_data="edit_description_simple"
    ))
    builder.add(InlineKeyboardButton(
        text="👷 Опыт работы",
        callback_data="edit_experience_simple"
    ))
    builder.add(InlineKeyboardButton(
        text="💰 Ценовая политика",
        callback_data="edit_pricing_simple"
    ))
    
    builder.add(InlineKeyboardButton(
        text="⬅️ Назад к профилю",
        callback_data=f"executor_view_{user_id}"
    ))
    
    builder.adjust(2, 2, 1, 1)
    
    try:
        await callback.message.edit_text(
            "✏️ РЕДАКТИРОВАНИЕ ПРОФИЛЯ\n\n"
            "Выберите, что хотите изменить:",
            reply_markup=builder.as_markup()
        )
    except:
        await callback.message.answer(
            "✏️ РЕДАКТИРОВАНИЕ ПРОФИЛЯ\n\n"
            "Выберите, что хотите изменить:",
            reply_markup=builder.as_markup()
        )
    
    await callback.answer()


@router.callback_query(F.data == "equipment_menu")
@executor_required
async def equipment_menu_handler(callback: CallbackQuery):
    """Меню управления техникой через inline-кнопку"""
    user_id = callback.from_user.id
    equipment = db.get_executor_equipment(user_id)
    
    if not equipment:
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(
            text="✅ Да, добавить", 
            callback_data="eq_add_first"
        ))
        builder.add(InlineKeyboardButton(
            text="❌ Нет, позже", 
            callback_data="back_to_profile"
        ))
        
        text = "🚛 У вас пока нет добавленной техники.\n\nХотите добавить первую единицу техники?"
        
        # Для callback используем edit_text
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
    else:
        text = "🚛 ВАША ТЕХНИКА:\n\n"
        for i, item in enumerate(equipment[:5], 1):
            status = "🟢" if item['is_available'] else "🔴"
            text += f"{status} {i}. {item['brand']} {item['model']} ({item['equipment_type']})\n"
        
        if len(equipment) > 5:
            text += f"\n... и ещё {len(equipment) - 5} единиц"
        
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(
            text="➕ Добавить ещё", 
            callback_data="eq_add_new"
        ))
        builder.add(InlineKeyboardButton(
            text="📋 Управлять", 
            callback_data="eq_manage_list"
        ))
        builder.row(InlineKeyboardButton(
            text="⬅️ Назад", 
            callback_data="back_to_profile"
        ))
        
        # Для callback используем edit_text
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
    
    await callback.answer()


@router.callback_query(F.data == "back_to_profile")
async def back_to_profile_handler(callback: CallbackQuery):
    """Назад к профилю исполнителя"""
    user_id = callback.from_user.id
    
    # Показываем клавиатуру профиля
    from keyboards import executor_profile_keyboard
    executor_profile = db.get_executor_profile(user_id)
    has_profile = bool(executor_profile and executor_profile.get('company_name'))
    
    try:
        await callback.message.edit_text(
            "👷 ВАШ ПРОФИЛЬ ИСПОЛНИТЕЛЯ",
            reply_markup=executor_profile_keyboard(user_id, has_profile)
        )
    except:
        await callback.message.answer(
            "👷 ВАШ ПРОФИЛЬ ИСПОЛНИТЕЛЯ",
            reply_markup=executor_profile_keyboard(user_id, has_profile)
        )
    
    await callback.answer()


# ========== РЕАЛЬНОЕ РЕДАКТИРОВАНИЕ ПРОФИЛЯ ==========

@router.callback_query(F.data == "edit_company_simple")
@executor_required
async def edit_company_start(callback: CallbackQuery, state: FSMContext):
    """Начать редактирование названия компании"""
    user_id = callback.from_user.id
    profile = db.get_executor_profile(user_id)
    
    current_name = profile.get('company_name', 'Не указано')
    
    await callback.message.answer(
        f"🏢 РЕДАКТИРОВАНИЕ НАЗВАНИЯ КОМПАНИИ\n\n"
        f"Текущее название: <b>{current_name}</b>\n\n"
        f"Введите новое название компании:",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )
    
    await state.set_state(ProfileEditSimpleStates.edit_company)
    await callback.answer()


@router.message(ProfileEditSimpleStates.edit_company)
@executor_required
async def edit_company_process(message: Message, state: FSMContext):
    """Обработка нового названия компании"""
    new_name = message.text.strip()
    
    if len(new_name) < 2:
        await message.answer("❌ Название слишком короткое. Введите название (минимум 2 символа):")
        return
    
    user_id = message.from_user.id
    
    # Сохраняем в БД
    db.update_executor_profile(user_id, company_name=new_name)
    
    await message.answer(
        f"✅ Название компании обновлено: <b>{new_name}</b>",
        parse_mode="HTML",
        reply_markup=back_to_profile_keyboard()
    )
    
    await state.clear()


@router.callback_query(F.data == "edit_phone_simple")
@executor_required
async def edit_phone_start(callback: CallbackQuery, state: FSMContext):
    """Начать редактирование телефона"""
    user_id = callback.from_user.id
    profile = db.get_executor_profile(user_id)
    
    current_phone = profile.get('phone', 'Не указан')
    
    await callback.message.answer(
        f"📞 РЕДАКТИРОВАНИЕ ТЕЛЕФОНА\n\n"
        f"Текущий телефон: <b>{current_phone}</b>\n\n"
        f"Введите новый телефон в формате +7XXXXXXXXXX или 8XXXXXXXXXX:",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )
    
    await state.set_state(ProfileEditSimpleStates.edit_phone)
    await callback.answer()


@router.message(ProfileEditSimpleStates.edit_phone)
@executor_required
async def edit_phone_process(message: Message, state: FSMContext):
    """Обработка нового телефона"""
    phone = message.text.strip()
    
    # Используем существующую валидацию
    from utils import validate_phone
    is_valid, result = validate_phone(phone)
    
    if not is_valid:
        await message.answer(result)
        return
    
    user_id = message.from_user.id
    
    # Сохраняем в БД
    db.update_executor_profile(user_id, phone=result)
    
    await message.answer(
        f"✅ Телефон обновлен: <b>{result}</b>",
        parse_mode="HTML",
        reply_markup=back_to_profile_keyboard()
    )
    
    await state.clear()


@router.callback_query(F.data == "edit_description_simple")
@executor_required
async def edit_description_start(callback: CallbackQuery, state: FSMContext):
    """Начать редактирование описания услуг"""
    user_id = callback.from_user.id
    profile = db.get_executor_profile(user_id)
    
    current_desc = profile.get('description', 'Не указано')
    if len(current_desc) > 100:
        current_desc = current_desc[:100] + "..."
    
    await callback.message.answer(
        f"📝 РЕДАКТИРОВАНИЕ ОПИСАНИЯ УСЛУГ\n\n"
        f"Текущее описание: {current_desc}\n\n"
        f"Введите новое описание ваших услуг (минимум 20 символов):",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )
    
    await state.set_state(ProfileEditSimpleStates.edit_description)
    await callback.answer()


@router.message(ProfileEditSimpleStates.edit_description)
@executor_required
async def edit_description_process(message: Message, state: FSMContext):
    """Обработка нового описания"""
    description = message.text.strip()
    
    if len(description) < 20:
        await message.answer("❌ Описание слишком короткое. Минимум 20 символов:")
        return
    
    user_id = message.from_user.id
    
    # Сохраняем в БД
    db.update_executor_profile(user_id, description=description)
    
    await message.answer(
        "✅ Описание услуг обновлено!",
        reply_markup=back_to_profile_keyboard()
    )
    
    await state.clear()


@router.callback_query(F.data == "edit_experience_simple")
@executor_required
async def edit_experience_start(callback: CallbackQuery, state: FSMContext):
    """Начать редактирование опыта работы"""
    user_id = callback.from_user.id
    profile = db.get_executor_profile(user_id)
    
    current_exp = profile.get('experience_years', 0)
    
    await callback.message.answer(
        f"👷 РЕДАКТИРОВАНИЕ ОПЫТА РАБОТЫ\n\n"
        f"Текущий опыт: <b>{current_exp} лет</b>\n\n"
        f"Введите количество лет опыта (число):",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )
    
    await state.set_state(ProfileEditSimpleStates.edit_experience)
    await callback.answer()


@router.message(ProfileEditSimpleStates.edit_experience)
@executor_required
async def edit_experience_process(message: Message, state: FSMContext):
    """Обработка нового опыта"""
    try:
        experience = int(message.text.strip())
        
        if experience < 0:
            await message.answer("❌ Опыт не может быть отрицательным. Введите положительное число:")
            return
        
        if experience > 50:
            await message.answer("❌ Слишком большое значение. Введите реалистичное количество лет:")
            return
        
    except ValueError:
        await message.answer("❌ Введите число (например: 5):")
        return
    
    user_id = message.from_user.id
    
    # Сохраняем в БД
    db.update_executor_profile(user_id, experience_years=experience)
    
    await message.answer(
        f"✅ Опыт работы обновлен: <b>{experience} лет</b>",
        parse_mode="HTML",
        reply_markup=back_to_profile_keyboard()
    )
    
    await state.clear()


@router.callback_query(F.data == "edit_pricing_simple")
@executor_required
async def edit_pricing_start(callback: CallbackQuery, state: FSMContext):
    """Начать редактирование ценовой политики"""
    user_id = callback.from_user.id
    profile = db.get_executor_profile(user_id)
    
    min_price = profile.get('min_price', 1000)
    max_price = profile.get('max_price', 50000)
    
    await callback.message.answer(
        f"💰 РЕДАКТИРОВАНИЕ ЦЕНОВОЙ ПОЛИТИКИ\n\n"
        f"Текущие настройки:\n"
        f"• Минимальная цена: <b>{min_price} руб</b>\n"
        f"• Максимальная цена: <b>{max_price} руб</b>\n\n"
        f"Введите новый диапазон цен в формате:\n"
        f"<b>мин-макс</b>\n\n"
        f"Примеры:\n"
        f"• 1000-50000 (от 1000 до 50000 руб)\n"
        f"• 5000- (от 5000 руб)\n"
        f"• -20000 (до 20000 руб)\n\n"
        f"Или введите 0 для сброса.",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )
    
    await state.set_state(ProfileEditSimpleStates.edit_pricing)
    await callback.answer()


@router.message(ProfileEditSimpleStates.edit_pricing)
@executor_required
async def edit_pricing_process(message: Message, state: FSMContext):
    """Обработка новой ценовой политики"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    if text == "0":
        # Сброс фильтра
        db.update_executor_profile(user_id, min_price=None, max_price=None)
        await message.answer("✅ Ценовая политика сброшена", reply_markup=back_to_profile_keyboard())
    else:
        try:
            # Парсим диапазон
            if '-' in text:
                parts = text.split('-')
                if len(parts) == 2:
                    min_price = int(parts[0].strip()) if parts[0].strip() else None
                    max_price = int(parts[1].strip()) if parts[1].strip() else None
                    
                    # Валидация
                    if min_price and min_price < 0:
                        await message.answer("❌ Минимальная цена не может быть отрицательной")
                        return
                    
                    if max_price and max_price < 0:
                        await message.answer("❌ Максимальная цена не может быть отрицательной")
                        return
                    
                    if min_price and max_price and min_price > max_price:
                        await message.answer("❌ Минимальная цена не может быть больше максимальной")
                        return
                    
                    # Сохраняем
                    db.update_executor_profile(user_id, min_price=min_price, max_price=max_price)
                    
                    min_text = f"{min_price}" if min_price else "любая"
                    max_text = f"{max_price}" if max_price else "любая"
                    
                    await message.answer(
                        f"✅ Ценовая политика обновлена: {min_text}-{max_text} руб",
                        reply_markup=back_to_profile_keyboard()
                    )
                else:
                    await message.answer("❌ Неверный формат. Используйте: мин-макс")
                    return
            else:
                await message.answer("❌ Неверный формат. Используйте: мин-макс")
                return
        except ValueError:
            await message.answer("❌ Введите числа или 0 для сброса")
            return
    
    await state.clear()


# ========== ОБРАБОТКА СОЗДАНИЯ ПРЕДЛОЖЕНИЯ ==========

@router.callback_query(F.data.startswith("make_offer_"))
@executor_required
async def make_offer_start(callback: CallbackQuery, state: FSMContext):
    """Начало создания предложения"""
    order_id = callback.data.replace("make_offer_", "")
    
    # Проверяем, существует ли заказ
    order = db.get_order(order_id)
    if not order:
        await callback.answer("❌ Заказ не найден", show_alert=True)
        return
    
    # Проверяем, не предложил ли уже исполнитель
    existing_offers = db.get_offers_for_order(order_id)
    user_id = callback.from_user.id
    
    for offer in existing_offers:
        if offer['executor_id'] == user_id:
            await callback.answer(
                "✅ Вы уже отправили предложение по этому заказу!\n\n"
                "Используйте '💼 Мои предложения' для просмотра.",
                show_alert=True
            )
            return
    
    # Сохраняем данные в состоянии
    await state.update_data(
        order_id=order_id,
        order_price=order.get('desired_price')
    )
    
    # Просим ввести цену
    price_hint = ""
    if order.get('desired_price'):
        price_hint = f"\n\nЗаказчик указал желаемую цену: {order['desired_price']} ₽\n" \
                     f"Вы можете предложить свою цену (выше/ниже/такую же)."
    
    await callback.message.answer(
        f"💰 ПРЕДЛОЖЕНИЕ ЦЕНЫ\n\n"
        f"Заказ #{order_id[:8]}...\n"
        f"Описание: {order['description'][:100]}...{price_hint}\n\n"
        f"📝 Введите вашу цену (в рублях):",
        reply_markup=cancel_keyboard()
    )
    
    # Устанавливаем состояние для ввода цены
    await state.set_state(OfferStates.enter_price)
    
    await callback.answer()


@router.message(OfferStates.enter_price)
async def process_offer_price(message: Message, state: FSMContext):
    """Обработка введенной цены"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание предложения отменено.", reply_markup=main_menu('executor'))
        return
    
    try:
        price = int(message.text)
        if price <= 0:
            await message.answer("❌ Цена должна быть положительной. Введите корректную сумму:")
            return
    except ValueError:
        await message.answer("❌ Введите число (например: 5000):")
        return
    
    # Сохраняем цену и просим комментарий
    await state.update_data(offer_price=price)
    
    await message.answer(
        f"✅ Цена: {price} ₽\n\n"
        f"💬 Теперь введите комментарий к предложению (необязательно):\n\n"
        f"Примеры:\n"
        f"• 'Есть подходящая техника, сделаю завтра'\n"
        f"• 'Могу выполнить дешевле, потому что по пути'\n"
        f"• 'Есть опыт подобных работ'\n\n"
        f"Или просто напишите 'Без комментария'",
        reply_markup=skip_keyboard()
    )
    
    await state.set_state(OfferStates.enter_comment)


@router.message(OfferStates.enter_comment)
async def process_offer_comment(message: Message, state: FSMContext):
    """Обработка комментария к предложению"""
    comment = message.text.strip()
    
    if message.text == "⏭️ Пропустить":
        comment = ""
    elif message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание предложения отменено.", reply_markup=main_menu('executor'))
        return
    
    # Получаем все данные
    data = await state.get_data()
    order_id = data.get('order_id')
    price = data.get('offer_price')
    user_id = message.from_user.id
    
    # Сохраняем предложение в БД
    success = db.create_offer(order_id, user_id, price, comment)
    
    if success:
        # Получаем информацию о заказе
        order = db.get_order(order_id)
        if order:
            # Уведомляем заказчика (если это не он сам)
            if order['user_id'] != user_id:
                try:
                    await bot.send_message(
                        order['user_id'],
                        f"🎉 НОВОЕ ПРЕДЛОЖЕНИЕ!\n\n"
                        f"📦 Заказ #{order_id}\n"
                        f"💰 Цена: {price} ₽\n"
                        f"👷 Исполнитель: {message.from_user.full_name}\n\n"
                        f"Используйте '📋 Мои заказы' для просмотра всех предложений."
                    )
                except:
                    pass  # Не удалось отправить уведомление
        
        await message.answer(
            f"✅ ПРЕДЛОЖЕНИЕ ОТПРАВЛЕНО!\n\n"
            f"📦 Заказ #{order_id[:8]}...\n"
            f"💰 Ваша цена: {price} ₽\n"
            f"💬 Комментарий: {comment if comment else 'Нет комментария'}\n\n"
            f"📊 Заказчик получил уведомление и скоро выберет исполнителя.",
            reply_markup=main_menu('executor')
        )
    else:
        await message.answer(
            "❌ Ошибка при сохранении предложения. Попробуйте еще раз.",
            reply_markup=main_menu('executor')
        )
    
    # Очищаем состояние
    await state.clear()