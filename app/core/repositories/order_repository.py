# app/core/repositories/order_repository.py
from abc import ABC, abstractmethod
from typing import Optional, List
from ..entities.order import Order


class OrderRepository(ABC):
    """Интерфейс репозитория заказов"""
    
    @abstractmethod
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Получить заказ по ID"""
        pass
    
    @abstractmethod
    async def create_order(self, order: Order) -> Order:
        """Создать заказ"""
        pass
    
    @abstractmethod
    async def get_orders_by_user(self, user_id: int) -> List[Order]:
        """Получить заказы пользователя"""
        pass
    
    @abstractmethod
    async def get_active_orders(self, exclude_user_id: Optional[int] = None) -> List[Order]:
        """Получить активные заказы"""
        pass
    
    @abstractmethod
    async def update_order_status(self, order_id: str, status: str) -> bool:
        """Обновить статус заказа"""
        pass