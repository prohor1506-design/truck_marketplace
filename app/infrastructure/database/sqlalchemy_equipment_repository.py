# app/infrastructure/database/sqlalchemy_equipment_repository.py
from typing import Optional, List
from sqlalchemy import select, delete, update
from sqlalchemy.orm import Session

from ...core.repositories.equipment_repository import EquipmentRepository
from ...core.entities.equipment import Equipment
from .models import EquipmentModel
from .mappers import EquipmentMapper


class SQLAlchemyEquipmentRepository(EquipmentRepository):
    """Реализация EquipmentRepository на SQLAlchemy"""
    
    def __init__(self, session_factory):
        self.session_factory = session_factory
    
    def _get_session(self) -> Session:
        """Получить сессию"""
        return self.session_factory()
    
    async def get_equipment(self, equipment_id: int) -> Optional[Equipment]:
        """Получить технику по ID"""
        with self._get_session() as session:
            stmt = select(EquipmentModel).where(EquipmentModel.id == equipment_id)
            result = session.execute(stmt)
            equipment_model = result.scalar_one_or_none()
            
            if equipment_model:
                return EquipmentMapper.model_to_entity(equipment_model)
            return None
    
    async def create_equipment(self, equipment: Equipment) -> Equipment:
        """Создать технику"""
        with self._get_session() as session:
            # Преобразуем сущность в модель
            equipment_model = EquipmentMapper.entity_to_model(equipment)
            
            # Сохраняем
            session.add(equipment_model)
            session.flush()
            
            # Возвращаем сущность с ID
            return EquipmentMapper.model_to_entity(equipment_model)
    
    async def get_executor_equipment(self, executor_id: int) -> List[Equipment]:
        """Получить технику исполнителя"""
        with self._get_session() as session:
            stmt = (
                select(EquipmentModel)
                .where(EquipmentModel.executor_id == executor_id)
                .order_by(EquipmentModel.created_at.desc())
            )
            result = session.execute(stmt)
            equipment_models = result.scalars().all()
            
            return [
                EquipmentMapper.model_to_entity(model) 
                for model in equipment_models
            ]
    
    async def update_equipment(self, equipment: Equipment) -> Equipment:
        """Обновить технику"""
        with self._get_session() as session:
            # Находим существующую технику
            stmt = select(EquipmentModel).where(EquipmentModel.id == equipment.id)
            result = session.execute(stmt)
            equipment_model = result.scalar_one_or_none()
            
            if not equipment_model:
                raise ValueError(f"Техника с ID {equipment.id} не найдена")
            
            # Обновляем поля
            equipment_model.equipment_type = equipment.equipment_type
            equipment_model.subtype = equipment.subtype
            equipment_model.brand = equipment.brand
            equipment_model.model = equipment.model
            equipment_model.year = equipment.year
            equipment_model.capacity_kg = equipment.capacity_kg
            equipment_model.volume_m3 = equipment.volume_m3
            equipment_model.dimensions = equipment.dimensions
            
            # Особенности (JSON)
            if equipment.features:
                import json
                equipment_model.features = json.dumps(equipment.features)
            
            equipment_model.is_available = equipment.is_available
            equipment_model.daily_rate = equipment.daily_rate
            equipment_model.hourly_rate = equipment.hourly_rate
            
            session.add(equipment_model)
            
            return EquipmentMapper.model_to_entity(equipment_model)
    
    async def delete_equipment(self, equipment_id: int) -> bool:
        """Удалить технику"""
        with self._get_session() as session:
            stmt = delete(EquipmentModel).where(EquipmentModel.id == equipment_id)
            result = session.execute(stmt)
            
            return result.rowcount > 0
    
    async def toggle_availability(self, equipment_id: int, is_available: bool) -> bool:
        """Изменить доступность техники"""
        with self._get_session() as session:
            stmt = (
                update(EquipmentModel)
                .where(EquipmentModel.id == equipment_id)
                .values(is_available=is_available)
            )
            result = session.execute(stmt)
            
            return result.rowcount > 0