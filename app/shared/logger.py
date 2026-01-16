# app/shared/logger.py - создайте этот файл
"""
Настройка системы логирования
"""

import logging
import sys
from pathlib import Path

from app.shared.config import config


def setup_logger() -> logging.Logger:
    """Настройка логгера"""
    
    # Создаем логгер
    logger = logging.getLogger("truck_marketplace")
    logger.setLevel(getattr(logging, config.LOG_LEVEL))
    
    # Очищаем существующие обработчики
    logger.handlers.clear()
    
    # Форматтер
    formatter = logging.Formatter(
        fmt=config.LOG_FORMAT,
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Создаем папку для логов
    log_file = Path(config.LOG_FILE)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Файловый обработчик
    file_handler = logging.FileHandler(
        filename=log_file,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # Консольный обработчик
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(
        logging.DEBUG if config.DEBUG else getattr(logging, config.LOG_LEVEL)
    )
    
    # Добавляем обработчики
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Настраиваем логирование внешних библиотек
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(
        logging.INFO if config.DATABASE_ECHO else logging.WARNING
    )
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    return logger


# Создаем глобальный логгер
logger = setup_logger()