# scripts/migrate_data.py
"""
Миграция данных из старой БД в новую
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.infrastructure.database.database_manager import db_manager
from app.infrastructure.database.repository_factory import repository_factory

# Импортируем старую БД
from database import db as old_db


async def migrate_users():
    """Миграция пользователей"""
    print("👤 Мигрируем пользователей...")
    
    user_repo = repository_factory.create_user_repository()
    
    # Получаем всех пользователей из старой БД
    with old_db.conn:
        old_db.cursor.execute("SELECT * FROM users")
        users = old_db.cursor.fetchall()
    
    migrated_count = 0
    
    for user_data in users:
        try:
            # Создаем сущность пользователя
            from app.core.entities.user import User
            user = User(
                user_id=user_data['user_id'],
                username=user_data['username'],
                full_name=user_data['full_name'],
                role=user_data['role'],
                rating=user_data['rating'],
                # created_at нужно преобразовать
            )
            
            # Сохраняем в новую БД
            await user_repo.create_user(user)
            migrated_count += 1
            
            # Если это исполнитель, создаем профиль
            if user.role == 'executor':
                await user_repo.create_executor_profile(user.user_id)
                
        except Exception as e:
            print(f"⚠️ Ошибка миграции пользователя {user_data['user_id']}: {e}")
    
    print(f"✅ Мигрировано пользователей: {migrated_count}/{len(users)}")
    return migrated_count


async def migrate_orders():
    """Миграция заказов"""
    print("\n📦 Мигрируем заказы...")
    
    order_repo = repository_factory.create_order_repository()
    
    # Получаем все заказы из старой БД
    with old_db.conn:
        old_db.cursor.execute("SELECT * FROM orders")
        orders = old_db.cursor.fetchall()
    
    migrated_count = 0
    
    for order_data in orders:
        try:
            # Создаем сущность заказа
            from app.core.entities.order import Order, OrderStatus
            from datetime import datetime
            
            try:
                status = OrderStatus(order_data['status'])
            except:
                status = OrderStatus.ACTIVE
            
            order = Order(
                order_id=order_data['order_id'],
                user_id=order_data['user_id'],
                service_type=order_data['service_type'],
                description=order_data['description'],
                address=order_data['address'],
                desired_price=order_data['desired_price'],
                status=status,
                selected_executor_id=order_data['selected_executor_id']
                # created_at и expires_at нужно преобразовать
            )
            
            # Сохраняем в новую БД
            await order_repo.create_order(order)
            migrated_count += 1
            
        except Exception as e:
            print(f"⚠️ Ошибка миграции заказа {order_data['order_id']}: {e}")
    
    print(f"✅ Мигрировано заказов: {migrated_count}/{len(orders)}")
    return migrated_count


async def run_migration():
    """Запуск миграции"""
    print("🚀 ЗАПУСК МИГРАЦИИ ДАННЫХ")
    print("=" * 50)
    
    # Инициализируем новую БД
    db_manager.init_database()
    
    # Запускаем миграции
    users_count = await migrate_users()
    orders_count = await migrate_orders()
    
    print("\n" + "=" * 50)
    print("📊 РЕЗУЛЬТАТЫ МИГРАЦИИ")
    print("=" * 50)
    print(f"👤 Пользователей: {users_count}")
    print(f"📦 Заказов: {orders_count}")
    print("\n✅ Миграция завершена!")
    
    # TODO: Добавить миграцию техники, предложений, отзывов


if __name__ == "__main__":
    print("⚠️ ВНИМАНИЕ: Этот скрипт мигрирует данные из старой БД в новую.")
    print("Сделайте backup базы данных перед запуском!")
    
    confirm = input("Продолжить? (yes/no): ")
    
    if confirm.lower() == 'yes':
        asyncio.run(run_migration())
    else:
        print("❌ Миграция отменена")