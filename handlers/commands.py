# handlers/commands.py

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import os

from database import db
from keyboards import main_menu, cancel_keyboard
from states import ExecutorRegistrationStates

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name
    
    # Очищаем состояние на всякий случай
    await state.clear()
    
    # Добавляем/обновляем пользователя
    db.add_user(user_id, username, full_name)
    
    # Получаем информацию о пользователе
    user_info = db.get_user(user_id)
    role = user_info['role'] if user_info else 'customer'
    
    await message.answer(
        f"👋 Добро пожаловать, {full_name}!\n\n"
        f"🤖 <b>Биржа грузоперевозок и спецтехники</b>\n\n"
        f"Вы вошли как: <b>{'Заказчик' if role == 'customer' else 'Исполнитель'}</b>\n\n"
        f"Используйте кнопки ниже для навигации:",
        parse_mode="HTML",
        reply_markup=main_menu(role)
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = (
        "🤖 <b>БИРЖА ГРУЗОПЕРЕВОЗОК - ПОМОЩЬ</b>\n\n"
        
        "<b>👷 ДЛЯ ЗАКАЗЧИКОВ:</b>\n"
        "• 📦 Создать заказ - разместить задание\n"
        "• 📋 Мои заказы - просмотреть свои заказы\n"
        "• 👤 Профиль - информация о вас\n"
        "• 👷 Стать исполнителем - переключиться в режим исполнителя\n\n"
        
        "<b>🛠️ ДЛЯ ИСПОЛНИТЕЛЕЙ:</b>\n"
        "• 📋 Доступные заказы - поиск работы\n"
        "• ⚙️ Мой профиль - управление профилем\n"
        "• 🚛 Моя техника - управление техникой\n"
        "• 💼 Мои предложения - ваши предложения\n"
        "• 🔍 Настройки фильтров - фильтры поиска\n"
        "• 📦 Вернуться в заказчики - переключиться обратно\n\n"
        
        "<b>📋 КОМАНДЫ:</b>\n"
        "/start - перезапуск бота\n"
        "/help - эта справка\n"
        "/profile - ваш профиль\n"
        "/executor - стать исполнителем\n"
        "/customer - стать заказчиком\n"
        "/register - быстрая регистрация исполнителя\n"
        "/fill_profile - начать заполнение профиля\n\n"
        
        "<b>📝 РЕГИСТРАЦИЯ ИСПОЛНИТЕЛЯ (8 шагов):</b>\n"
        "1. Название компании\n"
        "2. Контактный телефон\n"
        "3. Описание услуг\n"
        "4. Опыт работы\n"
        "5. Лицензия (необязательно)\n"
        "6. Страховка (необязательно)\n"
        "7. Местоположение\n"
        "8. Радиус работы\n\n"
        
        "❓ <b>Проблемы?</b>\n"
        "Если что-то не работает, используйте /start\n"
        "Или напишите администратору."
    )
    
    await message.answer(help_text, parse_mode="HTML")


@router.message(Command("profile"))
async def cmd_profile(message: Message):
    """Обработчик команды /profile"""
    user_id = message.from_user.id
    user_info = db.get_user(user_id)
    
    if not user_info:
        await message.answer("❌ Вы не зарегистрированы. Используйте /start")
        return
    
    role_text = "Заказчик" if user_info['role'] == 'customer' else "Исполнитель"
    
    profile_text = (
        f"👤 <b>ВАШ ПРОФИЛЬ</b>\n\n"
        f"<b>Имя:</b> {user_info['full_name']}\n"
        f"<b>Логин:</b> @{user_info['username'] or 'Не указан'}\n"
        f"<b>Роль:</b> {role_text}\n"
        f"<b>Рейтинг:</b> {user_info['rating']} ⭐\n"
        f"<b>Зарегистрирован:</b> {user_info['created_at'][:10]}"
    )
    
    await message.answer(profile_text, parse_mode="HTML", reply_markup=main_menu(user_info['role']))


@router.message(Command("executor"))
async def cmd_executor(message: Message):
    """Стать исполнителем"""
    user_id = message.from_user.id
    user_info = db.get_user(user_id)
    
    if not user_info:
        await message.answer("❌ Вы не зарегистрированы. Используйте /start")
        return
    
    # Меняем роль на исполнителя
    db.update_user_role(user_id, 'executor')
    
    await message.answer(
        "✅ Теперь вы исполнитель!\n\n"
        "Заполните профиль, чтобы начать получать заказы.\n\n"
        "Используйте:\n"
        "• Кнопку '⚙️ Мой профиль' в меню ниже\n"
        "• Или команду /fill_profile",
        reply_markup=main_menu('executor')
    )


@router.message(Command("customer"))
async def cmd_customer(message: Message):
    """Стать заказчиком"""
    user_id = message.from_user.id
    user_info = db.get_user(user_id)
    
    if not user_info:
        await message.answer("❌ Вы не зарегистрированы. Используйте /start")
        return
    
    # Меняем роль на заказчика
    db.update_user_role(user_id, 'customer')
    
    await message.answer(
        "✅ Теперь вы заказчик!\n\n"
        "Используйте меню ниже для создания заказов:",
        reply_markup=main_menu('customer')
    )


@router.message(Command("register"))
async def cmd_register(message: Message):
    """Быстрая регистрация исполнителя (альтернатива через команду)"""
    user_id = message.from_user.id
    user_info = db.get_user(user_id)
    
    if not user_info:
        await message.answer("❌ Вы не зарегистрированы. Используйте /start")
        return
    
    # Меняем роль на исполнителя
    db.update_user_role(user_id, 'executor')
    
    # Создаем профиль исполнителя
    db.create_executor_profile(user_id)
    
    await message.answer(
        "👷 БЫСТРАЯ РЕГИСТРАЦИЯ ИСПОЛНИТЕЛЯ\n\n"
        "✅ Вы переведены в режим исполнителя.\n"
        "✅ Создан пустой профиль.\n\n"
        "Теперь заполните ваш профиль:\n\n"
        "Используйте:\n"
        "1. Кнопку '⚙️ Мой профиль' в меню ниже\n"
        "2. Или команду /fill_profile\n"
        "3. Или нажмите кнопку '📝 Заполнить профиль'",
        reply_markup=main_menu('executor')
    )


@router.message(Command("fill_profile"))
async def cmd_fill_profile(message: Message, state: FSMContext):
    """Прямой переход к заполнению профиля исполнителя"""
    user_id = message.from_user.id
    user_info = db.get_user(user_id)
    
    if not user_info:
        await message.answer("❌ Вы не зарегистрированы. Используйте /start")
        return
    
    if user_info['role'] != 'executor':
        await message.answer(
            "❌ Вы не исполнитель.\n"
            "Сначала используйте /executor или /register",
            reply_markup=main_menu(user_info['role'])
        )
        return
    
    # Проверяем, заполнен ли уже профиль
    executor_profile = db.get_executor_profile(user_id)
    
    if executor_profile and executor_profile.get('company_name'):
        await message.answer(
            "✅ У вас уже заполнен профиль исполнителя!\n\n"
            "Используйте '⚙️ Мой профиль' для просмотра и редактирования.",
            reply_markup=main_menu('executor')
        )
        return
    
    # Начинаем регистрацию
    await message.answer(
        "👷 РЕГИСТРАЦИЯ ИСПОЛНИТЕЛЯ\n\n"
        "Заполните информацию о вашей компании/сервисе.\n"
        "Это поможет заказчикам доверять вам.\n\n"
        "<b>Шаг 1 из 8:</b> Введите название вашей компании или ИП:",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )
    
    await state.set_state(ExecutorRegistrationStates.enter_company_name)


@router.message(Command("status"))
async def cmd_status(message: Message):
    """Проверить статус системы"""
    user_id = message.from_user.id
    user_info = db.get_user(user_id)
    
    if not user_info:
        status_text = "❌ Вы не зарегистрированы"
    else:
        role_text = "Заказчик" if user_info['role'] == 'customer' else "Исполнитель"
        
        # Проверяем базу данных
        try:
            db.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = db.cursor.fetchall()
            table_count = len(tables)
            
            # Проверяем таблицу users
            db.cursor.execute("SELECT COUNT(*) as count FROM users")
            users_count = db.cursor.fetchone()['count']
            
            # Проверяем таблицу executor_profiles
            db.cursor.execute("SELECT COUNT(*) as count FROM executor_profiles")
            executors_count = db.cursor.fetchone()['count']
            
            status_text = (
                f"📊 <b>СТАТУС СИСТЕМЫ</b>\n\n"
                f"<b>Ваш статус:</b>\n"
                f"• ID: {user_id}\n"
                f"• Имя: {user_info['full_name']}\n"
                f"• Роль: {role_text}\n"
                f"• Рейтинг: {user_info['rating']} ⭐\n\n"
                f"<b>База данных:</b>\n"
                f"• Таблиц: {table_count}\n"
                f"• Пользователей: {users_count}\n"
                f"• Исполнителей: {executors_count}\n\n"
                f"<b>Файлы:</b>\n"
                f"• marketplace.db: {'✅ Существует' if os.path.exists('marketplace.db') else '❌ Отсутствует'}"
            )
            
        except Exception as e:
            status_text = f"❌ Ошибка проверки БД: {str(e)}"
    
    await message.answer(status_text, parse_mode="HTML")


@router.message(Command("debug_profile"))
async def cmd_debug_profile(message: Message):
    """Отладочная информация о профиле"""
    user_id = message.from_user.id
    user_info = db.get_user(user_id)
    
    if not user_info:
        await message.answer("❌ Вы не зарегистрированы. Используйте /start")
        return
    
    # Получаем данные профиля
    executor_profile = db.get_executor_profile(user_id)
    
    debug_text = (
        f"🔍 <b>ОТЛАДКА ПРОФИЛЯ</b>\n\n"
        f"<b>Основная информация:</b>\n"
        f"• ID: {user_id}\n"
        f"• Username: @{user_info.get('username', 'нет')}\n"
        f"• Имя: {user_info.get('full_name', 'нет')}\n"
        f"• Роль: {user_info.get('role', 'нет')}\n"
        f"• Рейтинг: {user_info.get('rating', 'нет')}\n\n"
        f"<b>Профиль исполнителя:</b>\n"
        f"• Существует: {'✅ Да' if executor_profile else '❌ Нет'}\n"
    )
    
    if executor_profile:
        debug_text += f"• ID профиля: {executor_profile.get('id', 'нет')}\n"
        
        # Проверяем заполненность полей
        fields_to_check = [
            ('company_name', 'Название компании'),
            ('phone', 'Телефон'),
            ('description', 'Описание'),
            ('experience_years', 'Опыт'),
            ('work_radius_km', 'Радиус работы')
        ]
        
        debug_text += f"\n<b>Заполненность полей:</b>\n"
        for field_key, field_name in fields_to_check:
            value = executor_profile.get(field_key)
            status = "✅" if value else "❌"
            debug_text += f"• {status} {field_name}: {value if value else 'Не заполнено'}\n"
        
        # Показываем все поля профиля
        debug_text += f"\n<b>Все поля профиля:</b>\n"
        for key, value in executor_profile.items():
            if value and len(str(value)) < 50:  # Показываем только короткие значения
                debug_text += f"• {key}: {value}\n"
    
    # Кнопка для принудительного начала регистрации
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📝 Начать регистрацию", 
            callback_data=f"executor_register_{user_id}"
        )]
    ])
    
    await message.answer(debug_text, parse_mode="HTML", reply_markup=keyboard)


# ========== ПРОСТАЯ КОМАНДА ДЛЯ ПЕРЕСОЗДАНИЯ БД ==========

@router.message(Command("recreate_db"))
async def cmd_recreate_db(message: Message):
    """Простая команда для пересоздания БД"""
    from config import ADMIN_ID
    
    user_id = message.from_user.id
    
    # Проверяем права администратора
    if user_id != ADMIN_ID:
        await message.answer("❌ У вас нет прав для этой команды")
        return
    
    # Простое сообщение с инструкциями
    await message.answer(
        "🔄 <b>ПЕРЕСОЗДАНИЕ БАЗЫ ДАННЫХ</b>\n\n"
        "Чтобы пересоздать базу данных:\n\n"
        "1. Остановите бота (Ctrl+C)\n"
        "2. Удалите файл <code>marketplace.db</code>\n"
        "3. Запустите бота снова: <code>python main.py</code>\n\n"
        "Бот автоматически создаст новые таблицы при запуске.",
        parse_mode="HTML"
    )
    from database import db
from keyboards import main_menu

@router.callback_query(F.data == "main_menu")
async def cmd_main_menu_callback(callback: CallbackQuery):
    """Обработчик кнопки 'В главное меню'"""
    user_id = callback.from_user.id
    user_info = db.get_user(user_id)
    
    role = user_info['role'] if user_info else 'customer'
    
    try:
        await callback.message.edit_text(
            "🏠 Вы вернулись в главное меню!",
            reply_markup=main_menu(role)
        )
    except:
        await callback.message.answer(
            "🏠 Вы вернулись в главное меню!",
            reply_markup=main_menu(role)
        )
    
    await callback.answer()