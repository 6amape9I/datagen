# gemini_generate/gemini_client.py
import json
from google import genai
from google.genai import types
from typing import Dict, Any

# --- Импорты из config уже корректны, ничего менять не нужно ---
from config import (
    MODEL_NAME,
    SYSTEM_PROMPT,
    BASE_PROMPT,
    ALL_RELATION_NAMES,
    PROMPT_SUFFIX
)


# Функция теперь принимает клиент как аргумент!
def get_model_response(client: genai.Client, sentence_data: Dict[str, Any]) -> Dict[str, Any] | None:
    """
    Отправляет данные одного предложения в Gemini API, используя предоставленный
    объект клиента, и возвращает ответ. Потокобезопасна.
    """
    #print(sentence_data)

    if not client:
        print("❌ Ошибка: в функцию не передан объект клиента.")
        return None

    try:
        base = str(BASE_PROMPT or "")
        suffix = str(PROMPT_SUFFIX or "")
        sentence_json_string = json.dumps(sentence_data, ensure_ascii=False, indent=2)
        user_prompt_text = f"{base}{sentence_json_string}{suffix}"
    except (TypeError, AttributeError) as e:
        print(f"❌ Ошибка при сборке промпта: {e}")
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
            print("  - 🟡 Ответ от API пустой.")
            return None

        return json.loads(full_response_text)

    except json.JSONDecodeError:
        print(f"❌ Ошибка декодирования JSON. Ответ от API:\n{full_response_text}")
        return None
    except Exception as e:
        print(f"❌ Непредвиденная ошибка во время запроса к API: {e}")
        return None