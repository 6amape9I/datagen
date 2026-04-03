# gemini_generate/gemini_client.py
import json
from typing import Any, Dict, Optional, Tuple, Union

from config import MODEL_NAME
from prompt_builder import build_annotation_request_text
from providers.google_genai_client import request_google_genai_response


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
        sentence_json_string = build_annotation_request_text(sentence_data)
    except (TypeError, AttributeError) as e:
        msg = f"❌ Ошибка при сборке промпта: {e}"
        if return_error:
            return None, msg
        print(msg)
        return None

    try:
        full_response_text = request_google_genai_response(
            sentence_json_string,
            api_key=api_key,
            model_name=MODEL_NAME,
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
