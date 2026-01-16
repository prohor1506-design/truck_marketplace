# app/core/entities/category.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class ServiceCategory:
    """Категория услуг"""
    id: Optional[int] = None
    name: str
    code: str
    parent_id: Optional[int] = None
    equipment_type: Optional[str] = None