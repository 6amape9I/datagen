import requests
import sys

# URL твоего сервиса (API)
# Используем 127.0.0.1 вместо localhost, чтобы избежать путаницы с IPv6
API_URL = "http://127.0.0.1:8000/generate"


def test_connection():
    print(f"📡 Отправляем запрос на {API_URL}...")

    # Промпт для теста
    payload = {
        "text": "Hello! Write one short sentence about AI."
    }

    # --- МАГИЯ ПРОТИВ VPN/PROXY ---
    # Создаем сессию
    session = requests.Session()
    # trust_env = False запрещает библиотеке читать настройки прокси из системы
    # Это заставляет запрос идти напрямую на локальный порт
    session.trust_env = False
    # ------------------------------

    try:
        # Отправляем POST запрос
        response = session.post(API_URL, json=payload, timeout=120)

        # Проверяем статус
        if response.status_code == 200:
            print("\n✅ УСПЕХ! Ответ от сервера:")
            print("-" * 30)
            # Выводим JSON ответ (поле 'response' из app.py)
            print(response.json().get("response", "Нет поля response"))
            print("-" * 30)
        else:
            print(f"\n❌ Ошибка сервера: {response.status_code}")
            print(f"Детали: {response.text}")

    except requests.exceptions.ConnectionError:
        print(f"\n❌ Не удалось подключиться к {API_URL}")
        print("Советы:")
        print("1. Убедись, что app.py запущен.")
        print("2. Убедись, что он слушает порт 8000.")
    except Exception as e:
        print(f"\n❌ Произошла ошибка: {e}")


if __name__ == "__main__":
    test_connection()