import os
from pathlib import Path
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Основные настройки приложения
APP_TITLE = "Devent Tender Analysis AI"
APP_DESCRIPTION = "Интеллектуальная система анализа тендерных предложений"

# Пути
BASE_DIR = Path(__file__).parent.parent.parent # Корень проекта
SRC_DIR = BASE_DIR / "src"
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
RESULT_DIR = DATA_DIR / "results"

# Пути к логотипам
ASSETS_DIR = SRC_DIR / "assets"
ASSETS_DIR.mkdir(exist_ok=True) # Создадим папку если ее еще нет
LOGO_PATH = ASSETS_DIR / "Logo.png" # Основной логотип
LOGO_WITH_NAME_PATH = ASSETS_DIR / "Logo_BrandName.png" # Логотип с названием

# Настройки боковой панели
SIDEBAR_FOOTER = "© 2025 Devent Tender Analysis AI | Все права защищены"

# Настройки AI моделей
AVAILABLE_MODELS = {
    "GPT-4o": "gpt-4o",
    "GPT-4.5 Preview": "gpt-4-turbo-preview",
    "GPT-4 Turbo": "gpt-4-turbo",
    # "o1": "o1", # Модель o1 пока недоступна через стандартный API
    # "o1-preview (Experimental)": "o1-preview", # Экспериментальные модели o1 недоступны
    # "o1-mini (Experimental)": "o1-mini",     # Экспериментальные модели o1 недоступны
    "Claude 3.7 Sonnet (Пользовательский запрос)": "claude-3-7-sonnet-20250219",  # Корректный идентификатор с датой
    "Claude 3.5 Sonnet (Рекомендуется)": "claude-3-5-sonnet-20240620",  # Актуальная модель
    "Claude 3 Opus": "claude-3-opus-20240229"  # Самая мощная модель Anthropic
}

# Критерии оценки (пример)
EVALUATION_CRITERIA = [
    {"id": "technical_compliance", "name": "Техническое соответствие", "weight": 0.3, "description": "Насколько предложенное решение соответствует техническим требованиям ТЗ?"},
    {"id": "functional_completeness", "name": "Функциональная полнота", "weight": 0.3, "description": "Насколько полно реализованы требуемые функции?"},
    {"id": "cost_effectiveness", "name": "Экономическая эффективность", "weight": 0.2, "description": "Насколько адекватна цена предложения рынку и бюджету?"},
    {"id": "timeline_realism", "name": "Реалистичность сроков", "weight": 0.1, "description": "Насколько реалистичны предложенные сроки выполнения работ?"},
    {"id": "vendor_reliability", "name": "Надежность поставщика", "weight": 0.1, "description": "Опыт, репутация и ресурсы поставщика."}
]

# API ключи для сервисов AI
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Конфигурация AI моделей
CLAUDE_MODEL = "claude-3-5-sonnet-20240620"
GPT_MODEL = "gpt-4o"

# Конфигурация интерфейса
APP_ICON = "📊"
THEME_COLOR = "#1a1c23"  # Темная тема, вдохновленная devent.world

# Поддерживаемые форматы файлов
SUPPORTED_FILE_FORMATS = {
    "tz": [".pdf", ".docx"],
    "kp": [".pdf", ".docx"],
    "additional": [".pdf", ".docx", ".txt"]
}

# Цвета бренда
BRAND_COLORS = {
    "primary": "#2E75D6",    # Основной синий цвет
    "secondary": "#1A1E3A",  # Тёмно-синий
    "accent": "#FF5F08",     # Оранжевый
    "background": "#F4F7FC", # Светлый фон
    "text": "#0F172A",       # Тёмный текст
    "light_text": "#64748B"  # Светлый текст
} 