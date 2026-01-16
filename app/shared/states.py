"""
Состояния (FSM) для бота
"""

from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    """Состояния для регистрации пользователя"""
    select_role = State()          # Выбор роли
    enter_full_name = State()      # Ввод имени (переименовал для ясности)
    enter_phone = State()          # Ввод телефона
    enter_company = State()        # Ввод названия компании
    enter_description = State()    # Описание/о себе
    confirm = State()              # Подтверждение данных