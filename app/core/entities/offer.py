# app/core/entities/offer.py
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Offer:
    """Сущность предложения"""
    id: Optional[int] = None
    order_id: str
    executor_id: int
    price: int
    comment: str = ""
    is_selected: bool = False
    created_at: datetime = field(default_factory=datetime.now)