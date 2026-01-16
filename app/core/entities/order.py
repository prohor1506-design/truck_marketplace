# app/core/entities/order.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class OrderStatus(Enum):
    """Статусы заказа"""
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass
class Order:
    """Сущность заказа"""
    order_id: str
    user_id: int
    service_type: str
    description: str
    address: str
    desired_price: Optional[int] = None
    status: OrderStatus = OrderStatus.ACTIVE
    selected_executor_id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    def is_active(self) -> bool:
        """Проверка, активен ли заказ"""
        if self.status != OrderStatus.ACTIVE:
            return False
        
        if self.expires_at and self.expires_at < datetime.now():
            return False
            
        return True