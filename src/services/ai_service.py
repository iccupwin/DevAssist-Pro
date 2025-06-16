"""
Модуль для работы с API моделей искусственного интеллекта
"""

import os
import json
from anthropic import Anthropic
from openai import OpenAI
from src.config import settings
import streamlit as st

# Инициализация клиентов
openai_client = None
if os.getenv("OPENAI_API_KEY"):
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
else:
    print("Warning: OpenAI API key not found.")

anthropic_client = None
if os.getenv("ANTHROPIC_API_KEY"):
    loaded_key = os.getenv("ANTHROPIC_API_KEY")
    print(f"[DEBUG] Loaded ANTHROPIC_API_KEY from env: {loaded_key[:10]}...{loaded_key[-4:]}") 
    
    # Временно захардкодим ключ для тестирования, так как он работает в test_anthropic.py
    # Должно быть удалено после тестирования!
    hardcoded_key = "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"
    print(f"[DEBUG] Using hardcoded key instead: {hardcoded_key[:10]}...{hardcoded_key[-4:]}")
    
    anthropic_client = Anthropic(api_key=hardcoded_key)
else:
    print("Warning: Anthropic API key not found.")

def get_ai_response(prompt: str, system_prompt: str = "You are a helpful assistant.", model_id: str = None) -> str:
    """
    Получает ответ от выбранной AI модели.

    Args:
        prompt (str): Основной запрос к модели.
        system_prompt (str): Системная инструкция для модели.
        model_id (str, optional): ID модели для использования. Если None, используется модель из session_state.

    Returns:
        str: Ответ модели.
    """
    if model_id is None:
        model_id = st.session_state.get("selected_model", list(settings.AVAILABLE_MODELS.values())[0])
    
    # Убираем замену модели Claude 3.7 Sonnet
    # Claude 3.7 Sonnet существует и должен использоваться без замены

    try:
        if "gpt" in model_id and openai_client:
            response = openai_client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1 # Низкая температура для более предсказуемого извлечения
            )
            return response.choices[0].message.content
        elif "claude" in model_id and anthropic_client:
            response = anthropic_client.messages.create(
                model=model_id,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000, # Увеличим лимит для ответа
                temperature=0.1
            )
            # Убедимся, что извлекаем текст правильно
            if response.content and isinstance(response.content, list) and hasattr(response.content[0], 'text'):
                return response.content[0].text
            else:
                 print(f"Unexpected Anthropic response format: {response}")
                 return "Error: Could not parse Anthropic response."
        else:
            return f"Error: Model '{model_id}' is not supported or its client is not configured."
    except Exception as e:
        st.error(f"Ошибка при вызове AI модели ({model_id}): {e}")
        return f"Error: Exception during AI call - {e}"

def analyze_with_claude(text, prompt, max_tokens=4000):
    """
    Анализирует текст с помощью модели Claude
    
    Args:
        text (str): Текст для анализа
        prompt (str): Инструкции для модели
        max_tokens (int): Максимальное количество токенов для генерации
        
    Returns:
        str: Результат анализа или None в случае ошибки
    """
    if not anthropic_client:
        print("Ошибка: API ключ для Claude не настроен")
        return None
    
    # Получаем ID выбранной модели или используем Claude 3.5 Sonnet по умолчанию
    model_id = st.session_state.get("selected_model", "claude-3-5-sonnet-20240620")
    
    # Убираем замену несуществующей модели
    # Claude 3.7 Sonnet существует и должен использоваться
    
    try:
        message = anthropic_client.messages.create(
            model=model_id,
            max_tokens=max_tokens,
            messages=[
                {"role": "user", "content": f"{prompt}\n\nТекст для анализа:\n{text}"}
            ]
        )
        return message.content[0].text
    except Exception as e:
        print(f"Ошибка при обращении к API Claude: {e}")
        return None

def generate_with_gpt(prompt, data, max_tokens=4000):
    """
    Генерирует текст с помощью модели GPT
    
    Args:
        prompt (str): Инструкции для модели
        data (dict): Данные для генерации текста
        max_tokens (int): Максимальное количество токенов для генерации
        
    Returns:
        str: Сгенерированный текст или None в случае ошибки
    """
    if not openai_client:
        print("Ошибка: API ключ для OpenAI не настроен")
        return None
    
    try:
        data_json = json.dumps(data, ensure_ascii=False, indent=2)
        
        response = openai_client.chat.completions.create(
            model=settings.GPT_MODEL,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Данные для обработки:\n{data_json}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Ошибка при обращении к API OpenAI: {e}")
        return None

def extract_kp_summary_data(kp_text: str) -> dict:
    """
    Извлекает основные данные из текста КП с помощью AI.
    Возвращает словарь с ключами: company_name, tech_stack, pricing, timeline.
    Ответ должен быть на русском языке.
    """
    system_prompt = (
        "Ты — эксперт-аналитик, специализирующийся на извлечении ключевой информации из коммерческих предложений (КП) "
        "для проектов по разработке ПО. Твоя задача — проанализировать предоставленный текст КП "
        "и извлечь следующую информацию. Верни результат ТОЛЬКО в виде валидного JSON-объекта "
        "с указанными ключами. Не добавляй никаких пояснений или вводного текста вне JSON.\n"
        "Ключи для извлечения:\n"
        "- company_name: Брендовое название компании, подавшей КП (например, 'ТехКорп', 'ИнноСолюшнс'). Избегай формальных юридических названий (ООО, АО, ЗАО), если только это не единственное доступное название.\n"
        "- tech_stack: Краткий список через запятую ключевых технологий, фреймворков или платформ, упомянутых в КП (например, 'Python, Django, React, AWS', 'Java, Spring, Angular, Azure', '.NET, C#, SQL Server'). Если явно не указано, верни 'Не указано'.\n"
        "- pricing: Краткое описание предложенной стоимости и модели ценообразования (например, 'Фиксированная цена: 5 000 000 руб.', 'T&M: 4 500 руб./час, оценка 800 часов', 'Подписка: 150 000 руб./мес'). Если четко не указано, верни 'Не указано'.\n"
        "- timeline: Краткое описание предложенной длительности проекта и этапов (например, '6 месяцев (3 фазы)', '120 рабочих дней', '8-10 недель'). Если не указано, верни 'Не указано'.\n"
        "ВАЖНО: Весь текст в значениях JSON должен быть на русском языке."
    )
    
    prompt = f"Проанализируй следующий текст коммерческого предложения и извлеки требуемую информацию в формате JSON (на русском языке):\n\n---\n{kp_text}\n---"
    
    response_text = get_ai_response(prompt, system_prompt)
    
    # Попытка распарсить JSON
    try:
        # Иногда модели добавляют ```json ... ```, удалим это
        if response_text.strip().startswith("```json"):
             response_text = response_text.strip()[7:-3].strip()
        elif response_text.strip().startswith("```"):
             response_text = response_text.strip()[3:-3].strip()
             
        extracted_data = json.loads(response_text)
        # Проверяем наличие ключей, добавляем значения по умолчанию если отсутствуют
        default_data = {
            "company_name": "Unknown Company",
            "tech_stack": "Not specified",
            "pricing": "Not specified",
            "timeline": "Not specified"
        }
        # Обновляем default_data только теми ключами, что есть в extracted_data
        # и имеют непустые значения
        for key in default_data.keys():
            if key in extracted_data and extracted_data[key]:
                default_data[key] = extracted_data[key]
                
        return default_data
        
    except json.JSONDecodeError as e:
        st.error(f"Не удалось распознать JSON от AI: {e}\nОтвет модели:\n{response_text}")
        # Возвращаем структуру по умолчанию в случае ошибки парсинга
        return {
            "company_name": "Error Parsing AI Response",
            "tech_stack": "Error",
            "pricing": "Error",
            "timeline": "Error"
        }
    except Exception as e:
        st.error(f"Неожиданная ошибка при обработке ответа AI: {e}")
        return {
            "company_name": "Unexpected Error",
            "tech_stack": "Error",
            "pricing": "Error",
            "timeline": "Error"
        }
        

def compare_tz_kp(tz_text: str, kp_text: str) -> dict:
    """
    Сравнивает ТЗ и КП с помощью AI, возвращает оценку соответствия, 
    списки пропущенных и добавленных требований.
    Ответ должен быть на русском языке.
    """
    system_prompt = (
        "Ты — AI-ассистент, специализирующийся на сравнении технических заданий (ТЗ) с коммерческими предложениями (КП) "
        "для разработки ПО. Проанализируй предоставленные тексты ТЗ и КП. Твоя цель — определить оценку соответствия (в процентах), "
        "выявить требования из ТЗ, упущенные в КП, и перечислить существенные функции, предложенные в КП, но отсутствовавшие в ТЗ. "
        "Верни результат ТОЛЬКО в виде валидного JSON-объекта со следующими ключами:\n"
        "- compliance_score: Примерная целочисленная оценка в процентах (0-100), показывающая, насколько хорошо КП соответствует требованиям ТЗ.\n"
        "- missing_requirements: Список строк (на русском языке), где каждая строка кратко описывает ключевое требование из ТЗ, которое НЕ было адекватно рассмотрено или упомянуто в КП.\n"
        "- additional_features: Список строк (на русском языке), где каждая строка кратко описывает существенную функцию, технологию или услугу, предложенную в КП, но НЕ требуемую явно в ТЗ.\n"
        "Не добавляй никаких пояснений или вводного текста вне JSON-объекта. Все текстовые значения должны быть на русском языке."
    )
    
    prompt = (
        f"Сравни следующие Техническое Задание (ТЗ) и Коммерческое Предложение (КП). Предоставь анализ в указанном формате JSON (на русском языке).\n\n"
        f"=== ТЗ (Technical Specification) ===\n{tz_text}\n\n"
        f"=== КП (Commercial Proposal) ===\n{kp_text}\n\n"
        f"Верни ТОЛЬКО JSON-объект."
    )
    
    response_text = get_ai_response(prompt, system_prompt)
    
    try:
        # Очистка от ```json ... ```
        if response_text.strip().startswith("```json"):
            response_text = response_text.strip()[7:-3].strip()
        elif response_text.strip().startswith("```"):
             response_text = response_text.strip()[3:-3].strip()
             
        comparison_data = json.loads(response_text)
        
        # Проверка и установка значений по умолчанию
        default_data = {
            "compliance_score": 0,
            "missing_requirements": [],
            "additional_features": []
        }
        # Обновление значений, если они есть и корректны
        if isinstance(comparison_data.get("compliance_score"), int):
             default_data["compliance_score"] = comparison_data["compliance_score"]
        if isinstance(comparison_data.get("missing_requirements"), list):
             default_data["missing_requirements"] = [str(item) for item in comparison_data["missing_requirements"]]
        if isinstance(comparison_data.get("additional_features"), list):
             default_data["additional_features"] = [str(item) for item in comparison_data["additional_features"]]
             
        return default_data
        
    except json.JSONDecodeError as e:
        st.error(f"Не удалось распознать JSON сравнения от AI: {e}\nОтвет модели:\n{response_text}")
        return {"compliance_score": 0, "missing_requirements": ["Error parsing AI response"], "additional_features": []}
    except Exception as e:
        st.error(f"Неожиданная ошибка при обработке ответа сравнения AI: {e}")
        return {"compliance_score": 0, "missing_requirements": ["Unexpected error"], "additional_features": []}

def generate_recommendation(comparison_result: dict, kp_summary: dict) -> dict:
    """
    Генерирует предварительную рекомендацию на основе результатов сравнения и обзора КП.
    Ответ должен быть на русском языке.
    """
    system_prompt = (
        "Ты — AI-аналитик, предоставляющий предварительные рекомендации по коммерческим предложениям (КП), основываясь на их сравнении с техническими заданиями (ТЗ) и кратком обзоре КП. "
        "Проанализируй предоставленные результаты сравнения (оценка соответствия, упущенные требования, доп. функции) и обзор КП (компания, технологии, цена, сроки). "
        "Предоставь сбалансированное мнение, выделив ключевые сильные и слабые стороны. "
        "Верни результат ТОЛЬКО в виде валидного JSON-объекта со следующими ключами:\n"
        "- strength: Список строк (на русском языке), описывающих 2-4 ключевых положительных аспекта (например, 'Высокий балл соответствия', 'Предложен современный стек технологий', 'Конкурентоспособная цена', 'Четкий график').\n"
        "- weakness: Список строк (на русском языке), описывающих 2-4 ключевых негативных аспекта или риска (например, 'Упущено несколько ключевых требований', 'Сроки выглядят оптимистично', 'Модель ценообразования недостаточно детализирована', 'Выбор технологии может потребовать специфической экспертизы').\n"
        "- summary: Краткое (1-2 предложения) общее заключение (на русском языке) о пригодности предложения.\n"
        "Не добавляй никаких пояснений или вводного текста вне JSON-объекта. Все текстовые значения должны быть на русском языке."
    )
    
    prompt = (
        f"Сгенерируй предварительную рекомендацию на основе следующих данных анализа. Верни ТОЛЬКО JSON-объект (на русском языке).\n\n"
        f"=== Обзор КП ===\nКомпания: {kp_summary.get('company_name', 'N/A')}\n"
        f"Технологии: {kp_summary.get('tech_stack', 'N/A')}\n"
        f"Цена: {kp_summary.get('pricing', 'N/A')}\n"
        f"Сроки: {kp_summary.get('timeline', 'N/A')}\n\n"
        f"=== Результаты Сравнения ===\nОценка соответствия: {comparison_result.get('compliance_score', 'N/A')} %\n"
        f"Упущенные требования: {'; '.join(comparison_result.get('missing_requirements', [])) if comparison_result.get('missing_requirements') else 'Нет'}\n"
        f"Дополнительные функции: {'; '.join(comparison_result.get('additional_features', [])) if comparison_result.get('additional_features') else 'Нет'}\n"
    )

    response_text = get_ai_response(prompt, system_prompt)

    try:
        # Очистка от ```json ... ```
        if response_text.strip().startswith("```json"):
            response_text = response_text.strip()[7:-3].strip()
        elif response_text.strip().startswith("```"):
             response_text = response_text.strip()[3:-3].strip()
             
        recommendation_data = json.loads(response_text)
        
        # Проверка и установка значений по умолчанию
        default_data = {
            "strength": [],
            "weakness": [],
            "summary": "Could not generate summary."
        }
        # Обновление значений
        if isinstance(recommendation_data.get("strength"), list):
            default_data["strength"] = [str(item) for item in recommendation_data["strength"]]
        if isinstance(recommendation_data.get("weakness"), list):
            default_data["weakness"] = [str(item) for item in recommendation_data["weakness"]]
        if isinstance(recommendation_data.get("summary"), str):
            default_data["summary"] = recommendation_data["summary"]
            
        return default_data

    except json.JSONDecodeError as e:
        st.error(f"Не удалось распознать JSON рекомендации от AI: {e}\nОтвет модели:\n{response_text}")
        return {"strength": ["Error parsing AI response"], "weakness": [], "summary": "Error"}
    except Exception as e:
        st.error(f"Неожиданная ошибка при обработке ответа рекомендации AI: {e}")
        return {"strength": [], "weakness": ["Unexpected error"], "summary": "Error"} 