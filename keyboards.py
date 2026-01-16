from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, 
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from config import SERVICES

# ========== REPLY КЛАВИАТУРЫ ==========

def main_menu(role='customer'):
    """Главное меню в зависимости от роли"""
    builder = ReplyKeyboardBuilder()
    
    if role == 'customer':
        builder.add(KeyboardButton(text="📦 Создать заказ"))
        builder.add(KeyboardButton(text="📋 Мои заказы"))
        builder.add(KeyboardButton(text="👷 Стать исполнителем"))
        builder.add(KeyboardButton(text="👤 Профиль"))
        builder.add(KeyboardButton(text="ℹ️ Помощь"))
        builder.adjust(2, 2, 1)
        
    else:  # executor
        builder.add(KeyboardButton(text="📋 Доступные заказы"))
        builder.add(KeyboardButton(text="⚙️ Мой профиль"))
        builder.add(KeyboardButton(text="🚛 Моя техника"))
        builder.add(KeyboardButton(text="💼 Мои предложения"))
        builder.add(KeyboardButton(text="🔍 Настройки фильтров"))
        builder.add(KeyboardButton(text="📦 Вернуться в заказчики"))
        builder.add(KeyboardButton(text="ℹ️ Помощь"))
        builder.adjust(2, 2, 2, 1)
    
    return builder.as_markup(resize_keyboard=True)


def cancel_keyboard():
    """Клавиатура с кнопкой отмены"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="❌ Отмена"))
    return builder.as_markup(resize_keyboard=True)


def skip_keyboard():
    """Клавиатура с кнопкой пропуска (для необязательных полей)"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="⏭️ Пропустить"))
    builder.add(KeyboardButton(text="❌ Отмена"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def yes_no_keyboard():
    """Клавиатура с Да/Нет"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="✅ Да"))
    builder.add(KeyboardButton(text="❌ Нет"))
    builder.add(KeyboardButton(text="❌ Отмена"))
    builder.adjust(2, 1)
    return builder.as_markup(resize_keyboard=True)


def location_keyboard():
    """Клавиатура для отправки геолокации"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="📍 Отправить местоположение", request_location=True))
    builder.add(KeyboardButton(text="📝 Ввести вручную"))
    builder.add(KeyboardButton(text="❌ Отмена"))
    builder.adjust(1, 1, 1)
    return builder.as_markup(resize_keyboard=True)


def executor_registration_steps(step):
    """Клавиатуры для каждого шага регистрации исполнителя"""
    builder = ReplyKeyboardBuilder()
    
    if step == "location":
        builder.add(KeyboardButton(text="📍 Отправить местоположение", request_location=True))
        builder.add(KeyboardButton(text="📝 Ввести адрес текстом"))
        builder.add(KeyboardButton(text="⏭️ Пропустить"))
        builder.add(KeyboardButton(text="❌ Отмена"))
        builder.adjust(1, 2, 1)
    
    elif step == "radius":
        for radius in [5, 10, 20, 50, 100]:
            builder.add(KeyboardButton(text=f"{radius} км"))
        builder.add(KeyboardButton(text="📝 Свой вариант"))
        builder.add(KeyboardButton(text="⏭️ Пропустить"))
        builder.add(KeyboardButton(text="❌ Отмена"))
        builder.adjust(3, 2, 1, 1)
    
    elif step == "experience":
        for years in ["Меньше года", "1-3 года", "3-5 лет", "5-10 лет", "Более 10 лет"]:
            builder.add(KeyboardButton(text=years))
        builder.add(KeyboardButton(text="❌ Отмена"))
        builder.adjust(2, 2, 1)
    
    else:
        builder.add(KeyboardButton(text="❌ Отмена"))
    
    return builder.as_markup(resize_keyboard=True)


# ========== INLINE КЛАВИАТУРЫ ==========

def services_keyboard():
    """Выбор услуги (для заказчиков)"""
    builder = InlineKeyboardBuilder()
    
    for key, value in SERVICES.items():
        builder.add(InlineKeyboardButton(text=value, callback_data=f"service_{key}"))
    
    builder.adjust(2)
    return builder.as_markup()


def executor_categories_keyboard(categories, selected_ids=None):
    """Выбор категорий услуг для исполнителя"""
    builder = InlineKeyboardBuilder()
    
    if not selected_ids:
        selected_ids = []
    
    for category in categories:
        prefix = "✅ " if category['id'] in selected_ids else ""
        text = f"{prefix}{category['name']}"
        
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=f"cat_{category['id']}"
        ))
    
    builder.adjust(2)
    
    builder.row(
        InlineKeyboardButton(text="✅ Завершить выбор", callback_data="cats_done"),
        InlineKeyboardButton(text="🔄 Сбросить все", callback_data="cats_reset")
    )
    
    return builder.as_markup()


def equipment_types_keyboard():
    """Выбор типа техники"""
    builder = InlineKeyboardBuilder()
    
    equipment_types = [
        ("🚚 Грузовик", "truck"),
        ("📦 Газель", "gazelle"),
        ("🚛 Фура", "truck_large"),
        ("🧊 Рефрижератор", "refrigerator"),
        ("🔨 Экскаватор", "excavator"),
        ("🏗️ Кран", "crane"),
        ("🏗️ Погрузчик", "loader"),
        ("🚜 Бульдозер", "bulldozer"),
    ]
    
    for name, code in equipment_types:
        builder.add(InlineKeyboardButton(text=name, callback_data=f"eq_type_{code}"))
    
    builder.adjust(2)
    return builder.as_markup()


def executor_profile_keyboard(user_id, has_profile=False):
    """Клавиатура профиля исполнителя"""
    builder = InlineKeyboardBuilder()
    
    if not has_profile:
        builder.add(InlineKeyboardButton(
            text="📝 Заполнить профиль", 
            callback_data=f"executor_register_{user_id}"
        ))
    else:
        builder.add(InlineKeyboardButton(
            text="👁️ Просмотреть профиль", 
            callback_data=f"executor_view_{user_id}"
        ))
        builder.add(InlineKeyboardButton(
            text="✏️ Редактировать профиль", 
            callback_data="executor_edit_menu"
        ))
        builder.add(InlineKeyboardButton(
            text="🚛 Управление техникой", 
            callback_data="equipment_menu"
        ))
    
    builder.add(InlineKeyboardButton(
        text="⬅️ В главное меню", 
        callback_data="main_menu"
    ))
    
    builder.adjust(1)
    return builder.as_markup()


def equipment_management_keyboard(equipment_id, is_available=True):
    """Клавиатура для управления конкретной единицей техники"""
    builder = InlineKeyboardBuilder()
    
    availability_text = "🔴 Сделать недоступной" if is_available else "🟢 Сделать доступной"
    availability_callback = f"eq_disable_{equipment_id}" if is_available else f"eq_enable_{equipment_id}"
    
    builder.add(InlineKeyboardButton(
        text="✏️ Редактировать", 
        callback_data=f"eq_edit_{equipment_id}"
    ))
    builder.add(InlineKeyboardButton(
        text=availability_text, 
        callback_data=availability_callback
    ))
    builder.add(InlineKeyboardButton(
        text="❌ Удалить", 
        callback_data=f"eq_delete_{equipment_id}"
    ))
    
    builder.adjust(1)
    builder.row(InlineKeyboardButton(
        text="⬅️ Назад", 
        callback_data="back_to_equipment_menu"
    ))
    
    return builder.as_markup()


def order_filters_keyboard(current_filters=None):
    """Клавиатура для настройки фильтров заказов - УПРОЩЕННАЯ (без расстояния)"""
    if not current_filters:
        current_filters = {}
    
    builder = InlineKeyboardBuilder()
    
    service_filter = current_filters.get('service_type', 'Все')
    builder.add(InlineKeyboardButton(
        text=f"📦 Услуга: {service_filter}", 
        callback_data="filter_service"
    ))
    
    price_filter = current_filters.get('price', 'Любая')
    builder.add(InlineKeyboardButton(
        text=f"💰 Цена: {price_filter}", 
        callback_data="filter_price"
    ))
    
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text="✅ Применить", callback_data="filters_apply"),
        InlineKeyboardButton(text="🔄 Сбросить", callback_data="filters_reset")
    )
    
    builder.row(InlineKeyboardButton(
        text="⬅️ Назад к профилю", 
        callback_data="back_to_profile"
    ))
    
    return builder.as_markup()


def price_suggestions_keyboard(order_id, current_price=None):
    """Предложения цен"""
    builder = InlineKeyboardBuilder()
    
    if current_price:
        base_prices = [
            int(current_price * 0.8),
            int(current_price * 0.9),
            current_price,
            int(current_price * 1.1),
            int(current_price * 1.2)
        ]
    else:
        base_prices = [500, 1000, 1500, 2000, 3000, 5000, 10000]
    
    unique_prices = sorted(set([p for p in base_prices if p > 0]))
    
    for price in unique_prices[:6]:
        builder.add(InlineKeyboardButton(text=f"{price} ₽", callback_data=f"price_{order_id}_{price}"))
    
    builder.adjust(2)
    builder.row(InlineKeyboardButton(
        text="💵 Ввести свою цену", 
        callback_data=f"custom_{order_id}"
    ))
    
    return builder.as_markup()


def order_actions_keyboard(order_id, user_id, is_owner=False):
    """Действия с заказом"""
    builder = InlineKeyboardBuilder()
    
    if is_owner:
        builder.add(InlineKeyboardButton(
            text="📊 Посмотреть предложения", 
            callback_data=f"offers_{order_id}"
        ))
        builder.add(InlineKeyboardButton(
            text="✏️ Редактировать", 
            callback_data=f"edit_{order_id}"
        ))
        builder.add(InlineKeyboardButton(
            text="❌ Закрыть заказ", 
            callback_data=f"close_{order_id}"
        ))
    else:
        builder.add(InlineKeyboardButton(
            text="💰 Предложить цену", 
            callback_data=f"offer_{order_id}"
        ))
    
    builder.adjust(1)
    return builder.as_markup()


def offers_list_keyboard(order_id, offers):
    """Список предложений по заказу"""
    builder = InlineKeyboardBuilder()
    
    for offer in offers[:5]:
        executor_name = offer.get('username', f"Исполнитель {offer['executor_id']}")
        text = f"{executor_name}: {offer['price']} ₽"
        
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=f"select_offer_{offer['id']}"
        ))
    
    builder.adjust(1)
    return builder.as_markup()


def order_list_keyboard(orders, current_index=0):
    """Список заказов с навигацией"""
    builder = InlineKeyboardBuilder()
    
    if orders:
        order = orders[current_index]
        builder.add(InlineKeyboardButton(
            text=f"📦 Заказ #{order['order_id']}",
            callback_data=f"order_{order['order_id']}"
        ))
    
    if len(orders) > 1:
        nav_buttons = []
        
        if current_index > 0:
            nav_buttons.append(InlineKeyboardButton(
                text="◀️ Предыдущий", 
                callback_data=f"nav_{current_index-1}"
            ))
        
        nav_buttons.append(InlineKeyboardButton(
            text=f"{current_index+1}/{len(orders)}", 
            callback_data="page_info"
        ))
        
        if current_index < len(orders) - 1:
            nav_buttons.append(InlineKeyboardButton(
                text="Следующий ▶️", 
                callback_data=f"nav_{current_index+1}"
            ))
        
        builder.row(*nav_buttons)
    
    builder.row(InlineKeyboardButton(
        text="🔄 Обновить список", 
        callback_data="refresh_orders"
    ))
    
    return builder.as_markup()


def confirmation_keyboard(action, item_id):
    """Клавиатура подтверждения"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="✅ Да", 
        callback_data=f"confirm_{action}_{item_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="❌ Нет", 
        callback_data=f"cancel_{action}_{item_id}"
    ))
    
    builder.adjust(2)
    return builder.as_markup()


def profile_keyboard(user_id):
    """Клавиатура профиля (общая)"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="📊 Статистика", 
        callback_data=f"stats_{user_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="⭐ Мои отзывы", 
        callback_data=f"reviews_{user_id}"
    ))
    
    builder.adjust(1)
    return builder.as_markup()


def back_to_menu_keyboard():
    """Кнопка возврата в меню"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="⬅️ В главное меню", 
        callback_data="back_to_main"
    ))
    return builder.as_markup()


def back_to_profile_keyboard():
    """Кнопка возврата к профилю"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="⬅️ Назад к профилю", 
        callback_data="back_to_profile"
    ))
    return builder.as_markup()


def order_navigation_keyboard(order_index, total_orders, order_id):
    """Клавиатура для навигации по заказам"""
    builder = InlineKeyboardBuilder()
    
    # Кнопка предложения
    builder.add(InlineKeyboardButton(
        text="💰 Предложить цену",
        callback_data=f"make_offer_{order_id}"
    ))
    
    # Навигация
    if total_orders > 1:
        nav_buttons = []
        
        if order_index > 0:
            nav_buttons.append(InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=f"order_nav_{order_index-1}"
            ))
        
        nav_buttons.append(InlineKeyboardButton(
            text=f"{order_index+1}/{total_orders}",
            callback_data="order_page_info"
        ))
        
        if order_index < total_orders - 1:
            nav_buttons.append(InlineKeyboardButton(
                text="Вперед ▶️",
                callback_data=f"order_nav_{order_index+1}"
            ))
        
        builder.row(*nav_buttons)
    
    builder.row(InlineKeyboardButton(
        text="⬅️ Назад в меню",
        callback_data="back_to_main_menu"
    ))
    
    return builder.as_markup()


def equipment_subtype_keyboard(equipment_type):
    """Клавиатура для выбора подтипа техники"""
    builder = InlineKeyboardBuilder()
    
    # Подтипы для разных типов техники
    subtypes = {
        'truck': ['КАМАЗ', 'MAN', 'Volvo', 'Scania', 'DAF', 'Другой'],
        'gazelle': ['ГАЗель', 'Mercedes Sprinter', 'Ford Transit', 'Другой'],
        'truck_large': ['Фура 20т', 'Фура 40т', 'Седельный тягач', 'Другой'],
        'refrigerator': ['Рефрижератор 10м³', 'Рефрижератор 20м³', 'Изотерма', 'Другой'],
        'excavator': ['Гусеничный', 'Колесный', 'Мини-экскаватор', 'Другой'],
        'crane': ['Автокран', 'Башенный', 'Гусеничный', 'Другой'],
        'loader': ['Фронтальный', 'Вилочный', 'Мини-погрузчик', 'Другой'],
        'bulldozer': ['Гусеничный', 'Колесный', 'Мини-бульдозер', 'Другой'],
        'dump_truck': ['Самосвал 10т', 'Самосвал 20т', 'Самосвал 30т', 'Другой'],
        'tractor': ['Колесный', 'Гусеничный', 'Трактор с прицепом', 'Другой'],
    }
    
    if equipment_type in subtypes:
        for subtype in subtypes[equipment_type]:
            builder.add(InlineKeyboardButton(
                text=subtype,
                callback_data=f"eq_subtype_{subtype}"
            ))
    else:
        # Если нет подтипов, предлагаем ввести свой
        builder.add(InlineKeyboardButton(
            text="📝 Ввести свой вариант",
            callback_data="eq_subtype_custom"
        ))
    
    builder.adjust(2)
    builder.row(InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data="back_to_equipment_types"
    ))
    
    return builder.as_markup()


def confirm_equipment_keyboard(equipment_id=None):
    """Клавиатура подтверждения добавления техники"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="✅ Да, сохранить",
        callback_data="eq_confirm_save"
    ))
    builder.add(InlineKeyboardButton(
        text="✏️ Нет, исправить",
        callback_data="eq_edit_again"
    ))
    
    builder.adjust(2)
    return builder.as_markup()


def equipment_features_keyboard():
    """Клавиатура для выбора особенностей техники"""
    builder = InlineKeyboardBuilder()
    
    features = [
        ("✅ Кондиционер", "ac"),
        ("✅ Гидроборт", "hydraulic"),
        ("✅ Погрузчик", "loader"),
        ("✅ Рефрижератор", "refrigerator"),
        ("✅ Тент", "tent"),
        ("✅ Манипулятор", "manipulator"),
        ("✅ Сигнализация", "alarm"),
        ("✅ Навигация", "navigation"),
    ]
    
    for name, code in features:
        builder.add(InlineKeyboardButton(
            text=name,
            callback_data=f"eq_feature_{code}"
        ))
    
    builder.adjust(2)
    builder.row(InlineKeyboardButton(
        text="✅ Завершить выбор",
        callback_data="eq_features_done"
    ))
    
    return builder.as_markup()