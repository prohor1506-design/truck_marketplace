# handlers/profile_edit.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db
from keyboards import (
    executor_profile_keyboard, 
    cancel_keyboard, 
    executor_registration_steps,
    back_to_profile_keyboard
)
from states import ProfileEditStates
from utils import validate_phone

router = Router()

# ========== МЕНЮ РЕДАКТИРОВАНИЯ ==========

@router.callback_query(F.data == "executor_edit_menu")
async def executor_edit_menu(callback: CallbackQuery):
    """Меню редактирования профиля"""
    user_id = callback.from_user.id
    profile = db.get_executor_profile(user_id)
    
    if not profile:
        await callback.answer("❌ Профиль не найден")
        return
    
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="🏢 Название компании",
        callback_data="edit_company_name_start"
    ))
    builder.add(InlineKeyboardButton(
        text="📞 Телефон",
        callback_data="edit_phone_start"
    ))
    
    builder.add(InlineKeyboardButton(
        text="📝 Описание услуг",
        callback_data="edit_description_start"
    ))
    builder.add(InlineKeyboardButton(
        text="👷 Опыт работы",
        callback_data="edit_experience_start"
    ))
    
    builder.add(InlineKeyboardButton(
        text="💰 Ценовая политика",
        callback_data="edit_pricing_start"
    ))
    
    builder.add(InlineKeyboardButton(
        text="⬅️ Назад к профилю",
        callback_data=f"executor_view_{user_id}"
    ))
    
    builder.adjust(2, 2, 1, 1)
    
    await callback.message.edit_text(
        "✏️ РЕДАКТИРОВАНИЕ ПРОФИЛЯ\n\n"
        "Выберите, что хотите изменить:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


# ========== РЕДАКТИРОВАНИЕ НАЗВАНИЯ КОМПАНИИ ==========

@router.callback_query(F.data == "edit_company_name_start")
async def edit_company_name_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования названия компании"""
    user_id = callback.from_user.id
    profile = db.get_executor_profile(user_id)
    
    current_name = profile.get('company_name', 'Не указано')
    
    await callback.message.answer(
        f"🏢 РЕДАКТИРОВАНИЕ НАЗВАНИЯ КОМПАНИИ\n\n"
        f"Текущее название: <b>{current_name}</b>\n\n"
        f"Введите новое название компании или ИП:",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )
    
    await state.set_state(ProfileEditStates.edit_company_name)
    await callback.answer()


@router.message(ProfileEditStates.edit_company_name)
async def process_edit_company_name(message: Message, state: FSMContext):
    """Обработка нового названия компании"""
    user_id = message.from_user.id
    new_name = message.text.strip()
    
    if len(new_name) < 2:
        await message.answer(
            "❌ Название слишком короткое. Введите название (минимум 2 символа):",
            reply_markup=cancel_keyboard()
        )
        return
    
    db.update_executor_profile(user_id, company_name=new_name)
    
    await message.answer(
        f"✅ Название компании обновлено: <b>{new_name}</b>",
        parse_mode="HTML",
        reply_markup=back_to_profile_keyboard()
    )
    
    await state.clear()


# ========== РЕДАКТИРОВАНИЕ ТЕЛЕФОНА ==========

@router.callback_query(F.data == "edit_phone_start")
async def edit_phone_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования телефона"""
    user_id = callback.from_user.id
    profile = db.get_executor_profile(user_id)
    
    current_phone = profile.get('phone', 'Не указан')
    
    await callback.message.answer(
        f"📞 РЕДАКТИРОВАНИЕ ТЕЛЕФОНА\n\n"
        f"Текущий телефон: <b>{current_phone}</b>\n\n"
        f"Введите новый контактный телефон:\n"
        f"Формат: +7XXXXXXXXXX или 8XXXXXXXXXX",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )
    
    await state.set_state(ProfileEditStates.edit_phone)
    await callback.answer()


@router.message(ProfileEditStates.edit_phone)
async def process_edit_phone(message: Message, state: FSMContext):
    """Обработка нового телефона"""
    user_id = message.from_user.id
    phone = message.text.strip()
    is_valid, result = validate_phone(phone)
    
    if not is_valid:
        await message.answer(result, reply_markup=cancel_keyboard())
        return
    
    db.update_executor_profile(user_id, phone=result)
    
    await message.answer(
        f"✅ Телефон обновлен: <b>{result}</b>",
        parse_mode="HTML",
        reply_markup=back_to_profile_keyboard()
    )
    
    await state.clear()


# ========== РЕДАКТИРОВАНИЕ ОПИСАНИЯ УСЛУГ ==========

@router.callback_query(F.data == "edit_description_start")
async def edit_description_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования описания услуг"""
    user_id = callback.from_user.id
    profile = db.get_executor_profile(user_id)
    
    current_description = profile.get('description', 'Не указано')
    if len(current_description) > 100:
        preview = current_description[:100] + "..."
    else:
        preview = current_description
    
    await callback.message.answer(
        f"📝 РЕДАКТИРОВАНИЕ ОПИСАНИЯ УСЛУГ\n\n"
        f"Текущее описание: <b>{preview}</b>\n\n"
        f"Введите новое описание ваших услуг:\n"
        f"Пример: 'Грузоперевозки по городу и области. Есть газели, фуры, рефрижераторы.'\n"
        f"Минимум 20 символов.",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )
    
    await state.set_state(ProfileEditStates.edit_description)
    await callback.answer()


@router.message(ProfileEditStates.edit_description)
async def process_edit_description(message: Message, state: FSMContext):
    """Обработка нового описания"""
    user_id = message.from_user.id
    description = message.text.strip()
    
    if len(description) < 20:
        await message.answer(
            "❌ Описание слишком короткое. Минимум 20 символов.\n"
            "Опишите подробнее, какие услуги вы предоставляете:",
            reply_markup=cancel_keyboard()
        )
        return
    
    db.update_executor_profile(user_id, description=description)
    
    await message.answer(
        f"✅ Описание услуг обновлено!\n\n"
        f"<b>Краткий просмотр:</b>\n"
        f"{description[:100]}...",
        parse_mode="HTML",
        reply_markup=back_to_profile_keyboard()
    )
    
    await state.clear()


# ========== РЕДАКТИРОВАНИЕ ОПЫТА РАБОТЫ ==========

@router.callback_query(F.data == "edit_experience_start")
async def edit_experience_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования опыта работы"""
    user_id = callback.from_user.id
    profile = db.get_executor_profile(user_id)
    
    current_experience = profile.get('experience_years', 0)
    
    await callback.message.answer(
        f"👷 РЕДАКТИРОВАНИЕ ОПЫТА РАБОТЫ\n\n"
        f"Текущий опыт: <b>{current_experience} лет</b>\n\n"
        f"Какой у вас опыт работы?\n"
        f"Выберите или введите количество лет:",
        parse_mode="HTML",
        reply_markup=executor_registration_steps("experience")
    )
    
    await state.set_state(ProfileEditStates.edit_experience)
    await callback.answer()


@router.message(ProfileEditStates.edit_experience)
async def process_edit_experience(message: Message, state: FSMContext):
    """Обработка нового опыта работы"""
    user_id = message.from_user.id
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
        try:
            import re
            numbers = re.findall(r'\d+', experience)
            if numbers:
                experience_years = int(numbers[0])
        except:
            experience_years = 0
    
    db.update_executor_profile(user_id, experience_years=experience_years)
    
    await message.answer(
        f"✅ Опыт работы обновлен: <b>{experience_years} лет</b>",
        parse_mode="HTML",
        reply_markup=back_to_profile_keyboard()
    )
    
    await state.clear()


# ========== РЕДАКТИРОВАНИЕ ЦЕНОВОЙ ПОЛИТИКИ ==========

@router.callback_query(F.data == "edit_pricing_start")
async def edit_pricing_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования ценовой политики"""
    user_id = callback.from_user.id
    profile = db.get_executor_profile(user_id)
    
    min_price = profile.get('min_price', 1000)
    max_price = profile.get('max_price', 50000)
    
    await callback.message.answer(
        f"💰 РЕДАКТИРОВАНИЕ ЦЕНОВОЙ ПОЛИТИКИ\n\n"
        f"Текущие настройки:\n"
        f"• Минимальная цена: <b>{min_price} ₽</b>\n"
        f"• Максимальная цена: <b>{max_price} ₽</b>\n\n"
        f"Введите новый диапазон цен в формате:\n"
        f"<b>мин-макс</b>\n\n"
        f"Примеры:\n"
        f"• 1000-5000 (от 1000 до 5000 руб)\n"
        f"• 5000- (от 5000 руб)\n"
        f"• -20000 (до 20000 руб)\n\n"
        f"Или введите 0 для сброса.",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )
    
    await state.set_state(ProfileEditStates.edit_pricing)
    await callback.answer()


@router.message(ProfileEditStates.edit_pricing)
async def process_edit_pricing(message: Message, state: FSMContext):
    """Обработка новой ценовой политики"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    if text == "0":
        db.update_executor_profile(user_id, min_price=None, max_price=None)
        await message.answer(
            "✅ Ценовая политика сброшена",
            reply_markup=back_to_profile_keyboard()
        )
    else:
        try:
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


# ========== ОБРАБОТКА ОТМЕНЫ ==========

@router.message(F.text == "❌ Отмена", ProfileEditStates.edit_company_name)
@router.message(F.text == "❌ Отмена", ProfileEditStates.edit_phone)
@router.message(F.text == "❌ Отмена", ProfileEditStates.edit_description)
@router.message(F.text == "❌ Отмена", ProfileEditStates.edit_experience)
@router.message(F.text == "❌ Отмена", ProfileEditStates.edit_pricing)
async def cancel_edit(message: Message, state: FSMContext):
    """Отмена редактирования"""
    await message.answer(
        "❌ Редактирование отменено.",
        reply_markup=back_to_profile_keyboard()
    )
    
    await state.clear()