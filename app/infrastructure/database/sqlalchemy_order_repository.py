# app/infrastructure/database/sqlalchemy_order_repository.py

from typing import Optional, List
from datetime import datetime

from sqlalchemy import select, update, and_, or_

from ...core.entities.order import Order, OrderStatus
from ...core.repositories.order_repository import OrderRepository
from .database_manager import db_manager
from .models import OrderModel, UserModel
from .mappers import OrderMapper


class SqlAlchemyOrderRepository(OrderRepository):
    """SQLAlchemy реализация репозитория заказов"""
    
    async def get_order(self, order_id: str) -> Optional[Order]:
        """
        Получить заказ по ID
        
        Args:
            order_id: ID заказа
        
        Returns:
            Order или None если не найден
        """
        with db_manager.get_session() as session:
            stmt = select(OrderModel).where(OrderModel.order_id == order_id)
            result = session.execute(stmt)
            order_model = result.scalar_one_or_none()
            
            if not order_model:
                return None
            
            return OrderMapper.model_to_entity(order_model)
    
    async def create_order(self, order: Order) -> Order:
        """
        Создать заказ
        
        Args:
            order: Сущность заказа
        
        Returns:
            Созданный заказ
        """
        with db_manager.get_session() as session:
            # Конвертируем сущность в модель
            order_model = OrderMapper.entity_to_model(order)
            
            # Сохраняем в БД
            session.add(order_model)
            session.flush()
            
            # Конвертируем обратно в сущность
            return OrderMapper.model_to_entity(order_model)
    
    async def get_orders_by_user(self, user_id: int) -> List[Order]:
        """
        Получить заказы пользователя
        
        Args:
            user_id: ID пользователя
        
        Returns:
            Список заказов
        """
        with db_manager.get_session() as session:
            stmt = (
                select(OrderModel)
                .where(OrderModel.user_id == user_id)
                .order_by(OrderModel.created_at.desc())
            )
            result = session.execute(stmt)
            order_models = result.scalars().all()
            
            return [OrderMapper.model_to_entity(model) for model in order_models]
    
    async def get_active_orders(self, exclude_user_id: Optional[int] = None) -> List[Order]:
        """
        Получить активные заказы
        
        Args:
            exclude_user_id: ID пользователя для исключения
        
        Returns:
            Список активных заказов
        """
        with db_manager.get_session() as session:
            # Базовые условия: статус active и не истек срок
            conditions = [
                OrderModel.status == OrderStatus.ACTIVE.value,
                or_(
                    OrderModel.expires_at.is_(None),
                    OrderModel.expires_at > datetime.now()
                )
            ]
            
            # Добавляем исключение пользователя если нужно
            if exclude_user_id:
                conditions.append(OrderModel.user_id != exclude_user_id)
            
            # Создаем запрос
            stmt = (
                select(OrderModel)
                .where(and_(*conditions))
                .order_by(OrderModel.created_at.desc())
            )
            
            result = session.execute(stmt)
            order_models = result.scalars().all()
            
            return [OrderMapper.model_to_entity(model) for model in order_models]
    
    async def update_order_status(self, order_id: str, status: str) -> bool:
        """
        Обновить статус заказа
        
        Args:
            order_id: ID заказа
            status: Новый статус
        
        Returns:
            True если успешно
        """
        with db_manager.get_session() as session:
            stmt = (
                update(OrderModel)
                .where(OrderModel.order_id == order_id)
                .values(status=status)
            )
            result = session.execute(stmt)
            session.commit()
            
            return result.rowcount > 0