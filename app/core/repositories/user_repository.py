# app/core/repositories/user_repository.py
from abc import ABC, abstractmethod
from typing import Optional, List
from ..entities.user import User, ExecutorProfile


class UserRepository(ABC):
    """Интерфейс репозитория пользователей"""
    
    @abstractmethod
    async def get_user(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        pass
    
    @abstractmethod
    async def create_user(self, user: User) -> User:
        """Создать пользователя"""
        pass
    
    @abstractmethod
    async def update_user_role(self, user_id: int, role: str) -> bool:
        """Обновить роль пользователя"""
        pass
    
    @abstractmethod
    async def get_executor_profile(self, user_id: int) -> Optional[ExecutorProfile]:
        """Получить профиль исполнителя"""
        pass
    
    @abstractmethod
    async def create_executor_profile(self, user_id: int) -> ExecutorProfile:
        """Создать профиль исполнителя"""
        pass
    
    @abstractmethod
    async def update_executor_profile(self, profile: ExecutorProfile) -> ExecutorProfile:
        """Обновить профиль исполнителя"""
        pass