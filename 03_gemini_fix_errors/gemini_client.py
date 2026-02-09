# gemini_generate/gemini_client.py
import json
from typing import Any, Dict, Optional, Tuple, Union

from genai_example import generate


ReturnType = Union[Dict[str, Any], None, Tuple[Optional[Dict[str, Any]], Optional[str]]]


def get_model_response(
    api_key: str,
    sentence_data: Dict[str, Any],
    *,
    return_error: bool = False,
) -> ReturnType:
    """
    Отправляет данные одного предложения в Google GenAI через функцию generate()
    из genai_example.py и возвращает ответ.

    При `return_error=True` возвращает кортеж `(ответ | None, сообщение_об_ошибке | None)`,
    что позволяет вызывающему коду понять причину сбоя.
    """
    if not api_key:
        msg = "❌ Ошибка: не передан API ключ для GenAI."
        if return_error:
            return None, msg
        print(msg)
        return None

    try:
        sentence_json_string = json.dumps(sentence_data, ensure_ascii=False, indent=2)
    except (TypeError, AttributeError) as e:
        msg = f"❌ Ошибка при сборке промпта: {e}"
        if return_error:
            return None, msg
        print(msg)
        return None

    try:
        full_response_text = generate(
            sentence_json_string,
            api_key=api_key,
            return_text=True,
        )

        if not full_response_text:
            msg = "  - 🟡 Ответ от GenAI пустой."
            if return_error:
                return None, msg
            print(msg)
            return None

        parsed = json.loads(full_response_text)
        if return_error:
            return parsed, None
        return parsed

    except json.JSONDecodeError:
        msg = f"❌ Ошибка декодирования JSON. Ответ от GenAI:\n{full_response_text}"
        if return_error:
            return None, msg
        print(msg)
        return None
    except Exception as e:
        msg = f"❌ Непредвиденная ошибка во время запроса к GenAI: {e}"
        if return_error:
            return None, msg
        print(msg)
        return None
