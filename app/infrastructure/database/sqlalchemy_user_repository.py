# app/infrastructure/database/sqlalchemy_user_repository.py

from typing import Optional, List
from datetime import datetime

from sqlalchemy import select, update

from ...core.entities.user import User, ExecutorProfile
from ...core.repositories.user_repository import UserRepository
from .database_manager import db_manager
from .models import UserModel, ExecutorProfileModel
from .mappers import UserMapper, ExecutorProfileMapper


class SqlAlchemyUserRepository(UserRepository):
    """SQLAlchemy реализация репозитория пользователей"""
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """
        Получить пользователя по ID
        
        Args:
            user_id: ID пользователя
        
        Returns:
            User или None если не найден
        """
        with db_manager.get_session() as session:
            # Ищем пользователя в БД
            stmt = select(UserModel).where(UserModel.user_id == user_id)
            result = session.execute(stmt)
            user_model = result.scalar_one_or_none()
            
            if not user_model:
                return None
            
            # Конвертируем модель в сущность
            return UserMapper.model_to_entity(user_model)
    
    async def create_user(self, user: User) -> User:
        """
        Создать пользователя
        
        Args:
            user: Сущность пользователя
        
        Returns:
            Созданный пользователь
        """
        with db_manager.get_session() as session:
            # Конвертируем сущность в модель
            user_model = UserMapper.entity_to_model(user)
            
            # Сохраняем в БД
            session.add(user_model)
            session.flush()  # Получаем ID если он сгенерирован
            
            # Конвертируем обратно в сущность
            created_user = UserMapper.model_to_entity(user_model)
            return created_user
    
    async def update_user_role(self, user_id: int, role: str) -> bool:
        """
        Обновить роль пользователя
        
        Args:
            user_id: ID пользователя
            role: Новая роль ('customer' или 'executor')
        
        Returns:
            True если успешно
        """
        with db_manager.get_session() as session:
            stmt = (
                update(UserModel)
                .where(UserModel.user_id == user_id)
                .values(role=role)
            )
            result = session.execute(stmt)
            session.commit()
            
            # Если роль изменилась на 'executor', создаем профиль
            if role == 'executor':
                self._create_executor_profile_if_not_exists(session, user_id)
            
            return result.rowcount > 0
    
    async def get_executor_profile(self, user_id: int) -> Optional[ExecutorProfile]:
        """
        Получить профиль исполнителя
        
        Args:
            user_id: ID пользователя
        
        Returns:
            ExecutorProfile или None если не найден
        """
        with db_manager.get_session() as session:
            # Ищем профиль в БД
            stmt = select(ExecutorProfileModel).where(ExecutorProfileModel.user_id == user_id)
            result = session.execute(stmt)
            profile_model = result.scalar_one_or_none()
            
            if not profile_model:
                return None
            
            # Конвертируем модель в сущность
            return ExecutorProfileMapper.model_to_entity(profile_model)
    
    async def create_executor_profile(self, user_id: int) -> ExecutorProfile:
        """
        Создать профиль исполнителя
        
        Args:
            user_id: ID пользователя
        
        Returns:
            Созданный профиль
        """
        with db_manager.get_session() as session:
            # Проверяем, не существует ли уже профиль
            existing_stmt = select(ExecutorProfileModel).where(ExecutorProfileModel.user_id == user_id)
            existing_result = session.execute(existing_stmt)
            existing_profile = existing_result.scalar_one_or_none()
            
            if existing_profile:
                # Профиль уже есть, возвращаем его
                return ExecutorProfileMapper.model_to_entity(existing_profile)
            
            # Создаем новый профиль
            profile = ExecutorProfile(user_id=user_id)
            profile_model = ExecutorProfileMapper.entity_to_model(profile)
            
            # Сохраняем в БД
            session.add(profile_model)
            session.flush()
            
            # Возвращаем сущность
            return ExecutorProfileMapper.model_to_entity(profile_model)
    
    async def update_executor_profile(self, profile: ExecutorProfile) -> ExecutorProfile:
        """
        Обновить профиль исполнителя
        
        Args:
            profile: Сущность профиля
        
        Returns:
            Обновленный профиль
        """
        with db_manager.get_session() as session:
            # Ищем существующий профиль
            stmt = select(ExecutorProfileModel).where(ExecutorProfileModel.user_id == profile.user_id)
            result = session.execute(stmt)
            profile_model = result.scalar_one_or_none()
            
            if not profile_model:
                # Если профиля нет, создаем его
                return await self.create_executor_profile(profile.user_id)
            
            # Обновляем поля
            profile_model.company_name = profile.company_name
            profile_model.phone = profile.phone
            profile_model.description = profile.description
            profile_model.experience_years = profile.experience_years
            profile_model.license_number = profile.license_number
            profile_model.insurance_info = profile.insurance_info
            profile_model.work_radius_km = profile.work_radius_km
            profile_model.min_price = profile.min_price
            profile_model.max_price = profile.max_price
            profile_model.service_filter = profile.service_filter
            profile_model.location_text = profile.location_text
            profile_model.latitude = profile.latitude
            profile_model.longitude = profile.longitude
            profile_model.is_verified = profile.is_verified
            profile_model.updated_at = datetime.now()
            
            # Сохраняем изменения
            session.flush()
            
            # Возвращаем обновленную сущность
            return ExecutorProfileMapper.model_to_entity(profile_model)
    
    def _create_executor_profile_if_not_exists(self, session, user_id: int):
        """
        Создать профиль исполнителя если он не существует
        
        Args:
            session: SQLAlchemy сессия
            user_id: ID пользователя
        """
        stmt = select(ExecutorProfileModel).where(ExecutorProfileModel.user_id == user_id)
        result = session.execute(stmt)
        existing_profile = result.scalar_one_or_none()
        
        if not existing_profile:
            profile = ExecutorProfileModel(
                user_id=user_id,
                work_radius_km=20,
                min_price=1000,
                max_price=50000
            )
            session.add(profile)