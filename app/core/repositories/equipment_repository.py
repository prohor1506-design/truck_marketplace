# app/core/repositories/equipment_repository.py
from abc import ABC, abstractmethod
from typing import Optional, List
from ..entities.equipment import Equipment


class EquipmentRepository(ABC):
    """Интерфейс репозитория техники"""
    
    @abstractmethod
    async def get_equipment(self, equipment_id: int) -> Optional[Equipment]:
        """Получить технику по ID"""
        pass
    
    @abstractmethod
    async def create_equipment(self, equipment: Equipment) -> Equipment:
        """Создать технику"""
        pass
    
    @abstractmethod
    async def get_executor_equipment(self, executor_id: int) -> List[Equipment]:
        """Получить технику исполнителя"""
        pass
    
    @abstractmethod
    async def update_equipment(self, equipment: Equipment) -> Equipment:
        """Обновить технику"""
        pass
    
    @abstractmethod
    async def delete_equipment(self, equipment_id: int) -> bool:
        """Удалить технику"""
        pass
    
    @abstractmethod
    async def toggle_availability(self, equipment_id: int, is_available: bool) -> bool:
        """Изменить доступность техники"""
        pass