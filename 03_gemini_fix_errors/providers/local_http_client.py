from __future__ import annotations

import json
from typing import Any, Dict, Optional, Tuple, Union

import requests

from config import LOCAL_API_URL


ReturnType = Union[Dict[str, Any], None, Tuple[Optional[Dict[str, Any]], Optional[str]]]


def request_local_http_response(
    client: requests.Session,
    prompt_text: str,
    *,
    return_error: bool = False,
) -> ReturnType:
    if not client:
        msg = "❌ Ошибка: в функцию не передан объект HTTP-клиента."
        if return_error:
            return None, msg
        print(msg)
        return None

    try:
        response = client.post(
            LOCAL_API_URL,
            json={"text": prompt_text},
            timeout=12000,
        )
        if response.status_code != 200:
            msg = f"❌ Ошибка сервера: {response.status_code}. Детали: {response.text}"
            if return_error:
                return None, msg
            print(msg)
            return None

        try:
            response_json = response.json()
        except ValueError as exc:
            msg = f"❌ Ошибка декодирования JSON ответа сервера: {exc}. Ответ: {response.text}"
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
    except requests.RequestException as exc:
        msg = f"❌ Ошибка при запросе к локальному API: {exc}"
        if return_error:
            return None, msg
        print(msg)
        return None
    except Exception as exc:
        msg = f"❌ Непредвиденная ошибка во время запроса к API: {exc}"
        if return_error:
            return None, msg
        print(msg)
        return None
