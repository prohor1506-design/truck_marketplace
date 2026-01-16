"""
Хендлеры для регистрации пользователей через FSM
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.shared.states import RegistrationStates
from app.infrastructure.database.models import User, UserRole
from app.presentation.keyboards import (
    get_role_keyboard,
    get_yes_no_keyboard,
    get_skip_keyboard,
    get_cancel_keyboard,
    get_main_keyboard
)
from app.shared.logger import logger

# Создаем роутер для регистрации
router = Router()

# Функция валидации телефона
def validate_phone(phone: str) -> tuple[bool, str]:
    """Простая валидация российского телефона"""
    phone = phone.strip()
    
    # Удаляем все пробелы и дефисы
    phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    
    # Проверяем форматы
    if phone.startswith("+7") and len(phone) == 12:
        return True, phone
    elif phone.startswith("8") and len(phone) == 11:
        return True, "+7" + phone[1:]
    elif phone.startswith("7") and len(phone) == 11:
        return True, "+" + phone
    
    return False, "❌ Неверный формат телефона. Используйте: +79161234567 или 89161234567"


@router.message(Command("register"))
async def cmd_register(message: Message, state: FSMContext, session: AsyncSession):
    """
    Начало регистрации - проверяем, не зарегистрирован ли пользователь
    """
    logger.info(f"Начало регистрации для пользователя {message.from_user.id}")
    
    # Получаем пользователя из базы данных
    stmt = select(User).where(User.telegram_id == message.from_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        # Создаем пользователя если не найден
        user = User(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name or "",
            last_name=message.from_user.last_name
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info(f"Создан новый пользователь: {user.telegram_id}")
    
    # Проверяем, есть ли у пользователя уже роль
    if user.role and user.role != UserRole.CUSTOMER:
        await message.answer(
            f"✅ Вы уже зарегистрированы как <b>{user.get_role_display()}</b>!\n\n"
            f"Используйте /profile для просмотра профиля.",
            parse_mode="HTML"
        )
        return
    
    # Начинаем регистрацию
    await message.answer(
        "🎯 <b>Регистрация нового пользователя</b>\n\n"
        "Давайте зарегистрируем вас в системе.\n"
        "Для начала выберите вашу роль:",
        parse_mode="HTML",
        reply_markup=get_role_keyboard()
    )
    await state.set_state(RegistrationStates.select_role)
    
    # Сохраняем базовую информацию в состояние
    await state.update_data(
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        user_id=user.id  # Сохраняем ID пользователя из базы
    )


@router.callback_query(F.data.startswith("role_"))
async def select_role(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Обработка выбора роли
    """
    # Словарь соответствия callback_data и ролей
    role_map = {
        "role_customer": UserRole.CUSTOMER,
        "role_executor": UserRole.EXECUTOR,
        "role_owner": UserRole.OWNER
    }
    
    role_value = callback.data
    role = role_map.get(role_value)
    
    if not role:
        await callback.answer("❌ Неизвестная роль")
        return
    
    await state.update_data(role=role)
    
    # Показываем информацию о роли
    role_info = {
        UserRole.CUSTOMER: (
            "👤 <b>Вы выбрали роль: Заказчик</b>\n\n"
            "Вы можете:\n"
            "• Создавать заказы на перевозку\n"
            "• Находить исполнителей\n"
            "• Управлять своими заказами\n\n"
            "📝 Теперь введите ваше полное имя (как в паспорте):\n"
            "<i>Пример: Иван Иванов</i>"
        ),
        UserRole.EXECUTOR: (
            "🚚 <b>Вы выбрали роль: Исполнитель</b>\n\n"
            "Вы можете:\n"
            "• Находить заказы на перевозку\n"
            "• Откликаться на заказы\n"
            "• Управлять выполнением заказов\n\n"
            "📝 Теперь введите ваше полное имя (как в паспорте):\n"
            "<i>Пример: Иван Иванов</i>"
        ),
        UserRole.OWNER: (
            "🏗️ <b>Вы выбрали роль: Владелец техники</b>\n\n"
            "Вы можете:\n"
            "• Добавлять свою технику в аренду\n"
            "• Получать заявки на аренду\n"
            "• Управлять своим парком техники\n\n"
            "📝 Теперь введите ваше полное имя (как в паспорте):\n"
            "<i>Пример: Иван Иванов</i>"
        )
    }
    
    await callback.message.edit_text(
        role_info[role],
        parse_mode="HTML"
    )
    await state.set_state(RegistrationStates.enter_full_name)
    await callback.answer()


@router.message(RegistrationStates.enter_full_name)
async def enter_full_name(message: Message, state: FSMContext):
    """
    Обработка ввода имени
    """
    full_name = message.text.strip()
    
    if len(full_name) < 2:
        await message.answer("❌ Имя слишком короткое. Введите полное имя:")
        return
    
    # Разделяем имя и фамилию
    parts = full_name.split()
    if len(parts) >= 2:
        first_name, last_name = parts[0], " ".join(parts[1:])
    else:
        first_name, last_name = full_name, ""
    
    await state.update_data(
        full_name=full_name,
        first_name=first_name,
        last_name=last_name
    )
    
    await message.answer(
        "📱 Теперь введите ваш номер телефона:\n"
        "<i>Пример: +79161234567 или 89161234567</i>\n\n"
        "Это нужно для связи с вами при работе с заказами.",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(RegistrationStates.enter_phone)


@router.message(RegistrationStates.enter_phone)
async def enter_phone(message: Message, state: FSMContext):
    """
    Обработка ввода телефона
    """
    phone = message.text
    
    is_valid, result = validate_phone(phone)
    if not is_valid:
        await message.answer(result, reply_markup=get_cancel_keyboard())
        return
    
    await state.update_data(phone=result)
    
    data = await state.get_data()
    role = data.get('role')
    
    if role == UserRole.EXECUTOR or role == UserRole.OWNER:
        # Для исполнителей и владельцев техники спрашиваем название компании
        await message.answer(
            "🏢 Введите название вашей компании или ИП:\n"
            "<i>Если вы работаете как ИП или у вас есть компания</i>\n\n"
            "<i>Можно пропустить</i>",
            parse_mode="HTML",
            reply_markup=get_skip_keyboard()
        )
        await state.set_state(RegistrationStates.enter_company)
    else:
        # Для заказчиков пропускаем компанию
        await message.answer(
            "💬 Расскажите немного о себе:\n"
            "<i>Что обычно перевозите, какие требования и т.д.</i>\n\n"
            "<i>Можно пропустить</i>",
            parse_mode="HTML",
            reply_markup=get_skip_keyboard()
        )
        await state.set_state(RegistrationStates.enter_description)


@router.callback_query(F.data == "skip", RegistrationStates.enter_company)
async def skip_company(callback: CallbackQuery, state: FSMContext):
    """
    Пропуск ввода компании
    """
    await state.update_data(company_name=None)
    
    await callback.message.edit_text(
        "💬 Расскажите немного о себе или о вашей деятельности:\n"
        "<i>Что перевозите, какие услуги предлагаете и т.д.</i>\n\n"
        "<i>Можно пропустить</i>",
        parse_mode="HTML"
    )
    await callback.message.answer(
        "Введите описание или нажмите 'Пропустить':",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(RegistrationStates.enter_description)
    await callback.answer("Компания пропущена")


@router.message(RegistrationStates.enter_company)
async def enter_company(message: Message, state: FSMContext):
    """
    Обработка ввода названия компании
    """
    company_name = message.text.strip()
    
    if len(company_name) < 2:
        await message.answer(
            "❌ Название слишком короткое. Введите название компании:",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    await state.update_data(company_name=company_name)
    
    await message.answer(
        "💬 Расскажите немного о себе или о вашей деятельности:\n"
        "<i>Что перевозите, какие услуги предлагаете и т.д.</i>\n\n"
        "<i>Можно пропустить</i>",
        parse_mode="HTML",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(RegistrationStates.enter_description)


@router.callback_query(F.data == "skip", RegistrationStates.enter_description)
async def skip_description(callback: CallbackQuery, state: FSMContext):
    """
    Пропуск ввода описания
    """
    await state.update_data(description=None)
    await show_confirmation(callback, state)
    await callback.answer("Описание пропущено")


@router.message(RegistrationStates.enter_description)
async def enter_description(message: Message, state: FSMContext):
    """
    Обработка ввода описания
    """
    description = message.text.strip()
    
    if description and len(description) < 10:
        await message.answer(
            "❌ Описание слишком короткое. Напишите хотя бы 10 символов:",
            reply_markup=get_skip_keyboard()
        )
        return
    
    await state.update_data(description=description or None)
    await show_confirmation(message, state)


async def show_confirmation(event: Message | CallbackQuery, state: FSMContext):
    """
    Показ подтверждения регистрации
    """
    data = await state.get_data()
    
    # Формируем текст подтверждения
    role_display = {
        UserRole.CUSTOMER: "👤 Заказчик",
        UserRole.EXECUTOR: "🚚 Исполнитель",
        UserRole.OWNER: "🏗️ Владелец техники"
    }
    
    confirmation_text = (
        "✅ <b>Проверьте ваши данные:</b>\n\n"
        f"<b>Роль:</b> {role_display.get(data['role'], 'Не указана')}\n"
        f"<b>Имя:</b> {data.get('full_name', 'Не указано')}\n"
        f"<b>Телефон:</b> {data.get('phone', 'Не указан')}\n"
    )
    
    if data.get('company_name'):
        confirmation_text += f"<b>Компания:</b> {data['company_name']}\n"
    
    if data.get('description'):
        desc = data['description'][:100] + ("..." if len(data['description']) > 100 else "")
        confirmation_text += f"<b>Описание:</b> {desc}\n"
    
    confirmation_text += "\n<i>Всё верно?</i>"
    
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(
            confirmation_text,
            parse_mode="HTML",
            reply_markup=get_yes_no_keyboard()
        )
    else:
        await event.answer(
            confirmation_text,
            parse_mode="HTML",
            reply_markup=get_yes_no_keyboard()
        )
    
    await state.set_state(RegistrationStates.confirm)


@router.callback_query(F.data == "confirm_yes", RegistrationStates.confirm)
async def confirm_registration(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Подтверждение и сохранение пользователя
    """
    data = await state.get_data()
    
    # Находим пользователя в базе
    user_id = data.get('telegram_id')
    if not user_id:
        await callback.answer("❌ Ошибка: пользователь не найден")
        return
    
    stmt = select(User).where(User.telegram_id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        # Создаем нового пользователя
        user = User(
            telegram_id=data['telegram_id'],
            username=data.get('username'),
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name'),
            phone=data.get('phone'),
            role=data['role']
        )
        session.add(user)
    else:
        # Обновляем существующего
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.phone = data.get('phone')
        user.role = data['role']
    
    await session.commit()
    await session.refresh(user)  # Обновляем объект user
    
    logger.info(f"Пользователь {user.telegram_id} зарегистрирован как {user.role.value}")
    
    # Отправляем подтверждение
    role_specific_message = {
        UserRole.CUSTOMER: (
            "🎉 <b>Регистрация завершена!</b>\n\n"
            "Теперь вы можете:\n"
            "• Создавать заказы на перевозку\n"
            "• Просматривать доступных исполнителей\n"
            "• Управлять своими заказами\n\n"
            "Используйте кнопки ниже для навигации 👇"
        ),
        UserRole.EXECUTOR: (
            "🎉 <b>Регистрация завершена!</b>\n\n"
            "Теперь вы можете:\n"
            "• Просматривать доступные заказы\n"
            "• Откликаться на заказы\n"
            "• Управлять своими предложениями\n\n"
            "Используйте кнопки ниже для навигации 👇"
        ),
        UserRole.OWNER: (
            "🎉 <b>Регистрация завершена!</b>\n\n"
            "Теперь вы можете:\n"
            "• Добавлять свою технику в аренду\n"
            "• Получать заявки на аренду\n"
            "• Управлять своим парком техники\n\n"
            "Используйте кнопки ниже для навигации 👇"
        )
    }
    
    await callback.message.edit_text(
        role_specific_message[user.role],
        parse_mode="HTML"
    )
    
    # Показываем основную клавиатуру
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=get_main_keyboard()
    )
    
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "confirm_no", RegistrationStates.confirm)
async def restart_registration(callback: CallbackQuery, state: FSMContext):
    """
    Начать регистрацию заново
    """
    await callback.message.edit_text(
        "🔄 Начнем регистрацию заново.\n\n"
        "Выберите вашу роль:",
        parse_mode="HTML",
        reply_markup=get_role_keyboard()
    )
    await state.set_state(RegistrationStates.select_role)
    await callback.answer()


@router.callback_query(F.data == "cancel")
@router.message(Command("cancel"))
async def cancel_handler(event: Message | CallbackQuery, state: FSMContext):
    """
    Отмена любого FSM процесса
    """
    current_state = await state.get_state()
    
    if current_state:
        await state.clear()
    
    message = event if isinstance(event, Message) else event.message
    
    await message.answer(
        "❌ Действие отменено.\n"
        "Вы можете начать заново с помощью /register",
        reply_markup=get_main_keyboard()
    )
    
    if isinstance(event, CallbackQuery):
        await event.answer()


@router.message(StateFilter(RegistrationStates))
async def handle_wrong_input(message: Message):
    """
    Обработка неправильного ввода во время регистрации
    """
    await message.answer(
        "❌ Пожалуйста, следуйте инструкциям.\n"
        "Если хотите прервать регистрацию, используйте /cancel"
    )