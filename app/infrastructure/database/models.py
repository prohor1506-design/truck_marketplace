"""
Модели базы данных SQLAlchemy
"""

from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, Enum
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import JSON

Base = declarative_base()


class UserRole(PyEnum):
    """Роли пользователей"""
    CUSTOMER = "customer"      # Заказчик
    EXECUTOR = "executor"      # Исполнитель
    OWNER = "owner"           # Владелец техники
    ADMIN = "admin"           # Администратор


class EquipmentType(PyEnum):
    """Типы техники"""
    TRUCK = "truck"           # Грузовик
    SPECIAL = "special"       # Спецтехника
    TRAILER = "trailer"       # Прицеп
    CRANE = "crane"          # Кран
    EXCAVATOR = "excavator"  # Экскаватор


class OrderStatus(PyEnum):
    """Статусы заказов"""
    CREATED = "created"       # Создан
    SEARCHING = "searching"   # В поиске исполнителя
    IN_PROGRESS = "in_progress"  # В работе
    COMPLETED = "completed"   # Завершен
    CANCELLED = "cancelled"   # Отменен


class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.CUSTOMER)
    balance = Column(Float, default=0.0)
    rating = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    orders = relationship("Order", back_populates="customer", foreign_keys="Order.customer_id")
    equipment = relationship("Equipment", back_populates="owner")
    offers = relationship("Offer", back_populates="executor")
    
    def __repr__(self):
        return f"<User {self.telegram_id} ({self.role.value})>"
    
    def get_role_display(self):
        """Получить читаемое название роли"""
        role_display = {
            UserRole.CUSTOMER: "👤 Заказчик",
            UserRole.EXECUTOR: "🚚 Исполнитель",
            UserRole.OWNER: "🏗️ Владелец техники",
            UserRole.ADMIN: "⚡ Администратор"
        }
        return role_display.get(self.role, "Не указана")
    
    def get_full_name(self):
        """Получить полное имя пользователя"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return "Не указано"
    
    def get_profile_info(self):
        """Получить информацию для профиля"""
        return (
            f"<b>👤 Профиль пользователя</b>\n\n"
            f"<b>ID:</b> {self.id}\n"
            f"<b>Telegram ID:</b> {self.telegram_id}\n"
            f"<b>Имя:</b> {self.get_full_name()}\n"
            f"<b>Username:</b> @{self.username if self.username else 'нет'}\n"
            f"<b>Роль:</b> {self.get_role_display()}\n"
            f"<b>Телефон:</b> {self.phone if self.phone else 'не указан'}\n"
            f"<b>Email:</b> {self.email if self.email else 'не указан'}\n"
            f"<b>Баланс:</b> {self.balance} ₽\n"
            f"<b>Рейтинг:</b> {self.rating} ⭐\n"
            f"<b>Статус:</b> {'✅ Активен' if self.is_active else '❌ Неактивен'}\n"
            f"<b>Верификация:</b> {'✅ Да' if self.is_verified else '❌ Нет'}\n"
            f"<b>Дата регистрации:</b> {self.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        )


class Equipment(Base):
    """Модель техники/оборудования"""
    __tablename__ = "equipment"
    
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(200), nullable=False)
    type = Column(Enum(EquipmentType), nullable=False)
    description = Column(Text, nullable=True)
    capacity = Column(Float, nullable=True)  # Грузоподъемность в тоннах
    price_per_hour = Column(Float, nullable=True)
    price_per_day = Column(Float, nullable=True)
    location = Column(String(200), nullable=True)
    is_available = Column(Boolean, default=True)
    photos = Column(JSON, nullable=True)  # Список photo_id из Telegram
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    owner = relationship("User", back_populates="equipment")
    
    def __repr__(self):
        return f"<Equipment {self.name} ({self.type.value})>"
    
    def get_type_display(self):
        """Получить читаемое название типа техники"""
        type_display = {
            EquipmentType.TRUCK: "🚚 Грузовик",
            EquipmentType.SPECIAL: "🏗️ Спецтехника",
            EquipmentType.TRAILER: "🚛 Прицеп",
            EquipmentType.CRANE: "🏗️ Кран",
            EquipmentType.EXCAVATOR: "🔨 Экскаватор"
        }
        return type_display.get(self.type, "Неизвестно")
    
    def get_info(self):
        """Получить информацию о технике"""
        return (
            f"<b>🚛 {self.name}</b>\n\n"
            f"<b>Тип:</b> {self.get_type_display()}\n"
            f"<b>Владелец:</b> {self.owner.get_full_name() if self.owner else 'Неизвестно'}\n"
            f"<b>Описание:</b> {self.description if self.description else 'нет'}\n"
            f"<b>Грузоподъемность:</b> {self.capacity if self.capacity else 'не указана'} т\n"
            f"<b>Местоположение:</b> {self.location if self.location else 'не указано'}\n"
            f"<b>Цена в час:</b> {self.price_per_hour if self.price_per_hour else 'не указана'} ₽/час\n"
            f"<b>Цена в сутки:</b> {self.price_per_day if self.price_per_day else 'не указана'} ₽/сутки\n"
            f"<b>Статус:</b> {'✅ Доступна' if self.is_available else '❌ Занята'}\n"
        )


class Order(Base):
    """Модель заказа на перевозку"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    cargo_type = Column(String(100), nullable=False)
    weight = Column(Float, nullable=True)  # Вес в тоннах
    volume = Column(Float, nullable=True)  # Объем в м³
    from_location = Column(String(200), nullable=False)
    to_location = Column(String(200), nullable=False)
    distance = Column(Float, nullable=True)  # Расстояние в км
    price = Column(Float, nullable=True)     # Предлагаемая цена
    status = Column(Enum(OrderStatus), default=OrderStatus.CREATED)
    equipment_type = Column(Enum(EquipmentType), nullable=True)
    deadline = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    customer = relationship("User", back_populates="orders", foreign_keys=[customer_id])
    offers = relationship("Offer", back_populates="order")
    
    def __repr__(self):
        return f"<Order {self.title} ({self.status.value})>"
    
    def get_status_display(self):
        """Получить читаемое название статуса"""
        status_display = {
            OrderStatus.CREATED: "📝 Создан",
            OrderStatus.SEARCHING: "🔍 В поиске исполнителя",
            OrderStatus.IN_PROGRESS: "🚚 В работе",
            OrderStatus.COMPLETED: "✅ Завершен",
            OrderStatus.CANCELLED: "❌ Отменен"
        }
        return status_display.get(self.status, "Неизвестно")
    
    def get_info(self):
        """Получить информацию о заказе"""
        return (
            f"<b>📦 Заказ: {self.title}</b>\n\n"
            f"<b>Описание:</b> {self.description if self.description else 'нет'}\n"
            f"<b>Тип груза:</b> {self.cargo_type}\n"
            f"<b>Маршрут:</b> {self.from_location} → {self.to_location}\n"
            f"<b>Вес:</b> {self.weight if self.weight else 'не указан'} т\n"
            f"<b>Объем:</b> {self.volume if self.volume else 'не указан'} м³\n"
            f"<b>Расстояние:</b> {self.distance if self.distance else 'не указано'} км\n"
            f"<b>Цена:</b> {self.price if self.price else 'не указана'} ₽\n"
            f"<b>Статус:</b> {self.get_status_display()}\n"
            f"<b>Срок:</b> {self.deadline.strftime('%d.%m.%Y') if self.deadline else 'не указан'}\n"
            f"<b>Заказчик:</b> {self.customer.get_full_name() if self.customer else 'Неизвестно'}\n"
            f"<b>Создан:</b> {self.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        )


class Offer(Base):
    """Модель предложения/отклика на заказ"""
    __tablename__ = "offers"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    executor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    price = Column(Float, nullable=False)
    message = Column(Text, nullable=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=True)
    status = Column(String(50), default="pending")  # pending, accepted, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    order = relationship("Order", back_populates="offers")
    executor = relationship("User", back_populates="offers")
    equipment = relationship("Equipment", foreign_keys=[equipment_id])
    
    def __repr__(self):
        return f"<Offer for Order {self.order_id} by {self.executor_id}>"
    
    def get_status_display(self):
        """Получить читаемое название статуса"""
        status_display = {
            "pending": "⏳ Ожидает рассмотрения",
            "accepted": "✅ Принят",
            "rejected": "❌ Отклонен"
        }
        return status_display.get(self.status, "Неизвестно")
    
    def get_info(self):
        """Получить информацию о предложении"""
        return (
            f"<b>💼 Предложение #{self.id}</b>\n\n"
            f"<b>К заказу:</b> {self.order.title if self.order else 'Неизвестно'}\n"
            f"<b>Исполнитель:</b> {self.executor.get_full_name() if self.executor else 'Неизвестно'}\n"
            f"<b>Предложенная цена:</b> {self.price} ₽\n"
            f"<b>Сообщение:</b> {self.message if self.message else 'нет'}\n"
            f"<b>Техника:</b> {self.equipment.name if self.equipment else 'не указана'}\n"
            f"<b>Статус:</b> {self.get_status_display()}\n"
            f"<b>Создано:</b> {self.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        )


class Review(Base):
    """Модель отзыва"""
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    order = relationship("Order")
    author = relationship("User", foreign_keys=[author_id])
    target = relationship("User", foreign_keys=[target_id])
    
    def __repr__(self):
        return f"<Review {self.rating}/5 by {self.author_id}>"
    
    def get_stars(self):
        """Получить звездочки для рейтинга"""
        return "⭐" * self.rating
    
    def get_info(self):
        """Получить информацию об отзыве"""
        return (
            f"<b>📝 Отзыв #{self.id}</b>\n\n"
            f"<b>К заказу:</b> {self.order.title if self.order else 'Неизвестно'}\n"
            f"<b>От:</b> {self.author.get_full_name() if self.author else 'Неизвестно'}\n"
            f"<b>Для:</b> {self.target.get_full_name() if self.target else 'Неизвестно'}\n"
            f"<b>Оценка:</b> {self.get_stars()} ({self.rating}/5)\n"
            f"<b>Комментарий:</b> {self.comment if self.comment else 'нет'}\n"
            f"<b>Дата:</b> {self.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        )