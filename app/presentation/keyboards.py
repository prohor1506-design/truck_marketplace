"""
Клавиатуры для бота
"""

from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from app.infrastructure.database.models import UserRole


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Основная клавиатура меню"""
    builder = ReplyKeyboardBuilder()
    
    builder.add(KeyboardButton(text="👤 Мой профиль"))
    builder.add(KeyboardButton(text="📊 Рынок заказов"))
    builder.add(KeyboardButton(text="🚛 Моя техника"))
    builder.add(KeyboardButton(text="➕ Создать заказ"))
    builder.add(KeyboardButton(text="🔍 Найти заказ"))
    
    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=False
    )


def get_role_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора роли при регистрации"""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="👤 Заказчик", 
        callback_data="role_customer"
    )
    builder.button(
        text="🚚 Исполнитель", 
        callback_data="role_executor"
    )
    builder.button(
        text="🏗️ Владелец техники", 
        callback_data="role_owner"
    )
    
    builder.adjust(1)  # По одной кнопке в строке
    return builder.as_markup()


def get_yes_no_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура Да/Нет"""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="✅ Да, всё верно", 
        callback_data="confirm_yes"
    )
    builder.button(
        text="❌ Нет, исправить", 
        callback_data="confirm_no"
    )
    
    builder.adjust(1)
    return builder.as_markup()


def get_skip_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой 'Пропустить'"""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="⏭️ Пропустить", 
        callback_data="skip"
    )
    
    return builder.as_markup()


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой 'Отмена'"""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="❌ Отменить регистрацию", 
        callback_data="cancel"
    )
    
    return builder.as_markup()