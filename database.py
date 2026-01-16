import sqlite3
import json
import math
from datetime import datetime, timedelta
import random
import string

class Database:
    def __init__(self, db_path="marketplace.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.init_db()
    
    def init_db(self):
        """Инициализация всех таблиц"""
        
        # Пользователи
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                role TEXT DEFAULT 'customer',
                rating REAL DEFAULT 5.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Заказы
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                user_id INTEGER,
                service_type TEXT,
                description TEXT,
                address TEXT,
                desired_price INTEGER,
                status TEXT DEFAULT 'active',
                selected_executor_id INTEGER DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (selected_executor_id) REFERENCES users (user_id)
            )
        ''')
        
        # Предложения
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS offers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT,
                executor_id INTEGER,
                price INTEGER,
                comment TEXT DEFAULT '',
                is_selected BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders (order_id),
                FOREIGN KEY (executor_id) REFERENCES users (user_id)
            )
        ''')
        
        # Отзывы
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT,
                from_user_id INTEGER,
                to_user_id INTEGER,
                rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Категории услуг
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS service_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                code TEXT UNIQUE NOT NULL,
                parent_id INTEGER DEFAULT NULL,
                equipment_type TEXT,
                FOREIGN KEY (parent_id) REFERENCES service_categories (id)
            )
        ''')
        
        # Профили исполнителей
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS executor_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                company_name TEXT,
                phone TEXT,
                description TEXT,
                experience_years INTEGER DEFAULT 0,
                license_number TEXT,
                insurance_info TEXT,
                work_radius_km INTEGER DEFAULT 20,
                min_price INTEGER DEFAULT 1000,
                max_price INTEGER DEFAULT 50000,
                service_filter TEXT,
                location_text TEXT,
                latitude REAL,
                longitude REAL,
                location_type TEXT,
                is_verified BOOLEAN DEFAULT 0,
                verification_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Техника исполнителя
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS executor_equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                executor_id INTEGER NOT NULL,
                equipment_type TEXT NOT NULL,
                subtype TEXT,
                brand TEXT,
                model TEXT,
                year INTEGER,
                capacity_kg INTEGER,
                volume_m3 REAL,
                dimensions TEXT,
                features TEXT,
                is_available BOOLEAN DEFAULT 1,
                daily_rate INTEGER,
                hourly_rate INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (executor_id) REFERENCES executor_profiles (user_id)
            )
        ''')
        
        # Геолокация пользователей
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                latitude REAL,
                longitude REAL,
                address TEXT,
                city TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Избранные категории исполнителя
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS executor_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                executor_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                FOREIGN KEY (executor_id) REFERENCES executor_profiles (user_id),
                FOREIGN KEY (category_id) REFERENCES service_categories (id)
            )
        ''')
        
        self.conn.commit()
        
        # Инициализируем базовые категории
        self.init_default_categories()
        
        print("✅ База данных инициализирована")
    
    def init_default_categories(self):
        """Заполняем таблицу категорий услугами по умолчанию"""
        default_categories = [
            {'name': '🚚 Грузоперевозки', 'code': 'trucks', 'parent_id': None, 'equipment_type': 'truck'},
            {'name': '📦 Газель', 'code': 'gazelle', 'parent_id': None, 'equipment_type': 'truck'},
            {'name': '🚛 Фура', 'code': 'truck', 'parent_id': None, 'equipment_type': 'truck'},
            {'name': '🧊 Рефрижератор', 'code': 'refrigerator', 'parent_id': None, 'equipment_type': 'truck'},
            {'name': '🏗️ Спецтехника', 'code': 'special', 'parent_id': None, 'equipment_type': 'special'},
            {'name': '🔨 Экскаватор', 'code': 'excavator', 'parent_id': None, 'equipment_type': 'special'},
            {'name': '🏗️ Кран', 'code': 'crane', 'parent_id': None, 'equipment_type': 'special'},
            {'name': '🏗️ Погрузчик', 'code': 'loader', 'parent_id': None, 'equipment_type': 'special'},
            {'name': '🚜 Бульдозер', 'code': 'bulldozer', 'parent_id': None, 'equipment_type': 'special'},
            {'name': '📦 Доставка', 'code': 'delivery', 'parent_id': None, 'equipment_type': 'universal'},
            {'name': '🏠 Квартирный переезд', 'code': 'moving', 'parent_id': None, 'equipment_type': 'universal'},
            {'name': '📝 Другое', 'code': 'other', 'parent_id': None, 'equipment_type': 'universal'},
        ]
        
        for category in default_categories:
            self.cursor.execute('''
                INSERT OR IGNORE INTO service_categories (name, code, parent_id, equipment_type)
                VALUES (?, ?, ?, ?)
            ''', (category['name'], category['code'], category['parent_id'], category['equipment_type']))
        
        self.conn.commit()
    
    # ===== ГЕОЛОКАЦИЯ =====
    
    @staticmethod
    def haversine_distance(lat1, lon1, lat2, lon2):
        """Рассчитывает расстояние между двумя точками на Земле (в км)"""
        R = 6371.0
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    # ===== ПОЛЬЗОВАТЕЛИ =====
    
    def add_user(self, user_id, username, full_name):
        """Добавление/обновление пользователя"""
        self.cursor.execute(
            '''INSERT OR REPLACE INTO users (user_id, username, full_name) 
               VALUES (?, ?, ?)''',
            (user_id, username, full_name)
        )
        self.conn.commit()
    
    def get_user(self, user_id):
        """Получение информации о пользователя"""
        self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = self.cursor.fetchone()
        return dict(user) if user else None
    
    def update_user_role(self, user_id, role):
        """Изменение роли пользователя"""
        self.cursor.execute(
            "UPDATE users SET role = ? WHERE user_id = ?",
            (role, user_id)
        )
        self.conn.commit()
        
        if role == 'executor':
            self.create_executor_profile(user_id)
        
        return True
    
    def update_user_rating(self, user_id, new_rating):
        """Обновление рейтинга пользователя"""
        self.cursor.execute(
            "UPDATE users SET rating = ? WHERE user_id = ?",
            (new_rating, user_id)
        )
        self.conn.commit()
    
    # ===== ПРОФИЛИ ИСПОЛНИТЕЛЕЙ =====
    
    def create_executor_profile(self, user_id):
        """Создание пустого профиля исполнителя"""
        self.cursor.execute('''
            INSERT OR IGNORE INTO executor_profiles 
            (user_id, work_radius_km, min_price, max_price) 
            VALUES (?, 20, 1000, 50000)
        ''', (user_id,))
        self.conn.commit()
        return True
    
    def get_executor_profile(self, user_id):
        """Получение профиля исполнителя"""
        self.cursor.execute('''
            SELECT ep.*, u.username, u.full_name, u.rating 
            FROM executor_profiles ep
            LEFT JOIN users u ON ep.user_id = u.user_id
            WHERE ep.user_id = ?
        ''', (user_id,))
        profile = self.cursor.fetchone()
        return dict(profile) if profile else None
    
    def update_executor_profile(self, user_id, **kwargs):
        """Обновление профиля исполнителя (БЕЗОПАСНЫЙ МЕТОД)"""
        if not kwargs:
            return False
        
        # Получаем список существующих колонок
        self.cursor.execute("PRAGMA table_info(executor_profiles)")
        existing_columns = [column[1] for column in self.cursor.fetchall()]
        
        # Фильтруем только существующие колонки
        valid_kwargs = {}
        for key, value in kwargs.items():
            if key in existing_columns:
                valid_kwargs[key] = value
            else:
                print(f"⚠️ Колонка '{key}' не существует в таблице executor_profiles")
        
        if not valid_kwargs:
            print("⚠️ Нет допустимых полей для обновления")
            return False
        
        set_clause = ", ".join([f"{key} = ?" for key in valid_kwargs.keys()])
        values = list(valid_kwargs.values())
        values.append(user_id)
        
        query = f"UPDATE executor_profiles SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?"
        self.cursor.execute(query, values)
        self.conn.commit()
        return True
    
    # ===== ТЕХНИКА =====
    
    def add_equipment(self, executor_id, equipment_data):
        """Добавление единицы техники"""
        self.cursor.execute('''
            INSERT INTO executor_equipment 
            (executor_id, equipment_type, subtype, brand, model, year, 
             capacity_kg, volume_m3, dimensions, features, daily_rate, hourly_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            executor_id,
            equipment_data.get('equipment_type'),
            equipment_data.get('subtype'),
            equipment_data.get('brand'),
            equipment_data.get('model'),
            equipment_data.get('year'),
            equipment_data.get('capacity_kg'),
            equipment_data.get('volume_m3'),
            equipment_data.get('dimensions'),
            json.dumps(equipment_data.get('features', {})) if equipment_data.get('features') else None,
            equipment_data.get('daily_rate'),
            equipment_data.get('hourly_rate')
        ))
        self.conn.commit()
        return True
    
    def get_executor_equipment(self, executor_id):
        """Получение всей техники исполнителя"""
        self.cursor.execute('''
            SELECT * FROM executor_equipment 
            WHERE executor_id = ? 
            ORDER BY created_at DESC
        ''', (executor_id,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_equipment(self, equipment_id):
        """Получение техники по ID"""
        self.cursor.execute(
            "SELECT * FROM executor_equipment WHERE id = ?",
            (equipment_id,)
        )
        equipment = self.cursor.fetchone()
        return dict(equipment) if equipment else None
    
    def update_equipment(self, equipment_id, **kwargs):
        """Обновление техники"""
        if not kwargs:
            return False
        
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values())
        values.append(equipment_id)
        
        query = f"UPDATE executor_equipment SET {set_clause} WHERE id = ?"
        self.cursor.execute(query, values)
        self.conn.commit()
        return True
    
    def delete_equipment(self, equipment_id):
        """Удаление техники"""
        self.cursor.execute(
            "DELETE FROM executor_equipment WHERE id = ?",
            (equipment_id,)
        )
        self.conn.commit()
        return True
    
    def toggle_equipment_availability(self, equipment_id, is_available):
        """Изменение статуса доступности техники"""
        self.cursor.execute(
            "UPDATE executor_equipment SET is_available = ? WHERE id = ?",
            (is_available, equipment_id)
        )
        self.conn.commit()
        return True
    
    # ===== ГЕОЛОКАЦИЯ =====
    
    def update_user_location(self, user_id, latitude=None, longitude=None, address=None, city=None):
        """Обновление/добавление локации пользователя"""
        self.cursor.execute('''
            INSERT OR REPLACE INTO user_locations 
            (user_id, latitude, longitude, address, city, last_updated)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, latitude, longitude, address, city))
        self.conn.commit()
        
        # Также обновляем в профиле исполнителя (если есть)
        self.cursor.execute('''
            UPDATE executor_profiles 
            SET location_text = ?, latitude = ?, longitude = ?, location_type = 'coordinates'
            WHERE user_id = ? AND (latitude IS NULL OR longitude IS NULL)
        ''', (address, latitude, longitude, user_id))
        self.conn.commit()
        
        return True
    
    def get_user_location(self, user_id):
        """Получение локации пользователя"""
        self.cursor.execute('''
            SELECT * FROM user_locations WHERE user_id = ?
        ''', (user_id,))
        location = self.cursor.fetchone()
        return dict(location) if location else None
    
    # ===== КАТЕГОРИИ УСЛУГ =====
    
    def get_categories(self, parent_id=None):
        """Получение категорий услуг"""
        if parent_id is not None:
            self.cursor.execute('''
                SELECT * FROM service_categories 
                WHERE parent_id = ?
                ORDER BY name
            ''', (parent_id,))
        else:
            self.cursor.execute('''
                SELECT * FROM service_categories 
                WHERE parent_id IS NULL
                ORDER BY name
            ''')
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_category_by_code(self, code):
        """Получение категории по коду"""
        self.cursor.execute('''
            SELECT * FROM service_categories WHERE code = ?
        ''', (code,))
        category = self.cursor.fetchone()
        return dict(category) if category else None
    
    # ===== ИЗБРАННЫЕ КАТЕГОРИИ =====
    
    def add_executor_category(self, executor_id, category_id):
        """Добавление категории, которую выполняет исполнитель"""
        self.cursor.execute('''
            INSERT OR IGNORE INTO executor_categories (executor_id, category_id)
            VALUES (?, ?)
        ''', (executor_id, category_id))
        self.conn.commit()
        return True
    
    def get_executor_categories(self, executor_id):
        """Получение категорий исполнителя"""
        self.cursor.execute('''
            SELECT sc.* 
            FROM executor_categories ec
            JOIN service_categories sc ON ec.category_id = sc.id
            WHERE ec.executor_id = ?
        ''', (executor_id,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    # ===== ФИЛЬТРАЦИЯ ЗАКАЗОВ (УПРОЩЕННАЯ) =====
    
    def get_filtered_orders_for_executor(self, executor_id):
        """
        УПРОЩЕННАЯ ФИЛЬТРАЦИЯ - только по услуге и цене
        """
        executor_profile = self.get_executor_profile(executor_id)
        
        if not executor_profile:
            return []
        
        # Базовый запрос
        query = """
            SELECT o.*, u.username, u.full_name
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.user_id
            WHERE o.status = 'active' 
            AND datetime(o.expires_at) > datetime('now')
            AND o.user_id != ?
        """
        
        params = [executor_id]
        
        # 1. Фильтр по цене (если указан)
        min_price = executor_profile.get('min_price')
        max_price = executor_profile.get('max_price')
        
        if min_price:
            query += " AND (o.desired_price IS NULL OR o.desired_price >= ?)"
            params.append(min_price)
        
        if max_price:
            query += " AND (o.desired_price IS NULL OR o.desired_price <= ?)"
            params.append(max_price)
        
        # 2. Фильтр по услуге (если указан)
        service_filter = executor_profile.get('service_filter')
        if service_filter and service_filter != 'all':
            query += " AND o.service_type = ?"
            params.append(service_filter)
        
        query += " ORDER BY o.created_at DESC"
        
        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]
    
    # ===== ЗАКАЗЫ =====
    
    def create_order(self, order_id, user_id, service_type, description, address, desired_price):
        """Создание нового заказа"""
        expires_at = datetime.now() + timedelta(days=7)
        
        self.cursor.execute(
            '''INSERT INTO orders (order_id, user_id, service_type, description, address, desired_price, expires_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (order_id, user_id, service_type, description, address, desired_price, expires_at)
        )
        self.conn.commit()
        return True
    
    def get_order(self, order_id):
        """Получение заказа по ID"""
        self.cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
        order = self.cursor.fetchone()
        if order:
            return dict(order)
        return None
    
    def get_orders_by_user(self, user_id):
        """Получение заказов пользователя"""
        self.cursor.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_active_orders(self, exclude_user_id=None):
        """Получение активных заказов"""
        query = """
            SELECT o.*, u.username, u.full_name 
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.user_id
            WHERE o.status = 'active' 
            AND datetime(o.expires_at) > datetime('now')
        """
        
        params = []
        if exclude_user_id:
            query += " AND o.user_id != ?"
            params.append(exclude_user_id)
        
        query += " ORDER BY o.created_at DESC"
        
        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]
    
    def update_order_status(self, order_id, status):
        """Обновление статуса заказа"""
        self.cursor.execute(
            "UPDATE orders SET status = ? WHERE order_id = ?",
            (status, order_id)
        )
        self.conn.commit()
        return True
    
    def select_executor_for_order(self, order_id, executor_id):
        """Выбор исполнителя для заказа"""
        self.cursor.execute(
            "UPDATE orders SET selected_executor_id = ?, status = 'in_progress' WHERE order_id = ?",
            (executor_id, order_id)
        )
        
        self.cursor.execute(
            "UPDATE offers SET is_selected = 1 WHERE order_id = ? AND executor_id = ?",
            (order_id, executor_id)
        )
        
        self.conn.commit()
        return True
    
    # ===== ПРЕДЛОЖЕНИЯ =====
    
    def create_offer(self, order_id, executor_id, price, comment=""):
        """Создание предложения от исполнителя"""
        self.cursor.execute(
            "SELECT * FROM offers WHERE order_id = ? AND executor_id = ?",
            (order_id, executor_id)
        )
        existing = self.cursor.fetchone()
        
        if existing:
            self.cursor.execute(
                "UPDATE offers SET price = ?, comment = ? WHERE order_id = ? AND executor_id = ?",
                (price, comment, order_id, executor_id)
            )
        else:
            self.cursor.execute(
                "INSERT INTO offers (order_id, executor_id, price, comment) VALUES (?, ?, ?, ?)",
                (order_id, executor_id, price, comment)
            )
        
        self.conn.commit()
        return True
    
    def get_offers_for_order(self, order_id):
        """Получение предложений по заказу"""
        self.cursor.execute('''
            SELECT o.*, u.username, u.full_name, u.rating
            FROM offers o
            LEFT JOIN users u ON o.executor_id = u.user_id
            WHERE o.order_id = ?
            ORDER BY o.price ASC
        ''', (order_id,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_offers_by_executor(self, executor_id):
        """Получение предложений исполнителя"""
        self.cursor.execute('''
            SELECT o.*, ord.service_type, ord.description, ord.status
            FROM offers o
            LEFT JOIN orders ord ON o.order_id = ord.order_id
            WHERE o.executor_id = ?
            ORDER BY o.created_at DESC
        ''', (executor_id,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_order_offers_count(self, order_id):
        """Количество предложений по заказу"""
        self.cursor.execute(
            "SELECT COUNT(*) as count FROM offers WHERE order_id = ?",
            (order_id,)
        )
        result = self.cursor.fetchone()
        return result['count'] if result else 0
    
    # ===== ОТЗЫВЫ =====
    
    def add_review(self, order_id, from_user_id, to_user_id, rating, comment):
        """Добавление отзыва"""
        self.cursor.execute(
            '''INSERT INTO reviews (order_id, from_user_id, to_user_id, rating, comment)
               VALUES (?, ?, ?, ?, ?)''',
            (order_id, from_user_id, to_user_id, rating, comment)
        )
        self.conn.commit()
        
        self.update_user_rating(to_user_id, rating)
        return True
    
    def get_user_reviews(self, user_id):
        """Получение отзывов о пользователе"""
        self.cursor.execute(
            "SELECT * FROM reviews WHERE to_user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        return [dict(row) for row in self.cursor.fetchall()]
    
    # ===== СТАТИСТИКА =====
    
    def get_user_stats(self, user_id):
        """Получение статистики пользователя"""
        user = self.get_user(user_id)
        if not user:
            return None
        
        stats = {
            'user': user,
            'orders_count': 0,
            'offers_count': 0,
            'completed_orders': 0,
            'average_rating': user.get('rating', 0)
        }
        
        self.cursor.execute(
            "SELECT COUNT(*) as count FROM orders WHERE user_id = ?",
            (user_id,)
        )
        stats['orders_count'] = self.cursor.fetchone()['count']
        
        self.cursor.execute(
            "SELECT COUNT(*) as count FROM offers WHERE executor_id = ?",
            (user_id,)
        )
        stats['offers_count'] = self.cursor.fetchone()['count']
        
        self.cursor.execute(
            "SELECT COUNT(*) as count FROM orders WHERE user_id = ? AND status = 'completed'",
            (user_id,)
        )
        stats['completed_orders'] = self.cursor.fetchone()['count']
        
        return stats
    
    def close(self):
        """Закрытие соединения"""
        self.conn.close()

# Глобальный экземпляр БД
db = Database()