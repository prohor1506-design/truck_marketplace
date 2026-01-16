# app/core/entities/user.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """Сущность пользователя"""
    user_id: int
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: str = "customer"
    rating: float = 5.0
    created_at: datetime = field(default_factory=datetime.now)
    
    def is_executor(self) -> bool:
        return self.role == 'executor'
    
    def is_customer(self) -> bool:
        return self.role == 'customer'


@dataclass
class ExecutorProfile:
    """Профиль исполнителя"""
    user_id: int
    company_name: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    experience_years: int = 0
    license_number: Optional[str] = None
    insurance_info: Optional[str] = None
    work_radius_km: int = 20
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    service_filter: Optional[str] = None
    location_text: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_verified: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)