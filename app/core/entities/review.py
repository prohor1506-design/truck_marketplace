# app/core/entities/review.py
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Review:
    """Сущность отзыва"""
    id: Optional[int] = None
    order_id: str
    from_user_id: int
    to_user_id: int
    rating: int  # 1-5
    comment: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    def validate(self) -> bool:
        """Валидация данных отзыва"""
        return 1 <= self.rating <= 5