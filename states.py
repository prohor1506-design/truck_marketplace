from aiogram.fsm.state import State, StatesGroup

# ========== СУЩЕСТВУЮЩИЕ СОСТОЯНИЯ ==========

class OrderStates(StatesGroup):
    """Состояния для создания заказа"""
    select_service = State()
    enter_description = State()
    enter_address = State()
    enter_price = State()

class OfferStates(StatesGroup):
    """Состояния для предложения цены"""
    enter_price = State()
    enter_comment = State()

class ProfileStates(StatesGroup):
    """Состояния для профиля"""
    edit_name = State()
    edit_phone = State()

class ReviewStates(StatesGroup):
    """Состояния для отзыва"""
    enter_rating = State()
    enter_comment = State()

# ========== НОВЫЕ СОСТОЯНИЯ ==========

class ExecutorRegistrationStates(StatesGroup):
    """
    Состояния для регистрации исполнителя
    (многошаговая форма заполнения профиля)
    """
    # Шаг 1: Основная информация
    enter_company_name = State()
    enter_phone = State()
    enter_description = State()
    enter_experience = State()
    
    # Шаг 2: Юридическая информация (не обязательно)
    enter_license = State()
    enter_insurance = State()
    
    # Шаг 3: Геолокация
    enter_location = State()          # Текстовый адрес
    enter_work_radius = State()       # Радиус работы (км)
    
    # Шаг 4: Ценовая политика
    enter_min_price = State()         # Минимальная цена заказа
    enter_max_price = State()         # Максимальная цена заказа
    
    # Шаг 5: Выбор категорий услуг (специализация)
    select_categories = State()


class EquipmentRegistrationStates(StatesGroup):
    """
    Состояния для добавления техники
    (исполнитель может добавить несколько единиц техники)
    """
    # Основная информация о технике
    select_equipment_type = State()   # Выбор типа (грузовик, экскаватор и т.д.)
    enter_subtype = State()           # Подтип (Газель, КАМАЗ и т.д.)
    enter_brand_model = State()       # Марка и модель
    enter_year = State()              # Год выпуска
    
    # Характеристики
    enter_capacity = State()          # Грузоподъемность (кг)
    enter_volume = State()            # Объем (м³)
    enter_dimensions = State()        # Габариты (ДхШхВ)
    
    # Цены
    enter_daily_rate = State()        # Ставка за день
    enter_hourly_rate = State()       # Ставка за час
    
    # Дополнительно
    enter_features = State()          # Особенности (кондиционер, гидроборт и т.д.)
    
    # Подтверждение
    confirm_equipment = State()


class LocationStates(StatesGroup):
    """
    Состояния для работы с геолокацией
    (для заказчиков и исполнителей)
    """
    # Для заказчика при создании заказа
    waiting_for_location = State()    # Ожидание отправки геолокации
    confirm_location = State()        # Подтверждение адреса
    
    # Для исполнителя
    set_work_radius = State()         # Установка радиуса работы
    update_location = State()         # Обновление местоположения


class OrderFilterStates(StatesGroup):
    """
    Состояния для фильтрации заказов
    (исполнитель может настраивать фильтры)
    """
    select_service_filter = State()   # Фильтр по типу услуги
    set_price_range = State()         # Фильтр по цене (мин-макс)
    set_distance_filter = State()     # Фильтр по расстоянию
    set_sorting = State()             # Сортировка (по цене, дате, расстоянию)


class ProfileEditStates(StatesGroup):
    """
    Состояния для редактирования профиля исполнителя
    """
    edit_company_info = State()       # Изменение информации о компании
    edit_contact_info = State()       # Изменение контактов
    edit_pricing = State()            # Изменение ценовой политики
    edit_schedule = State()           # Изменение расписания
    edit_company_name = State()
    edit_phone = State()
    edit_description = State()
    edit_experience = State()
    edit_pricing = State()


class EquipmentManagementStates(StatesGroup):
    """
    Состояния для управления техникой
    """
    # Просмотр и выбор техники
    viewing_equipment = State()       # Просмотр списка техники
    select_equipment_action = State() # Выбор действия (редактировать/удалить)
    
    # Редактирование
    edit_equipment_field = State()    # Редактирование конкретного поля
    
    # Добавление новой техники (использует EquipmentRegistrationStates)
    # Удаление
    confirm_delete_equipment = State()


# Для удобства создадим словарь с русскими названиями состояний
STATE_DESCRIPTIONS = {
    # Старые состояния
    'OrderStates:select_service': 'Выбор услуги',
    'OrderStates:enter_description': 'Ввод описания заказа',
    'OrderStates:enter_address': 'Ввод адреса',
    'OrderStates:enter_price': 'Ввод цены',
    
    # Новые состояния
    'ExecutorRegistrationStates:enter_company_name': 'Ввод названия компании',
    'ExecutorRegistrationStates:enter_phone': 'Ввод телефона',
    'ExecutorRegistrationStates:enter_description': 'Ввод описания услуг',
    'ExecutorRegistrationStates:enter_experience': 'Ввод опыта работы',
    'ExecutorRegistrationStates:enter_location': 'Ввод местоположения',
    'ExecutorRegistrationStates:enter_work_radius': 'Ввод радиуса работы',
    'ExecutorRegistrationStates:enter_min_price': 'Ввод минимальной цены',
    'ExecutorRegistrationStates:enter_max_price': 'Ввод максимальной цены',
    
    'EquipmentRegistrationStates:select_equipment_type': 'Выбор типа техники',
    'EquipmentRegistrationStates:enter_brand_model': 'Ввод марки и модели',
    
    'LocationStates:waiting_for_location': 'Ожидание геолокации',
    'OrderFilterStates:select_service_filter': 'Выбор фильтра по услуге',
}
# ========== СОСТОЯНИЯ ДЛЯ РЕДАКТИРОВАНИЯ ПРОФИЛЯ ==========

class ProfileEditSimpleStates(StatesGroup):
    """Упрощенные состояния для редактирования профиля"""
    edit_company = State()     # Редактирование названия компании
    edit_phone = State()       # Редактирование телефона
    edit_description = State() # Редактирование описания
    edit_experience = State()  # Редактирование опыта
    edit_pricing = State()     # Редактирование цены


def get_state_description(state: str) -> str:
    """Получить человеко-читаемое описание состояния"""
    return STATE_DESCRIPTIONS.get(state, 'Неизвестное состояние')