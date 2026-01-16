# app/core/entities/equipment.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class Equipment:
    """Сущность техники"""
    id: Optional[int] = None
    executor_id: int
    equipment_type: str
    subtype: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    capacity_kg: Optional[int] = None
    volume_m3: Optional[float] = None
    dimensions: Optional[str] = None
    features: Dict[str, Any] = field(default_factory=dict)
    is_available: bool = True
    daily_rate: Optional[int] = None
    hourly_rate: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def get_full_name(self) -> str:
        """Полное название техники"""
        if self.brand and self.model:
            return f"{self.brand} {self.model}"
        elif self.brand:
            return self.brand
        elif self.model:
            return self.model
        else:
            return self.equipment_type