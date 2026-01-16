# app/infrastructure/database/alembic_config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем .env файл
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

def get_database_url() -> str:
    """Получаем URL базы данных для Alembic"""
    db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./marketplace.db")
    return db_url