# app/core/services/order_service.py
from typing import Optional, List
from datetime import datetime, timedelta
import random
import string

from ..entities.order import Order, OrderStatus
from ..repositories.order_repository import OrderRepository
from ..repositories.user_repository import UserRepository


class OrderService:
    """Сервис для работы с заказами"""
    
    def __init__(self, order_repository: OrderRepository, user_repository: UserRepository):
        self.order_repository = order_repository
        self.user_repository = user_repository
    
    async def create_order(
        self, 
        user_id: int,
        service_type: str,
        description: str,
        address: str,
        desired_price: Optional[int] = None
    ) -> Order:
        """Создать новый заказ"""
        # Генерируем ID заказа
        order_id = self._generate_order_id()
        
        # Устанавливаем срок действия (7 дней)
        expires_at = datetime.now() + timedelta(days=7)
        
        # Создаем сущность заказа
        order = Order(
            order_id=order_id,
            user_id=user_id,
            service_type=service_type,
            description=description,
            address=address,
            desired_price=desired_price,
            status=OrderStatus.ACTIVE,
            expires_at=expires_at
        )
        
        # Сохраняем в репозитории
        return await self.order_repository.create_order(order)
    
    async def get_user_orders(self, user_id: int) -> List[Order]:
        """Получить заказы пользователя"""
        return await self.order_repository.get_orders_by_user(user_id)
    
    async def get_active_orders(self, exclude_user_id: Optional[int] = None) -> List[Order]:
        """Получить активные заказы"""
        return await self.order_repository.get_active_orders(exclude_user_id)
    
    async def get_order_details(self, order_id: str) -> Optional[dict]:
        """Получить детальную информацию о заказе"""
        order = await self.order_repository.get_order(order_id)
        
        if not order:
            return None
        
        # Получаем информацию о заказчике
        user = await self.user_repository.get_user(order.user_id)
        
        return {
            'order': order,
            'customer': user,
            'is_active': order.is_active()
        }
    
    @staticmethod
    def _generate_order_id() -> str:
        """Сгенерировать ID заказа"""
        timestamp = datetime.now().strftime("%y%m%d%H%M")
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"ORD-{timestamp}-{random_str}"