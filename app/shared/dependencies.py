# app/shared/dependencies.py - ПОЛНОСТЬЮ ПЕРЕДЕЛАТЬ

from typing import Annotated
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.shared.config import settings
from app.core.repositories import (
    UserRepository,
    OrderRepository,
    EquipmentRepository,
    OfferRepository
)
from app.core.services import (
    UserService,
    OrderService,
    EquipmentService,
    OfferService
)
from app.infrastructure.database.repository_factory import RepositoryFactory

class DependencyContainer:
    """Контейнер зависимостей"""
    
    def __init__(self):
        self._bot: Optional[Bot] = None
        self._dp: Optional[Dispatcher] = None
        self._engine = None
        self._session_factory = None
        
    async def init_database(self):
        """Инициализация базы данных"""
        self._engine = create_async_engine(
            settings.database.url,
            echo=settings.database.echo,
            pool_size=settings.database.pool_size
        )
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Создаем таблицы
        from app.infrastructure.database.models import Base
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def init_bot(self):
        """Инициализация бота"""
        self._bot = Bot(token=settings.bot.token)
        self._dp = Dispatcher(storage=MemoryStorage())
    
    def get_session(self) -> AsyncSession:
        """Получение сессии БД"""
        return self._session_factory()
    
    def get_user_repository(self) -> UserRepository:
        """Фабрика репозитория пользователей"""
        from app.infrastructure.database.sqlalchemy_user_repository import SQLAlchemyUserRepository
        return SQLAlchemyUserRepository(self.get_session())
    
    def get_user_service(self) -> UserService:
        """Фабрика сервиса пользователей"""
        return UserService(self.get_user_repository())
    
    # Аналогично для других репозиториев и сервисов...
    
    async def shutdown(self):
        """Корректное завершение"""
        if self._bot:
            await self._bot.session.close()
        if self._engine:
            await self._engine.dispose()

# Глобальный контейнер зависимостей
container = DependencyContainer()