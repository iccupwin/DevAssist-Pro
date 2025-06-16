# Система Анализа Тендерных Предложений

Приложение для автоматизированного анализа и сравнения коммерческих предложений (КП), поступающих на тендер, с исходным техническим заданием (ТЗ) тендера.

## Особенности системы

- Детальное сравнение КП и исходного ТЗ с использованием AI
- Анализ дополнительной информации (протоколы встреч, отчеты и т.д.)
- Оценочная карта с рейтингами по ключевым критериям
- Использование нескольких AI моделей (Claude 3.5 Sonnet, GPT-4o)
- Генерация структурированного экспертного отчета
- Современный пользовательский интерфейс

## Установка и запуск

### Предварительные требования

- Python 3.8 или новее
- API-ключи для Anthropic Claude и OpenAI GPT-4o

### Установка

1. Клонируйте репозиторий:
   ```bash
   git clone [URL репозитория]
   cd [название директории]
   ```

2. Создайте и активируйте виртуальное окружение:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Для Windows: venv\Scripts\activate
   ```

3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

4. Настройте API-ключи:
   - Откройте файл `.env` в корне проекта
   - Добавьте свои API-ключи:
     ```
     ANTHROPIC_API_KEY=your_anthropic_api_key
     OPENAI_API_KEY=your_openai_api_key
     ```

### Запуск приложения

Запустите приложение с помощью Streamlit:

```bash
streamlit run app.py
```

После запуска приложение будет доступно в браузере по адресу `http://localhost:8501`.

## Использование приложения

### Шаг 1: Загрузка документов
- Загрузите файл технического задания (ТЗ) в формате PDF или DOCX
- Загрузите один или несколько файлов коммерческих предложений (КП)
- Опционально загрузите дополнительные файлы или введите текст

### Шаг 2: Анализ и оценка
- Запустите анализ документов
- Ознакомьтесь с результатами сравнения ТЗ и КП
- Выставите рейтинги по ключевым критериям (от 1 до 10)

### Шаг 3: Итоговый отчет
- Просмотрите сгенерированный экспертный отчет
- Ознакомьтесь с итоговой рекомендацией
- Сохраните отчет или начните новый анализ

## Структура проекта

```
.
├── app.py                 # Основной файл приложения
├── src/                   # Исходный код
│   ├── components/        # Компоненты Streamlit UI
│   ├── config/            # Конфигурация и настройки
│   ├── data/              # Данные (загрузки и результаты)
│   ├── models/            # Модели данных
│   ├── services/          # Сервисы (AI API, сравнение и т.д.)
│   └── utils/             # Вспомогательные функции
├── requirements.txt       # Зависимости
└── .env                   # Файл с переменными окружения (API-ключи)
```

## Project Structure

- `backend/`: Contains the Flask (Python) backend application.
- `frontend/`: Contains the React (TypeScript) frontend application.

## Getting Started

### Prerequisites

- Python 3.8+ and pip
- Node.js (LTS recommended) and npm

### Backend Setup

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the backend server:
   ```bash
   flask run --port=5001
   ```
   The backend API will be available at `http://localhost:5001`.

### Frontend Setup

1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the frontend development server:
   ```bash
   npm start
   ```
   The frontend application will open automatically in your browser at `http://localhost:3000`.

## Further Development

Refer to the Technical Specification (ТЗ) document for detailed requirements and features to be implemented. 