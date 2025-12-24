# gemini_generate/gemini_client.py
import json
from google import genai
from google.genai import types
from typing import Dict, Any, Optional, Tuple, Union

# --- Импорты из config уже корректны, ничего менять не нужно ---
from config import (
    MODEL_NAME,
    SYSTEM_PROMPT,
    BASE_PROMPT,
    ALL_RELATION_NAMES,
    PROMPT_SUFFIX
)


ReturnType = Union[Dict[str, Any], None, Tuple[Optional[Dict[str, Any]], Optional[str]]]


# Функция теперь принимает клиент как аргумент!
def get_model_response(
    client: genai.Client,
    sentence_data: Dict[str, Any],
    *,
    return_error: bool = False,
) -> ReturnType:
    """
    Отправляет данные одного предложения в Gemini API, используя предоставленный
    объект клиента, и возвращает ответ. Потокобезопасна.

    При `return_error=True` возвращает кортеж `(ответ | None, сообщение_об_ошибке | None)`,
    что позволяет вызывающему коду понять причину сбоя.
    """
    #print(sentence_data)

    if not client:
        msg = "❌ Ошибка: в функцию не передан объект клиента."
        if return_error:
            return None, msg
        print(msg)
        return None

    try:
        base = str(BASE_PROMPT or "")
        suffix = str(PROMPT_SUFFIX or "")
        sentence_json_string = json.dumps(sentence_data, ensure_ascii=False, indent=2)
        user_prompt_text = f"{base}{sentence_json_string}{suffix}"
    except (TypeError, AttributeError) as e:
        msg = f"❌ Ошибка при сборке промпта: {e}"
        if return_error:
            return None, msg
        print(msg)
        return None

    contents = [types.Content(role="user", parts=[types.Part.from_text(text=user_prompt_text)])]

    generate_content_config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "nodes": types.Schema(
                    type=types.Type.ARRAY,
                    items=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "id": types.Schema(type=types.Type.STRING),
                            "syntactic_link_name": types.Schema(type=types.Type.STRING, enum=ALL_RELATION_NAMES),
                        },
                        required=["id", "syntactic_link_name"]
                    )
                )
            },
            required=["nodes"]
        ),
        system_instruction=[types.Part.from_text(text=SYSTEM_PROMPT)],
    )

    try:
        full_response_text = ""
        # Используем переданный 'client', а не глобальный
        stream = client.models.generate_content_stream(
            model=f"models/{MODEL_NAME}",
            contents=contents,
            config=generate_content_config,
        )

        for chunk in stream:
            text = str(chunk.text or "")
            full_response_text += text

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
    except Exception as e:
        msg = f"❌ Непредвиденная ошибка во время запроса к API: {e}"
        if return_error:
            return None, msg
        print(msg)
        return None
