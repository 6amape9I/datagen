# gemini_generate/gemini_client.py
import json
from typing import Any, Dict, Optional, Tuple, Union

import requests

# --- Импорты из config уже корректны, ничего менять не нужно ---
from config import (
    SYSTEM_PROMPT,
    BASE_PROMPT,
    PROMPT_SUFFIX,
    LOCAL_API_URL,
)


ReturnType = Union[Dict[str, Any], None, Tuple[Optional[Dict[str, Any]], Optional[str]]]


# Функция теперь принимает клиент как аргумент!
def get_model_response(
    client: requests.Session,
    sentence_data: Dict[str, Any],
    *,
    return_error: bool = False,
) -> ReturnType:
    """
    Отправляет данные одного предложения в локальный сервис генерации, используя
    предоставленный HTTP-клиент, и возвращает ответ. Потокобезопасна.

    При `return_error=True` возвращает кортеж `(ответ | None, сообщение_об_ошибке | None)`,
    что позволяет вызывающему коду понять причину сбоя.
    """
    #print(sentence_data)

    if not client:
        msg = "❌ Ошибка: в функцию не передан объект HTTP-клиента."
        if return_error:
            return None, msg
        print(msg)
        return None

    try:
        base = str("")
        suffix = str("")
        sentence_json_string = json.dumps(sentence_data, ensure_ascii=False, indent=2)
        user_prompt_text = f"{base}{sentence_json_string}{suffix}"
    except (TypeError, AttributeError) as e:
        msg = f"❌ Ошибка при сборке промпта: {e}"
        if return_error:
            return None, msg
        print(msg)
        return None
    try:
        payload_text = user_prompt_text
        #if SYSTEM_PROMPT:
            #payload_text = f"{SYSTEM_PROMPT}\n\n{user_prompt_text}"

        response = client.post(
            LOCAL_API_URL,
            json={"text": payload_text},
            timeout=120,
        )
        if response.status_code != 200:
            msg = f"❌ Ошибка сервера: {response.status_code}. Детали: {response.text}"
            if return_error:
                return None, msg
            print(msg)
            return None

        try:
            response_json = response.json()
        except ValueError as e:
            msg = f"❌ Ошибка декодирования JSON ответа сервера: {e}. Ответ: {response.text}"
            if return_error:
                return None, msg
            print(msg)
            return None

        full_response_text = str(response_json.get("response", "")).strip()

        if not full_response_text:
            msg = "  - 🟡 Ответ от API пустой."
            if return_error:
                return None, msg
            print(msg)
            return None

        parsed = json.loads(full_response_text)
        if return_error:
            return parsed, None
        return parsed

    except json.JSONDecodeError:
        msg = f"❌ Ошибка декодирования JSON. Ответ от API:\n{full_response_text}"
        if return_error:
            return None, msg
        print(msg)
        return None
    except requests.RequestException as e:
        msg = f"❌ Ошибка при запросе к локальному API: {e}"
        if return_error:
            return None, msg
        print(msg)
        return None
    except Exception as e:
        msg = f"❌ Непредвиденная ошибка во время запроса к API: {e}"
        if return_error:
            return None, msg
        print(msg)
        return None
