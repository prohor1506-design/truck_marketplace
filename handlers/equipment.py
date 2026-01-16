# handlers/equipment.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json
import re

from database import db
from keyboards import (
    main_menu,
    equipment_types_keyboard,
    equipment_subtype_keyboard,
    confirm_equipment_keyboard,
    equipment_features_keyboard,
    equipment_management_keyboard,
    cancel_keyboard,
    skip_keyboard,
    back_to_profile_keyboard,
    executor_profile_keyboard  # Добавляем этот импорт
)
from states import EquipmentRegistrationStates, EquipmentManagementStates

# Создаем роутер для управления техникой
router = Router()

# ========== ОБРАБОТКА КНОПКИ "НАЗАД К ПРОФИЛЮ" ==========

@router.callback_query(F.data == "back_to_profile")
async def back_to_profile_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Назад к профилю'"""
    user_id = callback.from_user.id
    user_info = db.get_user(user_id)
    
    if user_info and user_info['role'] == 'executor':
        executor_profile = db.get_executor_profile(user_id)
        has_full_profile = bool(executor_profile and executor_profile.get('company_name'))
        
        await callback.message.answer(
            "👷 ВАШ ПРОФИЛЬ ИСПОЛНИТЕЛЯ",
            reply_markup=executor_profile_keyboard(user_id, has_full_profile)
        )
    else:
        # Если пользователь не исполнитель, показываем главное меню
        from keyboards import main_menu
        await callback.message.answer(
            "👤 Ваш профиль",
            reply_markup=main_menu('customer')
        )
    
    await callback.answer()

# ========== CALLBACK ОБРАБОТЧИКИ ДЛЯ ДОБАВЛЕНИЯ ТЕХНИКИ ==========

@router.callback_query(F.data.in_(["eq_add_first", "eq_add_new"]))
async def start_add_equipment(callback: CallbackQuery, state: FSMContext):
    """Начало добавления новой техники"""
    user_id = callback.from_user.id
    user_info = db.get_user(user_id)
    
    if not user_info or user_info['role'] != 'executor':
        await callback.answer("❌ Вы не исполнитель", show_alert=True)
        return
    
    await state.clear()
    await state.set_state(EquipmentRegistrationStates.select_equipment_type)
    
    # Инициализируем данные для техники
    await state.update_data(
        executor_id=user_id,
        features={}  # Словарь для особенностей
    )
    
    await callback.message.answer(
        "🚛 ДОБАВЛЕНИЕ ТЕХНИКИ\n\n"
        "🔄 Шаг 1 из 8: ВЫБЕРИТЕ ТИП ТЕХНИКИ",  # Изменили с 7 на 8
        reply_markup=equipment_types_keyboard()
    )
    await callback.answer()

# ========== FSM ДЛЯ ДОБАВЛЕНИЯ ТЕХНИКИ (8 ШАГОВ) ==========

# ШАГ 1: Выбор типа техники
@router.callback_query(F.data.startswith("eq_type_"), EquipmentRegistrationStates.select_equipment_type)
async def select_equipment_type(callback: CallbackQuery, state: FSMContext):
    """Выбор типа техники"""
    equipment_type = callback.data.replace("eq_type_", "")
    
    # Сохраняем тип
    await state.update_data(equipment_type=equipment_type)
    
    # Переходим к выбору подтипа
    await state.set_state(EquipmentRegistrationStates.enter_subtype)
    
    # Получаем название типа для отображения
    type_names = {
        'truck': 'грузовик',
        'gazelle': 'газель',
        'truck_large': 'фура',
        'refrigerator': 'рефрижератор',
        'excavator': 'экскаватор',
        'crane': 'кран',
        'loader': 'погрузчик',
        'bulldozer': 'бульдозер',
        'dump_truck': 'самосвал',
        'tractor': 'трактор'
    }
    
    type_name = type_names.get(equipment_type, equipment_type)
    
    await callback.message.answer(
        f"✅ Вы выбрали: {type_name}\n\n"
        "🔄 Шаг 2 из 8: ВЫБЕРИТЕ ПОДТИП",  # Изменили с 7 на 8
        reply_markup=equipment_subtype_keyboard(equipment_type)
    )
    await callback.answer()

# Обработчик возврата к выбору типа
@router.callback_query(F.data == "back_to_equipment_types", EquipmentRegistrationStates.enter_subtype)
async def back_to_equipment_type(callback: CallbackQuery, state: FSMContext):
    """Вернуться к выбору типа техники"""
    await state.set_state(EquipmentRegistrationStates.select_equipment_type)
    await callback.message.answer(
        "🔄 Шаг 1 из 8: ВЫБЕРИТЕ ТИП ТЕХНИКИ",  # Изменили с 7 на 8
        reply_markup=equipment_types_keyboard()
    )
    await callback.answer()

# ШАГ 2: Выбор подтипа
@router.callback_query(F.data.startswith("eq_subtype_"), EquipmentRegistrationStates.enter_subtype)
async def select_subtype(callback: CallbackQuery, state: FSMContext):
    """Выбор подтипа техники"""
    if callback.data == "eq_subtype_custom":
        # Пользователь хочет ввести свой вариант
        await callback.message.answer(
            "📝 Введите свой вариант подтипа техники:",
            reply_markup=cancel_keyboard()
        )
        await callback.answer()
        return
    
    subtype = callback.data.replace("eq_subtype_", "")
    await state.update_data(subtype=subtype)
    await state.set_state(EquipmentRegistrationStates.enter_brand_model)
    
    await callback.message.answer(
        f"✅ Подтип: {subtype}\n\n"
        "🔄 Шаг 3 из 8: ВВЕДИТЕ МАРКУ И МОДЕЛЬ\n\n"  # Изменили с 7 на 8
        "Пример: КАМАЗ 65115 или JCB 3CX",
        reply_markup=cancel_keyboard()
    )
    await callback.answer()

@router.message(EquipmentRegistrationStates.enter_subtype)
async def process_custom_subtype(message: Message, state: FSMContext):
    """Обработка ввода своего подтипа"""
    if message.text == "❌ Отмена":
        await cancel_equipment_add(message, state)
        return
    
    await state.update_data(subtype=message.text)
    await state.set_state(EquipmentRegistrationStates.enter_brand_model)
    
    await message.answer(
        f"✅ Подтип: {message.text}\n\n"
        "🔄 Шаг 3 из 8: ВВЕДИТЕ МАРКУ И МОДЕЛЬ\n\n"  # Изменили с 7 на 8
        "Пример: КАМАЗ 65115 или JCB 3CX",
        reply_markup=cancel_keyboard()
    )

# ШАГ 3: Ввод марки и модели
@router.message(EquipmentRegistrationStates.enter_brand_model)
async def process_brand_model(message: Message, state: FSMContext):
    """Обработка марки и модели"""
    if message.text == "❌ Отмена":
        await cancel_equipment_add(message, state)
        return
    
    if len(message.text) < 2:
        await message.answer("❌ Название слишком короткое. Введите минимум 2 символа.")
        return
    
    await state.update_data(brand_model=message.text)
    await state.set_state(EquipmentRegistrationStates.enter_year)
    
    await message.answer(
        f"✅ Марка/модель: {message.text}\n\n"
        "🔄 Шаг 4 из 8: ВВЕДИТЕ ГОД ВЫПУСКА\n\n"  # Изменили с 7 на 8
        "Пример: 2020",
        reply_markup=cancel_keyboard()
    )

# ШАГ 4: Ввод года выпуска
@router.message(EquipmentRegistrationStates.enter_year)
async def process_year(message: Message, state: FSMContext):
    """Обработка года выпуска"""
    if message.text == "❌ Отмена":
        await cancel_equipment_add(message, state)
        return
    
    try:
        year = int(message.text)
        current_year = 2024  # Можно сделать динамическим
        if year < 1900 or year > current_year:
            await message.answer(f"❌ Год должен быть между 1900 и {current_year}")
            return
    except ValueError:
        await message.answer("❌ Введите корректный год (число)")
        return
    
    await state.update_data(year=year)
    await state.set_state(EquipmentRegistrationStates.enter_capacity)
    
    await message.answer(
        f"✅ Год выпуска: {year}\n\n"
        "🔄 Шаг 5 из 8: ВВЕДИТЕ ГРУЗОПОДЪЕМНОСТЬ\n\n"  # Изменили с 7 на 8
        "В килограммах (кг). Пример: 5000",
        reply_markup=skip_keyboard()
    )

# ШАГ 5: Ввод грузоподъемности
@router.message(EquipmentRegistrationStates.enter_capacity)
async def process_capacity(message: Message, state: FSMContext):
    """Обработка грузоподъемности"""
    if message.text == "❌ Отмена":
        await cancel_equipment_add(message, state)
        return
    
    if message.text == "⏭️ Пропустить":
        capacity = None
    else:
        try:
            capacity = int(message.text)
            if capacity <= 0:
                await message.answer("❌ Грузоподъемность должна быть положительным числом")
                return
        except ValueError:
            await message.answer("❌ Введите число (в кг)")
            return
    
    await state.update_data(capacity_kg=capacity)
    await state.set_state(EquipmentRegistrationStates.enter_daily_rate)
    
    await message.answer(
        f"✅ Грузоподъемность: {capacity if capacity else 'не указана'} кг\n\n"
        "🔄 Шаг 6 из 8: ВВЕДИТЕ СТАВКУ ЗА ДЕНЬ\n\n"  # Изменили с 7 на 8
        "Стоимость аренды за сутки в рублях. Пример: 5000",
        reply_markup=cancel_keyboard()
    )

# ШАГ 6: Ввод ставки за день
@router.message(EquipmentRegistrationStates.enter_daily_rate)
async def process_daily_rate(message: Message, state: FSMContext):
    """Обработка ставки за день"""
    if message.text == "❌ Отмена":
        await cancel_equipment_add(message, state)
        return
    
    try:
        daily_rate = int(message.text)
        if daily_rate <= 0:
            await message.answer("❌ Ставка должна быть положительным числом")
            return
    except ValueError:
        await message.answer("❌ Введите число (в рублях)")
        return
    
    await state.update_data(daily_rate=daily_rate)
    await state.set_state(EquipmentRegistrationStates.enter_hourly_rate)
    
    # Расчет примерной почасовой ставки (8-часовой рабочий день)
    suggested_hourly = int(daily_rate / 8)
    
    await message.answer(
        f"✅ Ставка за день: {daily_rate} ₽\n\n"
        "🔄 Шаг 7 из 8: ВВЕДИТЕ СТАВКУ ЗА ЧАС\n\n"  # Новый шаг!
        f"Примерная ставка (исходя из 8-часового дня): {suggested_hourly} ₽/час\n"
        "Введите почасовую ставку в рублях. Пример: 1000",
        reply_markup=cancel_keyboard()
    )

# ШАГ 7: Ввод ставки за час
@router.message(EquipmentRegistrationStates.enter_hourly_rate)
async def process_hourly_rate(message: Message, state: FSMContext):
    """Обработка почасовой ставки"""
    if message.text == "❌ Отмена":
        await cancel_equipment_add(message, state)
        return
    
    try:
        hourly_rate = int(message.text)
        if hourly_rate <= 0:
            await message.answer("❌ Ставка должна быть положительным числом")
            return
    except ValueError:
        await message.answer("❌ Введите число (в рублях)")
        return
    
    # Получаем дневную ставку из состояния для проверки логики
    data = await state.get_data()
    daily_rate = data.get('daily_rate', 0)
    
    # Проверка 1: часовая ставка не может быть больше дневной
    if hourly_rate > daily_rate:
        await message.answer(
            f"❌ Почасовая ставка ({hourly_rate} ₽) не может быть больше дневной ({daily_rate} ₽).\n"
            f"Обычно часовая ставка составляет 1/8 от дневной (~{int(daily_rate/8)} ₽).\n"
            "Пожалуйста, введите корректную сумму:"
        )
        return
    
    # Проверка 2: часовая ставка не может быть слишком маленькой
    min_hourly = int(daily_rate / 24)  # Минимум, если бы работали 24 часа
    if hourly_rate < min_hourly:
        await message.answer(
            f"❌ Почасовая ставка ({hourly_rate} ₽) слишком низкая.\n"
            f"Минимальная разумная ставка: {min_hourly} ₽ (исходя из 24 часов работы).\n"
            "Введите корректную сумму:"
        )
        return
    
    # Проверка 3: рекомендуемый диапазон
    recommended_min = int(daily_rate / 10)  # 10 часов работы в день
    recommended_max = int(daily_rate / 6)   # 6 часов работы в день
    
    await state.update_data(hourly_rate=hourly_rate)
    await state.set_state(EquipmentRegistrationStates.enter_features)
    
    # Даем подсказку, если ставка вне рекомендуемого диапазона
    hint = ""
    if hourly_rate < recommended_min:
        hint = f"\n💡 Совет: Обычно почасовая ставка выше ({recommended_min}-{recommended_max} ₽)"
    elif hourly_rate > recommended_max:
        hint = f"\n💡 Совет: Обычно почасовая ставка ниже ({recommended_min}-{recommended_max} ₽)"
    
    await message.answer(
        f"✅ Ставки установлены:\n"
        f"• За день: {daily_rate} ₽\n"
        f"• За час: {hourly_rate} ₽{hint}\n\n"
        "🔄 Шаг 8 из 8: ВЫБЕРИТЕ ОСОБЕННОСТИ\n\n"  # Изменили с 7 на 8
        "Выберите доступные опции (можно несколько):",
        reply_markup=equipment_features_keyboard()
    )

# ШАГ 8: Выбор особенностей
@router.callback_query(F.data.startswith("eq_feature_"), EquipmentRegistrationStates.enter_features)
async def select_feature(callback: CallbackQuery, state: FSMContext):
    """Выбор особенности техники"""
    feature_code = callback.data.replace("eq_feature_", "")
    
    # Получаем текущие особенности
    data = await state.get_data()
    features = data.get('features', {})
    
    # Переключаем состояние особенности
    if feature_code in features:
        del features[feature_code]
    else:
        features[feature_code] = True
    
    # Обновляем состояние
    await state.update_data(features=features)
    
    # Получаем названия особенностей
    feature_names = {
        'ac': 'Кондиционер',
        'hydraulic': 'Гидроборт',
        'loader': 'Погрузчик',
        'refrigerator': 'Рефрижератор',
        'tent': 'Тент',
        'manipulator': 'Манипулятор',
        'alarm': 'Сигнализация',
        'navigation': 'Навигация'
    }
    
    # Формируем список выбранных особенностей
    selected_features = [feature_names.get(code, code) for code in features.keys()]
    
    # Обновляем сообщение
    text = "✅ Выбранные особенности:\n"
    if selected_features:
        text += "\n".join([f"• {feat}" for feat in selected_features])
    else:
        text += "Пока не выбрано"
    
    text += "\n\nНажмите '✅ Завершить выбор' когда закончите."
    
    await callback.message.edit_text(text)
    await callback.message.edit_reply_markup(reply_markup=equipment_features_keyboard())
    await callback.answer()

@router.callback_query(F.data == "eq_features_done", EquipmentRegistrationStates.enter_features)
async def finish_features(callback: CallbackQuery, state: FSMContext):
    """Завершение выбора особенностей"""
    data = await state.get_data()
    
    # Формируем сводку
    summary = "📋 СВОДКА ПО ТЕХНИКЕ:\n\n"
    
    type_names = {
        'truck': 'грузовик',
        'gazelle': 'газель',
        'truck_large': 'фура',
        'refrigerator': 'рефрижератор',
        'excavator': 'экскаватор',
        'crane': 'кран',
        'loader': 'погрузчик',
        'bulldozer': 'бульдозер',
        'dump_truck': 'самосвал',
        'tractor': 'трактор'
    }
    
    summary += f"Тип: {type_names.get(data['equipment_type'], data['equipment_type'])}\n"
    summary += f"Подтип: {data.get('subtype', 'не указан')}\n"
    summary += f"Марка/модель: {data.get('brand_model', 'не указана')}\n"
    summary += f"Год выпуска: {data.get('year', 'не указан')}\n"
    summary += f"Грузоподъемность: {data.get('capacity_kg', 'не указана')} кг\n"
    summary += f"Ставка за день: {data.get('daily_rate', 'не указана')} ₽\n"
    summary += f"Ставка за час: {data.get('hourly_rate', 'не указана')} ₽\n"  # Добавили почасовую ставку
    
    features = data.get('features', {})
    if features:
        feature_names = {
            'ac': 'Кондиционер',
            'hydraulic': 'Гидроборт',
            'loader': 'Погрузчик',
            'refrigerator': 'Рефрижератор',
            'tent': 'Тент',
            'manipulator': 'Манипулятор',
            'alarm': 'Сигнализация',
            'navigation': 'Навигация'
        }
        summary += "Особенности:\n"
        for code in features.keys():
            summary += f"• {feature_names.get(code, code)}\n"
    
    summary += "\n✅ Всё верно?"
    
    await state.set_state(EquipmentRegistrationStates.confirm_equipment)
    await callback.message.answer(summary, reply_markup=confirm_equipment_keyboard())
    await callback.answer()

# ПОДТВЕРЖДЕНИЕ СОХРАНЕНИЯ
@router.callback_query(F.data == "eq_confirm_save", EquipmentRegistrationStates.confirm_equipment)
async def confirm_save_equipment(callback: CallbackQuery, state: FSMContext):
    """Подтверждение и сохранение техники"""
    data = await state.get_data()
    
    # Подготавливаем данные для сохранения
    equipment_data = {
        'equipment_type': data.get('equipment_type'),
        'subtype': data.get('subtype'),
        'brand_model': data.get('brand_model'),
        'year': data.get('year'),
        'capacity_kg': data.get('capacity_kg'),
        'daily_rate': data.get('daily_rate'),
        'hourly_rate': data.get('hourly_rate'),  # Сохраняем почасовую ставку из ввода
        'features': data.get('features', {})
    }
    
    # Разделяем brand и model если есть пробел
    brand_model = data.get('brand_model', '').split(' ', 1)
    if len(brand_model) >= 2:
        equipment_data['brand'] = brand_model[0]
        equipment_data['model'] = brand_model[1]
    else:
        equipment_data['brand'] = brand_model[0] if brand_model else ''
        equipment_data['model'] = ''
    
    # Сохраняем в БД
    success = db.add_equipment(data['executor_id'], equipment_data)
    
    if success:
        await callback.message.answer(
            "✅ Техника успешно добавлена!\n\n"
            f"Тип: {data.get('equipment_type')}\n"
            f"Модель: {data.get('brand_model')}\n"
            f"Ставки:\n"
            f"• Дневная: {data.get('daily_rate')} ₽\n"
            f"• Почасовая: {data.get('hourly_rate')} ₽",
            reply_markup=back_to_profile_keyboard()
        )
    else:
        await callback.message.answer(
            "❌ Ошибка при сохранении техники. Попробуйте еще раз.",
            reply_markup=back_to_profile_keyboard()
        )
    
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "eq_edit_again", EquipmentRegistrationStates.confirm_equipment)
async def edit_equipment_again(callback: CallbackQuery, state: FSMContext):
    """Вернуться к редактированию техники"""
    await state.set_state(EquipmentRegistrationStates.select_equipment_type)
    await callback.message.answer(
        "🔄 Начнем заново. Выберите тип техники:",
        reply_markup=equipment_types_keyboard()
    )
    await callback.answer()

# ========== ОТМЕНА ДОБАВЛЕНИЯ ТЕХНИКИ ==========

async def cancel_equipment_add(message: Message, state: FSMContext):
    """Отмена добавления техники"""
    await state.clear()
    user_info = db.get_user(message.from_user.id)
    role = user_info.get('role', 'customer') if user_info else 'customer'
    
    await message.answer(
        "❌ Добавление техники отменено.",
        reply_markup=main_menu(role)
    )

# ========== УПРАВЛЕНИЕ СУЩЕСТВУЮЩЕЙ ТЕХНИКОЙ ==========

@router.callback_query(F.data == "eq_manage_list")
async def manage_equipment_list(callback: CallbackQuery):
    """Показать список техники для управления"""
    user_id = callback.from_user.id
    equipment = db.get_executor_equipment(user_id)
    
    if not equipment:
        await callback.message.answer("🚛 У вас нет техники для управления.")
        await callback.answer()
        return
    
    builder = InlineKeyboardBuilder()
    
    for item in equipment[:10]:  # Ограничиваем 10 элементами
        status = "🟢" if item['is_available'] else "🔴"
        btn_text = f"{status} {item['brand']} {item['model']}"
        
        builder.add(InlineKeyboardButton(
            text=btn_text[:30],  # Обрезаем слишком длинный текст
            callback_data=f"eq_view_{item['id']}"
        ))
    
    builder.adjust(1)
    
    await callback.message.answer(
        "🚛 ВЫБЕРИТЕ ТЕХНИКУ ДЛЯ УПРАВЛЕНИЯ:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("eq_view_"))
async def view_equipment_details(callback: CallbackQuery):
    """Просмотр деталей техники"""
    equipment_id = int(callback.data.replace("eq_view_", ""))
    equipment = db.get_equipment(equipment_id)
    
    if not equipment:
        await callback.answer("❌ Техника не найдена", show_alert=True)
        return
    
    # Формируем информацию
    status = "🟢 Доступна" if equipment['is_available'] else "🔴 Недоступна"
    
    text = f"""🚛 ДЕТАЛИ ТЕХНИКИ #{equipment_id}

Тип: {equipment['equipment_type']}
Подтип: {equipment['subtype'] or 'не указан'}
Марка: {equipment['brand'] or 'не указана'}
Модель: {equipment['model'] or 'не указана'}
Год выпуска: {equipment['year'] or 'не указан'}
Грузоподъемность: {equipment['capacity_kg'] or 'не указана'} кг

💰 СТАВКИ:
• За день: {equipment['daily_rate'] or 'не указана'} ₽
• За час: {equipment['hourly_rate'] or 'не указана'} ₽

Статус: {status}

📅 Добавлено: {equipment['created_at'][:10]}"""
    
    # Особенности
    if equipment['features']:
        try:
            features = json.loads(equipment['features'])
            if features:
                text += "\n\nОсобенности:\n"
                feature_names = {
                    'ac': '• Кондиционер',
                    'hydraulic': '• Гидроборт',
                    'loader': '• Погрузчик',
                    'refrigerator': '• Рефрижератор',
                    'tent': '• Тент',
                    'manipulator': '• Манипулятор',
                    'alarm': '• Сигнализация',
                    'navigation': '• Навигация'
                }
                for code, value in features.items():
                    if value:
                        text += f"{feature_names.get(code, f'• {code}')}\n"
        except:
            pass
    
    await callback.message.answer(
        text,
        reply_markup=equipment_management_keyboard(
            equipment_id, 
            equipment['is_available']
        )
    )
    await callback.answer()

# ========== УДАЛЕНИЕ ТЕХНИКИ ==========

@router.callback_query(F.data.startswith("eq_delete_"))
async def delete_equipment_start(callback: CallbackQuery):
    """Начало удаления техники"""
    equipment_id = int(callback.data.replace("eq_delete_", ""))
    equipment = db.get_equipment(equipment_id)
    
    if not equipment:
        await callback.answer("❌ Техника не найдена", show_alert=True)
        return
    
    # Создаем клавиатуру подтверждения
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="✅ Да, удалить",
        callback_data=f"confirm_delete_{equipment_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="❌ Нет, отмена",
        callback_data=f"eq_view_{equipment_id}"
    ))
    
    await callback.message.answer(
        f"⚠️ ВЫ УВЕРЕНЫ, ЧТО ХОТИТЕ УДАЛИТЬ?\n\n"
        f"Техника: {equipment['brand']} {equipment['model']}\n"
        f"Тип: {equipment['equipment_type']}\n\n"
        f"Это действие нельзя отменить!",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("confirm_delete_"))
async def confirm_delete_equipment(callback: CallbackQuery):
    """Подтверждение удаления техники"""
    equipment_id = int(callback.data.replace("confirm_delete_", ""))
    equipment = db.get_equipment(equipment_id)
    
    if not equipment:
        await callback.answer("❌ Техника не найдена", show_alert=True)
        return
    
    # Удаляем из БД
    success = db.delete_equipment(equipment_id)
    
    if success:
        await callback.message.answer(
            f"✅ Техника удалена:\n"
            f"{equipment['brand']} {equipment['model']}",
            reply_markup=back_to_profile_keyboard()
        )
    else:
        await callback.message.answer(
            "❌ Ошибка при удалении техники",
            reply_markup=back_to_profile_keyboard()
        )
    
    await callback.answer()

# ========== ИЗМЕНЕНИЕ ДОСТУПНОСТИ ==========

@router.callback_query(F.data.startswith("eq_disable_"))
async def disable_equipment(callback: CallbackQuery):
    """Сделать технику недоступной"""
    equipment_id = int(callback.data.replace("eq_disable_", ""))
    
    success = db.toggle_equipment_availability(equipment_id, False)
    
    if success:
        await callback.answer("🔴 Техника теперь недоступна", show_alert=True)
        # Обновляем сообщение
        await view_equipment_details(callback)
    else:
        await callback.answer("❌ Ошибка", show_alert=True)

@router.callback_query(F.data.startswith("eq_enable_"))
async def enable_equipment(callback: CallbackQuery):
    """Сделать технику доступной"""
    equipment_id = int(callback.data.replace("eq_enable_", ""))
    
    success = db.toggle_equipment_availability(equipment_id, True)
    
    if success:
        await callback.answer("🟢 Техника теперь доступна", show_alert=True)
        # Обновляем сообщение
        await view_equipment_details(callback)
    else:
        await callback.answer("❌ Ошибка", show_alert=True)

# ========== РЕДАКТИРОВАНИЕ ТЕХНИКИ ==========

@router.callback_query(F.data.startswith("eq_edit_"))
async def edit_equipment_start(callback: CallbackQuery):
    """Начало редактирования техники"""
    equipment_id = int(callback.data.replace("eq_edit_", ""))
    
    # Пока временное сообщение
    await callback.message.answer(
        "✏️ Редактирование техники (в разработке)\n\n"
        "Скоро вы сможете:\n"
        "• Изменить характеристики\n"
        "• Обновить ставки\n"
        "• Добавить фото\n\n"
        "А пока используйте удаление и создание заново.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🚛 Управление техникой", callback_data="eq_manage_list"),
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"eq_view_{equipment_id}")
        ]])
    )
    await callback.answer()

# ========== ОБРАБОТКА ВОЗВРАТОВ ==========

@router.callback_query(F.data == "back_to_equipment_menu")
async def back_to_equipment_menu(callback: CallbackQuery):
    """Вернуться к меню техники"""
    user_id = callback.from_user.id
    equipment = db.get_executor_equipment(user_id)
    
    if not equipment:
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="✅ Добавить", callback_data="eq_add_first"))
        builder.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_profile"))
        
        await callback.message.answer(
            "🚛 У вас пока нет техники.",
            reply_markup=builder.as_markup()
        )
    else:
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="➕ Добавить", callback_data="eq_add_new"))
        builder.add(InlineKeyboardButton(text="📋 Управлять", callback_data="eq_manage_list"))
        builder.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_profile"))
        builder.adjust(2, 1)
        
        await callback.message.answer(
            "🚛 УПРАВЛЕНИЕ ТЕХНИКОЙ",
            reply_markup=builder.as_markup()
        )
    
    await callback.answer()