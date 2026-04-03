# gemini_generate/local_client.py
import json
from typing import Any, Dict, Optional, Tuple, Union

import requests

from prompt_builder import build_annotation_request_text
from providers.local_http_client import request_local_http_response


ReturnType = Union[Dict[str, Any], None, Tuple[Optional[Dict[str, Any]], Optional[str]]]


def get_local_model_response(
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
    if not client:
        msg = "❌ Ошибка: в функцию не передан объект HTTP-клиента."
        if return_error:
            return None, msg
        print(msg)
        return None

    try:
        user_prompt_text = build_annotation_request_text(sentence_data)
    except (TypeError, AttributeError) as e:
        msg = f"❌ Ошибка при сборке промпта: {e}"
        if return_error:
            return None, msg
        print(msg)
        return None
    return request_local_http_response(client, user_prompt_text, return_error=return_error)
