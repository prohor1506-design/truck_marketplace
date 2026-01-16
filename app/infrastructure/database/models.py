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