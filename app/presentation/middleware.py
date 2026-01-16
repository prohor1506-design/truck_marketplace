"""
Middleware для работы с базой данных и пользователями
"""

from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import select

from app.infrastructure.database.models import User
from app.shared.logger import logger


class DatabaseMiddleware(BaseMiddleware):
    """Middleware для предоставления сессии БД и пользователя в хендлерах"""
    
    def __init__(self, session_pool: async_sessionmaker):
        super().__init__()
        self.session_pool = session_pool
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        
        # Создаем сессию БД
        async with self.session_pool() as session:
            data['session'] = session
            
            # Получаем или создаем пользователя для каждого запроса
            user = None
            if hasattr(event, 'from_user') and event.from_user:
                user_id = event.from_user.id
                
                # Ищем пользователя в базе
                from sqlalchemy import select
                stmt = select(User).where(User.telegram_id == user_id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()
                
                if not user:
                    # Создаем базовую запись пользователя
                    user = User(
                        telegram_id=user_id,
                        username=event.from_user.username,
                        first_name=event.from_user.first_name or "",
                        last_name=event.from_user.last_name
                    )
                    session.add(user)
                    await session.commit()
                    await session.refresh(user)
                    logger.info(f"📝 Создан новый пользователь: {user.telegram_id}")
                else:
                    logger.info(f"👤 Найден пользователь: {user.telegram_id}, роль: {user.role}")
                
                data['user'] = user
            
            # Вызываем хендлер с данными
            return await handler(event, data)


# Альтернативный middleware для конкретных роутеров
class UserMiddleware(BaseMiddleware):
    """Middleware только для получения пользователя"""
    
    def __init__(self, session_pool: async_sessionmaker):
        super().__init__()
        self.session_pool = session_pool
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        
        async with self.session_pool() as session:
            # Получаем пользователя
            user = None
            if hasattr(event, 'from_user'):
                from sqlalchemy import select
                stmt = select(User).where(User.telegram_id == event.from_user.id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()
            
            data['user'] = user
            data['session'] = session
            
            return await handler(event, data)