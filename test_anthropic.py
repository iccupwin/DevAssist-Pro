"""
Простой отладочный скрипт для проверки работы API Anthropic
"""
import os
from anthropic import Anthropic

# Ключ API напрямую из .env (вы можете скопировать его сюда для теста)
API_KEY = "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"

print("[DEBUG] Используем ключ API:", API_KEY[:10] + "..." + API_KEY[-4:])

try:
    # Инициализируем клиент Anthropic с явным ключом
    anthropic_client = Anthropic(api_key=API_KEY)
    
    # Попробуем самый простой запрос
    response = anthropic_client.messages.create(
        model="claude-3-opus-20240229",  # Используем гарантированно существующую модель
        system="Ты - помощник для тестирования API. Отвечай коротко.",
        messages=[
            {"role": "user", "content": "Привет, это тест API Anthropic. Ответь одним словом."}
        ],
        max_tokens=10
    )
    
    # Выводим результат
    print("[SUCCESS] Ответ API:")
    if response.content and len(response.content) > 0:
        print(response.content[0].text)
    else:
        print("Пустой ответ")
        
except Exception as e:
    print("[ERROR] Ошибка при вызове API Anthropic:")
    print(e)
    print("\nТип ошибки:", type(e).__name__)
    
    # Попробуем вывести более детальную информацию
    import traceback
    print("\nПолный стек вызовов:")
    traceback.print_exc()
    
print("\n[DONE] Тест завершен.") 