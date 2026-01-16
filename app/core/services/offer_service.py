# app/core/services/offer_service.py

from typing import List, Optional
from datetime import datetime

from ..entities.offer import Offer
from ..entities.order import Order, OrderStatus
from ..repositories.offer_repository import OfferRepository
from ..repositories.order_repository import OrderRepository
from ..repositories.user_repository import UserRepository


class OfferService:
    """Сервис для работы с предложениями"""
    
    def __init__(
        self, 
        offer_repository: OfferRepository,
        order_repository: OrderRepository,
        user_repository: UserRepository
    ):
        self.offer_repository = offer_repository
        self.order_repository = order_repository
        self.user_repository = user_repository
    
    async def create_offer(self, order_id: str, executor_id: int, price: int, comment: str = "") -> Offer:
        """
        Создать предложение по заказу
        
        Args:
            order_id: ID заказа
            executor_id: ID исполнителя
            price: Цена предложения
            comment: Комментарий
        
        Returns:
            Созданное предложение
        """
        # Проверяем, что заказ существует и активен
        order = await self.order_repository.get_order(order_id)
        if not order:
            raise ValueError(f"Заказ с ID {order_id} не найден")
        
        # Проверяем, что заказ активен
        if not order.is_active():
            raise ValueError("Заказ неактивен или истек срок")
        
        # Проверяем, что исполнитель существует
        executor = await self.user_repository.get_user(executor_id)
        if not executor:
            raise ValueError(f"Исполнитель с ID {executor_id} не найден")
        
        # Проверяем, что исполнитель не является заказчиком
        if order.user_id == executor_id:
            raise ValueError("Нельзя делать предложение на свой же заказ")
        
        # Проверяем, не было ли уже предложения от этого исполнителя
        existing_offers = await self.offer_repository.get_offers_for_order(order_id)
        for offer in existing_offers:
            if offer.executor_id == executor_id:
                raise ValueError("Вы уже делали предложение по этому заказу")
        
        # Создаем предложение
        offer = Offer(
            order_id=order_id,
            executor_id=executor_id,
            price=price,
            comment=comment,
            created_at=datetime.now()
        )
        
        # Сохраняем
        return await self.offer_repository.create_offer(offer)
    
    async def get_offers_for_order(self, order_id: str, include_executor_info: bool = True) -> List[dict]:
        """
        Получить предложения по заказу
        
        Args:
            order_id: ID заказа
            include_executor_info: Включать информацию об исполнителях
        
        Returns:
            Список предложений с дополнительной информацией
        """
        offers = await self.offer_repository.get_offers_for_order(order_id)
        
        if not include_executor_info or not offers:
            return offers
        
        # Добавляем информацию об исполнителях
        result = []
        for offer in offers:
            executor = await self.user_repository.get_user(offer.executor_id)
            executor_profile = await self.user_repository.get_executor_profile(offer.executor_id)
            
            offer_dict = {
                'offer': offer,
                'executor': executor,
                'executor_profile': executor_profile
            }
            result.append(offer_dict)
        
        return result
    
    async def get_executor_offers(self, executor_id: int, include_order_info: bool = True) -> List[dict]:
        """
        Получить предложения исполнителя
        
        Args:
            executor_id: ID исполнителя
            include_order_info: Включать информацию о заказах
        
        Returns:
            Список предложений с дополнительной информацией
        """
        offers = await self.offer_repository.get_offers_by_executor(executor_id)
        
        if not include_order_info or not offers:
            return offers
        
        # Добавляем информацию о заказах
        result = []
        for offer in offers:
            order = await self.order_repository.get_order(offer.order_id)
            
            offer_dict = {
                'offer': offer,
                'order': order
            }
            result.append(offer_dict)
        
        return result
    
    async def select_offer(self, order_id: str, offer_id: int, customer_id: int) -> bool:
        """
        Выбрать предложение исполнителя
        
        Args:
            order_id: ID заказа
            offer_id: ID предложения
            customer_id: ID заказчика (для проверки прав)
        
        Returns:
            True если успешно
        """
        # Проверяем, что заказ существует и принадлежит заказчику
        order = await self.order_repository.get_order(order_id)
        if not order:
            raise ValueError("Заказ не найден")
        
        if order.user_id != customer_id:
            raise PermissionError("Вы не можете выбирать исполнителя для чужого заказа")
        
        # Получаем все предложения по заказу
        offers = await self.offer_repository.get_offers_for_order(order_id)
        selected_offer = None
        
        for offer in offers:
            if offer.id == offer_id:
                selected_offer = offer
                break
        
        if not selected_offer:
            raise ValueError("Предложение не найдено")
        
        # TODO: Обновить статус заказа и выбранное предложение
        # Это будет реализовано в репозитории
        
        return True
    
    async def get_order_offers_count(self, order_id: str) -> int:
        """
        Получить количество предложений по заказу
        
        Args:
            order_id: ID заказа
        
        Returns:
            Количество предложений
        """
        return await self.offer_repository.get_order_offers_count(order_id)