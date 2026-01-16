# app/core/repositories/offer_repository.py
from abc import ABC, abstractmethod
from typing import Optional, List
from ..entities.offer import Offer


class OfferRepository(ABC):
    """Интерфейс репозитория предложений"""
    
    @abstractmethod
    async def create_offer(self, offer: Offer) -> Offer:
        """Создать предложение"""
        pass
    
    @abstractmethod
    async def get_offers_for_order(self, order_id: str) -> List[Offer]:
        """Получить предложения по заказу"""
        pass
    
    @abstractmethod
    async def get_offers_by_executor(self, executor_id: int) -> List[Offer]:
        """Получить предложения исполнителя"""
        pass
    
    @abstractmethod
    async def get_order_offers_count(self, order_id: str) -> int:
        """Получить количество предложений по заказу"""
        pass