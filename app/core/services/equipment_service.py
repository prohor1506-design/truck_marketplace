# app/core/services/equipment_service.py

from typing import List, Optional, Dict, Any
from datetime import datetime

from ..entities.equipment import Equipment
from ..repositories.equipment_repository import EquipmentRepository
from ..repositories.user_repository import UserRepository


class EquipmentService:
    """Сервис для работы с техникой исполнителей"""
    
    def __init__(self, equipment_repository: EquipmentRepository, user_repository: UserRepository):
        self.equipment_repository = equipment_repository
        self.user_repository = user_repository
    
    async def add_equipment(self, executor_id: int, equipment_data: Dict[str, Any]) -> Equipment:
        """
        Добавить новую технику исполнителю
        
        Args:
            executor_id: ID исполнителя
            equipment_data: Данные техники
        
        Returns:
            Созданная техника
        """
        # Проверяем, что исполнитель существует
        executor = await self.user_repository.get_user(executor_id)
        if not executor:
            raise ValueError(f"Исполнитель с ID {executor_id} не найден")
        
        # Проверяем, что исполнитель действительно исполнитель
        if not executor.is_executor():
            raise ValueError(f"Пользователь с ID {executor_id} не является исполнителем")
        
        # Создаем сущность техники
        equipment = Equipment(
            executor_id=executor_id,
            equipment_type=equipment_data.get('equipment_type'),
            subtype=equipment_data.get('subtype'),
            brand=equipment_data.get('brand'),
            model=equipment_data.get('model'),
            year=equipment_data.get('year'),
            capacity_kg=equipment_data.get('capacity_kg'),
            volume_m3=equipment_data.get('volume_m3'),
            dimensions=equipment_data.get('dimensions'),
            features=equipment_data.get('features', {}),
            daily_rate=equipment_data.get('daily_rate'),
            hourly_rate=equipment_data.get('hourly_rate'),
            created_at=datetime.now()
        )
        
        # Сохраняем в репозитории
        return await self.equipment_repository.create_equipment(equipment)
    
    async def get_executor_equipment(self, executor_id: int) -> List[Equipment]:
        """
        Получить всю технику исполнителя
        
        Args:
            executor_id: ID исполнителя
        
        Returns:
            Список техники
        """
        return await self.equipment_repository.get_executor_equipment(executor_id)
    
    async def update_equipment(self, equipment_id: int, update_data: Dict[str, Any]) -> Equipment:
        """
        Обновить данные техники
        
        Args:
            equipment_id: ID техники
            update_data: Данные для обновления
        
        Returns:
            Обновленная техника
        """
        # Получаем текущую технику
        equipment = await self.equipment_repository.get_equipment(equipment_id)
        if not equipment:
            raise ValueError(f"Техника с ID {equipment_id} не найдена")
        
        # Обновляем поля
        for key, value in update_data.items():
            if hasattr(equipment, key):
                setattr(equipment, key, value)
        
        # Сохраняем изменения
        return await self.equipment_repository.update_equipment(equipment)
    
    async def delete_equipment(self, executor_id: int, equipment_id: int) -> bool:
        """
        Удалить технику
        
        Args:
            executor_id: ID исполнителя (для проверки прав)
            equipment_id: ID техники
        
        Returns:
            True если удалено успешно
        """
        # Проверяем, что техника принадлежит исполнителю
        equipment = await self.equipment_repository.get_equipment(equipment_id)
        if not equipment:
            return False
        
        if equipment.executor_id != executor_id:
            raise PermissionError("Вы не можете удалить чужую технику")
        
        # Удаляем
        return await self.equipment_repository.delete_equipment(equipment_id)
    
    async def toggle_equipment_availability(self, equipment_id: int, is_available: bool) -> bool:
        """
        Изменить статус доступности техники
        
        Args:
            equipment_id: ID техники
            is_available: Новый статус доступности
        
        Returns:
            True если успешно
        """
        return await self.equipment_repository.toggle_availability(equipment_id, is_available)
    
    async def get_available_equipment_by_type(self, equipment_type: str) -> List[Equipment]:
        """
        Получить доступную технику по типу
        
        Args:
            equipment_type: Тип техники (truck, excavator и т.д.)
        
        Returns:
            Список доступной техники
        """
        # Пока заглушка - будет реализовано в репозитории
        all_equipment = []
        # TODO: Реализовать в репозитории
        return [eq for eq in all_equipment if eq.equipment_type == equipment_type and eq.is_available]