import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID")) if os.getenv("ADMIN_ID") else None

SERVICES = {
    'truck': '🚚 Грузоперевозки',
    'excavator': '🏗️ Экскаватор',
    'crane': '🏗️ Кран',
    'loader': '🏗️ Погрузчик',
    'delivery': '📦 Доставка',
    'moving': '🏠 Квартирный переезд',
    'other': '📝 Другое'
}