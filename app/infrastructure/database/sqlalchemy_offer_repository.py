# app/infrastructure/database/sqlalchemy_offer_repository.py
from typing import List
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from ...core.repositories.offer_repository import OfferRepository
from ...core.entities.offer import Offer
from .models import OfferModel, UserModel, OrderModel
from .mappers import OfferMapper


class SQLAlchemyOfferRepository(OfferRepository):
    """Реализация OfferRepository на SQLAlchemy"""
    
    def __init__(self, session_factory):
        self.session_factory = session_factory
    
    def _get_session(self) -> Session:
        """Получить сессию"""
        return self.session_factory()
    
    async def create_offer(self, offer: Offer) -> Offer:
        """Создать предложение"""
        with self._get_session() as session:
            # Проверяем, не существует ли уже предложение
            stmt = select(OfferModel).where(
                and_(
                    OfferModel.order_id == offer.order_id,
                    OfferModel.executor_id == offer.executor_id
                )
            )
            result = session.execute(stmt)
            existing_offer = result.scalar_one_or_none()
            
            if existing_offer:
                # Обновляем существующее
                existing_offer.price = offer.price
                existing_offer.comment = offer.comment
                session.add(existing_offer)
                session.flush()
                return OfferMapper.model_to_entity(existing_offer)
            else:
                # Создаем новое
                offer_model = OfferMapper.entity_to_model(offer)
                session.add(offer_model)
                session.flush()
                return OfferMapper.model_to_entity(offer_model)
    
    async def get_offers_for_order(self, order_id: str) -> List[Offer]:
        """Получить предложения по заказу"""
        with self._get_session() as session:
            stmt = (
                select(OfferModel)
                .where(OfferModel.order_id == order_id)
                .order_by(OfferModel.price.asc())  # Сортируем по цене (дешевые первые)
            )
            result = session.execute(stmt)
            offer_models = result.scalars().all()
            
            return [
                OfferMapper.model_to_entity(model) 
                for model in offer_models
            ]
    
    async def get_offers_by_executor(self, executor_id: int) -> List[dict]:
        """Получить предложения исполнителя с информацией о заказах"""
        with self._get_session() as session:
            # JOIN предложений с заказами
            stmt = (
                select(OfferModel, OrderModel)
                .join(OrderModel, OfferModel.order_id == OrderModel.order_id)
                .where(OfferModel.executor_id == executor_id)
                .order_by(OfferModel.created_at.desc())
            )
            
            result = session.execute(stmt)
            rows = result.all()
            
            offers_with_orders = []
            for offer_model, order_model in rows:
                offer_dict = {
                    'offer': OfferMapper.model_to_entity(offer_model),
                    'order_service_type': order_model.service_type,
                    'order_description': order_model.description,
                    'order_status': order_model.status
                }
                offers_with_orders.append(offer_dict)
            
            return offers_with_orders
    
    async def get_order_offers_count(self, order_id: str) -> int:
        """Получить количество предложений по заказу"""
        with self._get_session() as session:
            stmt = select(OfferModel).where(OfferModel.order_id == order_id)
            result = session.execute(stmt)
            offers = result.scalars().all()
            
            return len(offers)
    
    async def get_offers_with_executor_info(self, order_id: str) -> List[dict]:
        """Получить предложения с информацией об исполнителях"""
        with self._get_session() as session:
            # JOIN предложений с пользователями
            stmt = (
                select(OfferModel, UserModel)
                .join(UserModel, OfferModel.executor_id == UserModel.user_id)
                .where(OfferModel.order_id == order_id)
                .order_by(OfferModel.price.asc())
            )
            
            result = session.execute(stmt)
            rows = result.all()
            
            offers_info = []
            for offer_model, user_model in rows:
                offer_info = {
                    'id': offer_model.id,
                    'price': offer_model.price,
                    'comment': offer_model.comment,
                    'is_selected': offer_model.is_selected,
                    'created_at': offer_model.created_at,
                    'executor_id': user_model.user_id,
                    'executor_username': user_model.username,
                    'executor_full_name': user_model.full_name,
                    'executor_rating': user_model.rating
                }
                offers_info.append(offer_info)
            
            return offers_info