"""Example client that sends a local inference request.

Run a compatible local inference server first (it should expose POST /infer on 127.0.0.1:8000).

Then run:
  python 02_local_generation/request_example.py "Ваше предложение"
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from http.client import RemoteDisconnected
from typing import Any, Dict

# --- proxy safety: never proxy localhost ---
import urllib.request

_proxy_handler = urllib.request.ProxyHandler({})
_opener = urllib.request.build_opener(_proxy_handler)
urllib.request.install_opener(_opener)
# ------------------------------------------


SERVER_URL = "http://127.0.0.1:8000/infer"


def request_inference(text: str, *, retries: int = 3, backoff_sec: float = 1.0) -> Dict[str, Any]:
    payload = json.dumps({"text": text}, ensure_ascii=False).encode("utf-8")
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        req = urllib.request.Request(
            SERVER_URL,
            data=payload,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                body = resp.read().decode("utf-8")
            return json.loads(body)
        except RemoteDisconnected as exc:
            last_error = exc
        except urllib.error.URLError as exc:
            last_error = exc

        if attempt < retries:
            time.sleep(backoff_sec * attempt)

    assert last_error is not None
    raise last_error


def main() -> int:
    text = " ".join(sys.argv[1:]).strip() or "В четверг четвёртого числа четыре чёрненьких чертёнка чертили чёрный квадрат."
    try:
        result = request_inference(text)
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP error: {exc.code} {exc.reason}\n{error_body}")
        return 1
    except urllib.error.URLError as exc:
        print(f"Connection error: {exc}")
        return 2
    except RemoteDisconnected as exc:
        print(f"Server disconnected without response: {exc}")
        return 3

    # This is inference_result["json"].
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
