# app/shared/config.py - создайте этот файл
"""
Простая и надежная конфигурация приложения
"""

import os
from pathlib import Path
from typing import Literal


def load_env_file():
    """Загружает переменные из .env файла в os.environ"""
    env_path = Path(__file__).parent.parent.parent / ".env"
    
    if not env_path.exists():
        print(f"⚠️  Файл .env не найден: {env_path}")
        return False
    
    print(f"🔍 Загрузка .env из: {env_path}")
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Пропускаем комментарии и пустые строки
                if not line or line.startswith('#'):
                    continue
                
                # Разделяем ключ и значение
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Убираем кавычки если есть
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    
                    os.environ[key] = value
        
        print("✅ .env файл загружен")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка загрузки .env: {e}")
        return False


# Загружаем .env файл при импорте модуля
load_env_file()


class Config:
    """Простая и рабочая конфигурация"""
    
    # === БОТ ===
    @property
    def BOT_TOKEN(self) -> str:
        """Токен бота от @BotFather"""
        token = os.getenv("BOT_TOKEN", "")
        return token
    
    @property
    def ADMIN_ID(self) -> int:
        """ID администратора в Telegram"""
        try:
            return int(os.getenv("BOT_ADMIN_ID", "0"))
        except ValueError:
            return 0
    
    @property
    def SKIP_UPDATES(self) -> bool:
        """Пропускать updates при запуске"""
        return os.getenv("BOT_SKIP_UPDATES", "True").lower() == "true"
    
    # === БАЗА ДАННЫХ ===
    @property
    def DATABASE_URL(self) -> str:
        """URL базы данных"""
        return os.getenv("DB_URL", "sqlite+aiosqlite:///./marketplace.db")
    
    @property
    def DATABASE_ECHO(self) -> bool:
        """Логировать SQL запросы"""
        return os.getenv("DB_ECHO", "False").lower() == "true"
    
    @property 
    def DATABASE_POOL_SIZE(self) -> int:
        """Размер пула соединений"""
        try:
            return int(os.getenv("DB_POOL_SIZE", "10"))
        except ValueError:
            return 10
    
    # === ЛОГИРОВАНИЕ ===
    @property
    def LOG_LEVEL(self) -> Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        """Уровень логирования"""
        level = os.getenv("LOG_LEVEL", "INFO").upper()
        if level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            return "INFO"
        return level
    
    @property
    def LOG_FORMAT(self) -> str:
        """Формат логов"""
        return os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    @property
    def LOG_FILE(self) -> str:
        """Файл для логов"""
        return os.getenv("LOG_FILE", "logs/bot.log")
    
    # === ПРИЛОЖЕНИЕ ===
    @property
    def DEBUG(self) -> bool:
        """Режим отладки"""
        return os.getenv("DEBUG", "False").lower() == "true"
    
    @property
    def ENVIRONMENT(self) -> Literal["development", "staging", "production"]:
        """Окружение приложения"""
        env = os.getenv("ENVIRONMENT", "development")
        if env not in ["development", "staging", "production"]:
            return "development"
        return env
    
    def validate(self) -> bool:
        """Проверка конфигурации"""
        print("\n" + "=" * 50)
        print("🔧 ПРОВЕРКА КОНФИГУРАЦИИ")
        print("=" * 50)
        
        errors = []
        warnings = []
        
        # Проверка обязательных полей
        if not self.BOT_TOKEN:
            errors.append("❌ BOT_TOKEN не установлен в .env файле")
        elif "ВАШ_ТОКЕН" in self.BOT_TOKEN:
            errors.append("❌ BOT_TOKEN содержит placeholder. Замените на реальный токен")
        
        if not self.ADMIN_ID or self.ADMIN_ID <= 0:
            warnings.append("⚠️  ADMIN_ID не установлен или равен 0")
        
        # Вывод информации
        print(f"📱 БОТ:")
        print(f"   Токен: {'✅ Есть' if self.BOT_TOKEN and 'ВАШ_ТОКЕН' not in self.BOT_TOKEN else '❌ Нет/Невалидный'}")
        print(f"   Админ ID: {self.ADMIN_ID if self.ADMIN_ID else '❌ Не установлен'}")
        
        print(f"\n🗄️  БАЗА ДАННЫХ:")
        print(f"   URL: {self.DATABASE_URL}")
        print(f"   Echo: {self.DATABASE_ECHO}")
        
        print(f"\n📊 ПРИЛОЖЕНИЕ:")
        print(f"   Режим: {self.ENVIRONMENT}")
        print(f"   Debug: {self.DEBUG}")
        print(f"   Log Level: {self.LOG_LEVEL}")
        
        print("\n" + "=" * 50)
        
        # Вывод ошибок и предупреждений
        if warnings:
            print("\n📢 ПРЕДУПРЕЖДЕНИЯ:")
            for warning in warnings:
                print(f"   {warning}")
        
        if errors:
            print("\n❌ ОШИБКИ:")
            for error in errors:
                print(f"   {error}")
            print("\n💡 РЕКОМЕНДАЦИИ:")
            print("   1. Получите токен бота у @BotFather в Telegram")
            print("   2. Узнайте свой Telegram ID через @userinfobot")
            print("   3. Добавьте их в .env файл:")
            print('      BOT_TOKEN="ваш_реальный_токен"')
            print("      BOT_ADMIN_ID=ваш_id")
            return False
        
        print("✅ Конфигурация проверена успешно!")
        return True


# Создаем глобальный экземпляр конфигурации
config = Config()