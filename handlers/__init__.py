# handlers/__init__.py
from .commands import router as commands_router
from .customer import router as customer_router
from .executor import router as executor_router
from .equipment import router as equipment_router

__all__ = [
    'commands_router',
    'customer_router', 
    'executor_router',
    'equipment_router'  # ✅ Добавлено
]