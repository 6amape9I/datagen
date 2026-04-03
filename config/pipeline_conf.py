# config/pipeline_conf.py
import os
from .generate_conf import API_KEYS_STR, ALL_KEYS_FOR_SHEDULE

# --- Настройки API ---
# Позволяет переопределить ключи через переменную окружения
_API_KEYS_FINAL_STR = os.environ.get("GEMINI_API_KEYS", API_KEYS_STR)
API_KEYS = _API_KEYS_FINAL_STR.split(',') if _API_KEYS_FINAL_STR else []
ALL_SCHEDULER_KEYS = [key.strip() for key in ALL_KEYS_FOR_SHEDULE.split(',') if key.strip()]

# --- Настройки клиента ---
# Возможные значения: "local" (локальный сервис), "genai" (google-genai)
REQUEST_STRATEGY = os.environ.get("GEMINI_REQUEST_STRATEGY", "genai").strip().lower()

# --- Настройки воркеров ---
# Фиксированное число воркеров, не зависящее от количества ключей
NUM_WORKERS = 8

# --- Настройки повторных запросов (retry) ---
MAX_RETRIES = 4             # Максимальное количество попыток для одного запроса
INITIAL_BACKOFF_DELAY = 8   # Начальная задержка в секундах перед повтором

# --- Настройки шедулера ---
SCHEDULER_MAX_CONCURRENT_WORKERS = int(os.environ.get("SCHEDULER_WORKERS", "4"))
SCHEDULER_CONSECUTIVE_ERROR_LIMIT = int(os.environ.get("SCHEDULER_ERROR_LIMIT", "10"))
SCHEDULER_DAILY_QUOTA = int(os.environ.get("SCHEDULER_DAILY_QUOTA", "250"))
