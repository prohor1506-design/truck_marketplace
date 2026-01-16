# utils.py

import random
import string
import re
from datetime import datetime

# Генерация ID заказа
def generate_order_id():
    """Генерация уникального ID для заказа"""
    return f"ORD{''.join(random.choices(string.ascii_uppercase, k=6))}"

# Валидация телефона
def validate_phone(phone: str) -> tuple[bool, str]:
    """Валидация российского номера телефона"""
    phone_clean = re.sub(r'[\s\(\)\-]', '', phone)
    phone_pattern = r'^(\+7|8)\d{10}$'
    
    if not re.match(phone_pattern, phone_clean):
        return False, "❌ Неверный формат телефона.\nВведите в формате +7XXXXXXXXXX или 8XXXXXXXXXX:"
    
    return True, phone_clean

# Форматирование даты
def format_datetime(dt_str: str) -> str:
    """Форматирование даты для отображения"""
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime("%d.%m.%Y %H:%M")
    except:
        return dt_str[:16]

# Проверка минимальной длины текста
def validate_text_length(text: str, min_length: int = 10) -> bool:
    """Проверка минимальной длины текста"""
    return len(text.strip()) >= min_length

# Форматирование цены
def format_price(price: int) -> str:
    """Форматирование цены с разделителями"""
    return f"{price:,}".replace(",", " ") + " ₽"