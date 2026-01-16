# test_new_architecture.py
"""
Тестирование новой Clean Architecture
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.infrastructure.database.database_manager import db_manager
from app.infrastructure.database.repository_factory import repository_factory
from app.shared.dependencies import container
from app.core.entities.user import User
from app.core.entities.order import Order, OrderStatus
from datetime import datetime, timedelta


async def test_database_connection():
    """Тест соединения с БД"""
    print("🔧 Тестируем соединение с БД...")
    
    try:
        db_manager.init_database()
        print("✅ База данных инициализирована")
        
        # Проверяем, что таблицы созданы
        with db_manager.get_session() as session:
            # Простой запрос для проверки
            from app.infrastructure.database.models import UserModel
            from sqlalchemy import text
            session.execute(text("SELECT 1"))
            print("✅ Соединение с БД работает")
            
    except Exception as e:
        print(f"❌ Ошибка БД: {e}")
        return False
    
    return True


async def test_repository_factory():
    """Тест фабрики репозиториев"""
    print("\n🏭 Тестируем фабрику репозиториев...")
    
    try:
        # Создаем репозитории через фабрику
        user_repo = repository_factory.create_user_repository()
        order_repo = repository_factory.create_order_repository()
        equipment_repo = repository_factory.create_equipment_repository()
        offer_repo = repository_factory.create_offer_repository()
        
        print(f"✅ UserRepository: {type(user_repo).__name__}")
        print(f"✅ OrderRepository: {type(order_repo).__name__}")
        print(f"✅ EquipmentRepository: {type(equipment_repo).__name__}")
        print(f"✅ OfferRepository: {type(offer_repo).__name__}")
        
        # Проверяем, что это разные объекты
        assert user_repo is not order_repo
        print("✅ Репозитории созданы как отдельные объекты")
        
    except Exception as e:
        print(f"❌ Ошибка фабрики: {e}")
        return False
    
    return True


async def test_user_repository():
    """Тест репозитория пользователей"""
    print("\n👤 Тестируем UserRepository...")
    
    try:
        user_repo = repository_factory.create_user_repository()
        
        # Тест 1: Создание пользователя
        test_user = User(
            user_id=999999,  # Используем ID, который точно не существует
            username="test_user",
            full_name="Test User"
        )
        
        created_user = await user_repo.create_user(test_user)
        print(f"✅ Пользователь создан: {created_user.user_id}")
        
        # Тест 2: Получение пользователя
        retrieved_user = await user_repo.get_user(999999)
        assert retrieved_user is not None
        print(f"✅ Пользователь получен: {retrieved_user.username}")
        
        # Тест 3: Обновление роли
        await user_repo.update_user_role(999999, "executor")
        
        # Тест 4: Получение профиля исполнителя
        profile = await user_repo.get_executor_profile(999999)
        if profile:
            print(f"✅ Профиль исполнителя получен")
        else:
            print(f"⚠️ Профиль не найден (возможно еще не создан)")
        
        # Тест 5: Создание профиля
        new_profile = await user_repo.create_executor_profile(999999)
        print(f"✅ Профиль создан/получен")
        
        # Очистка тестовых данных (опционально)
        # Можно удалить тестового пользователя если нужно
        
    except Exception as e:
        print(f"❌ Ошибка UserRepository: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


async def test_order_repository():
    """Тест репозитория заказов"""
    print("\n📦 Тестируем OrderRepository...")
    
    try:
        order_repo = repository_factory.create_order_repository()
        
        # Тест 1: Создание заказа
        test_order = Order(
            order_id="TEST-000001",
            user_id=999999,
            service_type="truck",
            description="Test order description",
            address="Test address",
            desired_price=5000,
            status=OrderStatus.ACTIVE,
            expires_at=datetime.now() + timedelta(days=7)
        )
        
        created_order = await order_repo.create_order(test_order)
        print(f"✅ Заказ создан: {created_order.order_id}")
        
        # Тест 2: Получение заказа
        retrieved_order = await order_repo.get_order("TEST-000001")
        assert retrieved_order is not None
        print(f"✅ Заказ получен: {retrieved_order.service_type}")
        
        # Тест 3: Получение заказов пользователя
        user_orders = await order_repo.get_orders_by_user(999999)
        print(f"✅ Заказов пользователя: {len(user_orders)}")
        
        # Тест 4: Получение активных заказов
        active_orders = await order_repo.get_active_orders()
        print(f"✅ Активных заказов: {len(active_orders)}")
        
        # Тест 5: Обновление статуса
        await order_repo.update_order_status("TEST-000001", "completed")
        updated_order = await order_repo.get_order("TEST-000001")
        print(f"✅ Статус обновлен: {updated_order.status}")
        
    except Exception as e:
        print(f"❌ Ошибка OrderRepository: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


async def test_di_container():
    """Тест DI контейнера"""
    print("\n🧪 Тестируем DI контейнер...")
    
    try:
        # Получаем сервисы из контейнера
        user_service = container.get_user_service()
        order_service = container.get_order_service()
        
        print(f"✅ UserService получен: {type(user_service).__name__}")
        print(f"✅ OrderService получен: {type(order_service).__name__}")
        
        # Тест сервисов
        # Тест 1: Создание пользователя через сервис
        user = await user_service.get_or_create_user(
            user_id=888888,
            username="di_test_user",
            full_name="DI Test User"
        )
        print(f"✅ Пользователь через сервис: {user.user_id}")
        
        # Тест 2: Создание заказа через сервис
        order = await order_service.create_order(
            user_id=888888,
            service_type="delivery",
            description="Test order from DI",
            address="DI Test Address",
            desired_price=3000
        )
        print(f"✅ Заказ через сервис: {order.order_id}")
        
    except Exception as e:
        print(f"❌ Ошибка DI контейнера: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


async def run_all_tests():
    """Запуск всех тестов"""
    print("=" * 50)
    print("🧪 ТЕСТИРОВАНИЕ CLEAN ARCHITECTURE")
    print("=" * 50)
    
    tests = [
        ("Соединение с БД", test_database_connection),
        ("Фабрика репозиториев", test_repository_factory),
        ("UserRepository", test_user_repository),
        ("OrderRepository", test_order_repository),
        ("DI контейнер", test_di_container),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Тест: {test_name}")
        try:
            success = await test_func()
            results.append((test_name, success))
            if success:
                print(f"✅ {test_name}: ПРОЙДЕН")
            else:
                print(f"❌ {test_name}: НЕ ПРОЙДЕН")
        except Exception as e:
            print(f"💥 {test_name}: ОШИБКА - {e}")
            results.append((test_name, False))
    
    # Вывод итогов
    print("\n" + "=" * 50)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ ПРОЙДЕН" if success else "❌ НЕ ПРОЙДЕН"
        print(f"{status} - {test_name}")
    
    print(f"\n🎯 ИТОГО: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Можно начинать миграцию.")
        return True
    else:
        print(f"\n⚠️ {total - passed} тестов не пройдено. Нужно исправить ошибки.")
        return False


if __name__ == "__main__":
    # Запускаем тесты
    success = asyncio.run(run_all_tests())
    
    if success:
        print("\n🚀 Готово к миграции! Следующие шаги:")
        print("1. Создать SQLAlchemy реализации для EquipmentRepository и OfferRepository")
        print("2. Начать миграцию handlers/executor.py на новую архитектуру")
        print("3. Постепенно заменять старый код на новый")
    else:
        print("\n🔧 Нужно исправить ошибки перед миграцией")
    
    sys.exit(0 if success else 1)