# app/core/services/user_service.py
from typing import Optional
from ..entities.user import User, ExecutorProfile
from ..repositories.user_repository import UserRepository


class UserService:
    """Сервис для работы с пользователями"""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    async def get_or_create_user(self, user_id: int, username: str, full_name: str) -> User:
        """Получить существующего пользователя или создать нового"""
        user = await self.user_repository.get_user(user_id)
        
        if not user:
            user = User(
                user_id=user_id,
                username=username,
                full_name=full_name
            )
            user = await self.user_repository.create_user(user)
        
        return user
    
    async def switch_to_executor(self, user_id: int) -> bool:
        """Переключить пользователя в режим исполнителя"""
        user = await self.user_repository.get_user(user_id)
        
        if not user:
            raise ValueError("Пользователь не найден")
        
        if user.role == 'executor':
            return True  # Уже исполнитель
        
        success = await self.user_repository.update_user_role(user_id, 'executor')
        
        if success:
            # Создаем профиль исполнителя
            await self.user_repository.create_executor_profile(user_id)
        
        return success
    
    async def get_executor_profile_info(self, user_id: int) -> dict:
        """Получить информацию о профиле исполнителя"""
        profile = await self.user_repository.get_executor_profile(user_id)
        
        if not profile:
            return {"exists": False, "is_complete": False}
        
        # Проверяем заполненность профиля
        is_complete = bool(
            profile.company_name and
            profile.phone and
            profile.description
        )
        
        return {
            "exists": True,
            "is_complete": is_complete,
            "profile": profile
        }