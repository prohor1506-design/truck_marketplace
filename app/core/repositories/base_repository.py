# app/core/repositories/base_repository.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """Базовый интерфейс репозитория"""
    
    @abstractmethod
    async def get(self, id: int) -> Optional[T]:
        """Получить сущность по ID"""
        pass
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        """Создать сущность"""
        pass
    
    @abstractmethod
    async def update(self, entity: T) -> T:
        """Обновить сущность"""
        pass
    
    @abstractmethod
    async def delete(self, id: int) -> bool:
        """Удалить сущность по ID"""
        pass
    
    @abstractmethod
    async def list(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Получить список сущностей"""
        pass