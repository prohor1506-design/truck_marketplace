# app/infrastructure/database/mappers.py
from datetime import datetime
import json
from typing import Dict, Any

from ...core.entities.user import User, ExecutorProfile
from ...core.entities.order import Order, OrderStatus
from ...core.entities.equipment import Equipment
from ...core.entities.offer import Offer
from ...core.entities.review import Review
from ...core.entities.category import ServiceCategory
from .models import (
    UserModel, ExecutorProfileModel, OrderModel, 
    EquipmentModel, OfferModel, ReviewModel, ServiceCategoryModel
)


class UserMapper:
    """Маппер для пользователя"""
    
    @staticmethod
    def model_to_entity(model: UserModel) -> User:
        """Преобразовать модель в сущность"""
        return User(
            user_id=model.user_id,
            username=model.username,
            full_name=model.full_name,
            role=model.role,
            rating=model.rating,
            created_at=model.created_at
        )
    
    @staticmethod
    def entity_to_model(entity: User) -> UserModel:
        """Преобразовать сущность в модель"""
        return UserModel(
            user_id=entity.user_id,
            username=entity.username,
            full_name=entity.full_name,
            role=entity.role,
            rating=entity.rating,
            created_at=entity.created_at or datetime.now()
        )


class ExecutorProfileMapper:
    """Маппер для профиля исполнителя"""
    
    @staticmethod
    def model_to_entity(model: ExecutorProfileModel) -> ExecutorProfile:
        """Преобразовать модель в сущность"""
        return ExecutorProfile(
            user_id=model.user_id,
            company_name=model.company_name,
            phone=model.phone,
            description=model.description,
            experience_years=model.experience_years,
            license_number=model.license_number,
            insurance_info=model.insurance_info,
            work_radius_km=model.work_radius_km,
            min_price=model.min_price,
            max_price=model.max_price,
            service_filter=model.service_filter,
            location_text=model.location_text,
            latitude=model.latitude,
            longitude=model.longitude,
            is_verified=model.is_verified,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    @staticmethod
    def entity_to_model(entity: ExecutorProfile) -> ExecutorProfileModel:
        """Преобразовать сущность в модель"""
        return ExecutorProfileModel(
            user_id=entity.user_id,
            company_name=entity.company_name,
            phone=entity.phone,
            description=entity.description,
            experience_years=entity.experience_years,
            license_number=entity.license_number,
            insurance_info=entity.insurance_info,
            work_radius_km=entity.work_radius_km,
            min_price=entity.min_price,
            max_price=entity.max_price,
            service_filter=entity.service_filter,
            location_text=entity.location_text,
            latitude=entity.latitude,
            longitude=entity.longitude,
            is_verified=entity.is_verified,
            created_at=entity.created_at or datetime.now(),
            updated_at=entity.updated_at or datetime.now()
        )


class OrderMapper:
    """Маппер для заказа"""
    
    @staticmethod
    def model_to_entity(model: OrderModel) -> Order:
        """Преобразовать модель в сущность"""
        try:
            status = OrderStatus(model.status)
        except ValueError:
            status = OrderStatus.ACTIVE
            
        return Order(
            order_id=model.order_id,
            user_id=model.user_id,
            service_type=model.service_type,
            description=model.description,
            address=model.address,
            desired_price=model.desired_price,
            status=status,
            selected_executor_id=model.selected_executor_id,
            created_at=model.created_at,
            expires_at=model.expires_at
        )
    
    @staticmethod
    def entity_to_model(entity: Order) -> OrderModel:
        """Преобразовать сущность в модель"""
        return OrderModel(
            order_id=entity.order_id,
            user_id=entity.user_id,
            service_type=entity.service_type,
            description=entity.description,
            address=entity.address,
            desired_price=entity.desired_price,
            status=entity.status.value,
            selected_executor_id=entity.selected_executor_id,
            created_at=entity.created_at or datetime.now(),
            expires_at=entity.expires_at
        )


class EquipmentMapper:
    """Маппер для техники"""
    
    @staticmethod
    def model_to_entity(model: EquipmentModel) -> Equipment:
        """Преобразовать модель в сущность"""
        # Обрабатываем JSON features
        features: Dict[str, Any] = {}
        if model.features:
            try:
                if isinstance(model.features, str):
                    features = json.loads(model.features)
                elif isinstance(model.features, dict):
                    features = model.features
            except:
                features = {}
        
        return Equipment(
            id=model.id,
            executor_id=model.executor_id,
            equipment_type=model.equipment_type,
            subtype=model.subtype,
            brand=model.brand,
            model=model.model,
            year=model.year,
            capacity_kg=model.capacity_kg,
            volume_m3=model.volume_m3,
            dimensions=model.dimensions,
            features=features,
            is_available=model.is_available,
            daily_rate=model.daily_rate,
            hourly_rate=model.hourly_rate,
            created_at=model.created_at
        )
    
    @staticmethod
    def entity_to_model(entity: Equipment) -> EquipmentModel:
        """Преобразовать сущность в модель"""
        # Преобразуем features в JSON
        features_json = None
        if entity.features:
            try:
                features_json = json.dumps(entity.features)
            except:
                features_json = "{}"
        
        return EquipmentModel(
            id=entity.id,
            executor_id=entity.executor_id,
            equipment_type=entity.equipment_type,
            subtype=entity.subtype,
            brand=entity.brand,
            model=entity.model,
            year=entity.year,
            capacity_kg=entity.capacity_kg,
            volume_m3=entity.volume_m3,
            dimensions=entity.dimensions,
            features=features_json,
            is_available=entity.is_available,
            daily_rate=entity.daily_rate,
            hourly_rate=entity.hourly_rate,
            created_at=entity.created_at or datetime.now()
        )


class OfferMapper:
    """Маппер для предложения"""
    
    @staticmethod
    def model_to_entity(model: OfferModel) -> Offer:
        """Преобразовать модель в сущность"""
        return Offer(
            id=model.id,
            order_id=model.order_id,
            executor_id=model.executor_id,
            price=model.price,
            comment=model.comment,
            is_selected=model.is_selected,
            created_at=model.created_at
        )
    
    @staticmethod
    def entity_to_model(entity: Offer) -> OfferModel:
        """Преобразовать сущность в модель"""
        return OfferModel(
            id=entity.id,
            order_id=entity.order_id,
            executor_id=entity.executor_id,
            price=entity.price,
            comment=entity.comment,
            is_selected=entity.is_selected,
            created_at=entity.created_at or datetime.now()
        )


class CategoryMapper:
    """Маппер для категории"""
    
    @staticmethod
    def model_to_entity(model: ServiceCategoryModel) -> ServiceCategory:
        """Преобразовать модель в сущность"""
        return ServiceCategory(
            id=model.id,
            name=model.name,
            code=model.code,
            parent_id=model.parent_id,
            equipment_type=model.equipment_type
        )