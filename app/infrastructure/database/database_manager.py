"""
Менеджер базы данных для создания таблиц и управления соединениями
"""

import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.shared.config import config
from app.infrastructure.database.models import Base


class DatabaseManager:
    """Менеджер базы данных"""
    
    def __init__(self):
        # SQLite не поддерживает pool_size, убираем его
        if "sqlite" in config.DATABASE_URL:
            # Для SQLite
            self.engine = create_async_engine(
                config.DATABASE_URL,
                echo=config.DATABASE_ECHO,
                connect_args={"check_same_thread": False}  # Для SQLite
            )
        else:
            # Для других БД (PostgreSQL, MySQL)
            self.engine = create_async_engine(
                config.DATABASE_URL,
                echo=config.DATABASE_ECHO,
                pool_size=config.DATABASE_POOL_SIZE,
            )
        
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def create_tables(self):
        """Создание всех таблиц в базе данных"""
        print("🔄 Создание таблиц в базе данных...")
        
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Таблицы созданы успешно")
        
        # Проверяем созданные таблицы
        async with self.engine.connect() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table';")
            )
            tables = result.fetchall()
            print(f"📋 Создано таблиц: {len(tables)}")
            for table in tables:
                print(f"   - {table[0]}")
    
    async def get_session(self):
        """Получение сессии базы данных (контекстный менеджер)"""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    async def close(self):
        """Закрытие соединений с базой данных"""
        await self.engine.dispose()
        print("✅ Соединение с базой данных закрыто")
    
    async def check_connection(self):
        """Проверка соединения с базой данных"""
        try:
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            print("✅ Соединение с базой данных работает")
            return True
        except Exception as e:
            print(f"❌ Ошибка соединения с БД: {e}")
            return False


# Функция для быстрого создания таблиц
async def create_database():
    """Создает базу данных и таблицы"""
    manager = DatabaseManager()
    await manager.create_tables()
    await manager.close()


if __name__ == "__main__":
    # Для запуска из командной строки
    asyncio.run(create_database())