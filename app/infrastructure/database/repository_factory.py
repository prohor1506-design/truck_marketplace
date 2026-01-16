# app/infrastructure/database/repository_factory.py - ИСПРАВЛЕННАЯ ВЕРСИЯ

from typing import Type
from ...core.repositories.user_repository import UserRepository
from ...core.repositories.order_repository import OrderRepository
from ...core.repositories.equipment_repository import EquipmentRepository
from ...core.repositories.offer_repository import OfferRepository

# Импортируем SQLAlchemy реализации
from .sqlalchemy_user_repository import SqlAlchemyUserRepository
from .sqlalchemy_order_repository import SqlAlchemyOrderRepository

# Пока используем заглушки для equipment и offer
# TODO: Создать настоящие репозитории
from .stub_repositories import (
    SqlAlchemyEquipmentRepository,
    SqlAlchemyOfferRepository
)


class RepositoryFactory:
    """Фабрика для создания репозиториев"""
    
    def __init__(self, use_sqlalchemy: bool = True):
        """
        Args:
            use_sqlalchemy: Использовать новую SQLAlchemy реализацию (True)
                           или старую (False) для миграции
        """
        self.use_sqlalchemy = use_sqlalchemy
        self._cache = {}  # Кэш созданных репозиториев
    
    def create_user_repository(self) -> UserRepository:
        """Создать репозиторий пользователей"""
        if 'user' not in self._cache:
            if self.use_sqlalchemy:
                self._cache['user'] = SqlAlchemyUserRepository()
            else:
                # Пока нет старой реализации
                from .stub_repositories import StubUserRepository
                self._cache['user'] = StubUserRepository()
        return self._cache['user']
    
    def create_order_repository(self) -> OrderRepository:
        """Создать репозиторий заказов"""
        if 'order' not in self._cache:
            if self.use_sqlalchemy:
                self._cache['order'] = SqlAlchemyOrderRepository()
            else:
                # Пока нет старой реализации
                from .stub_repositories import StubOrderRepository
                self._cache['order'] = StubOrderRepository()
        return self._cache['order']
    
    def create_equipment_repository(self) -> EquipmentRepository:
        """Создать репозиторий техники"""
        if 'equipment' not in self._cache:
            if self.use_sqlalchemy:
                self._cache['equipment'] = SqlAlchemyEquipmentRepository()
            else:
                # Пока нет старой реализации
                from .stub_repositories import StubOrderRepository
                self._cache['equipment'] = StubOrderRepository()
        return self._cache['equipment']
    
    def create_offer_repository(self) -> OfferRepository:
        """Создать репозиторий предложений"""
        if 'offer' not in self._cache:
            if self.use_sqlalchemy:
                self._cache['offer'] = SqlAlchemyOfferRepository()
            else:
                # Пока нет старой реализации
                from .stub_repositories import StubOrderRepository
                self._cache['offer'] = StubOrderRepository()
        return self._cache['offer']


# Создаем глобальную фабрику
repository_factory = RepositoryFactory(use_sqlalchemy=True)