from __future__ import annotations

import os


NUM_WORKERS = int(os.environ.get("GENAI_NUM_WORKERS", "8"))

MAX_RETRIES = int(os.environ.get("GENAI_MAX_RETRIES", "4"))
INITIAL_BACKOFF_DELAY = int(os.environ.get("GENAI_INITIAL_BACKOFF_DELAY", "8"))

SCHEDULER_MAX_CONCURRENT_WORKERS = int(os.environ.get("SCHEDULER_WORKERS", "4"))
SCHEDULER_CONSECUTIVE_ERROR_LIMIT = int(os.environ.get("SCHEDULER_ERROR_LIMIT", "10"))
SCHEDULER_DAILY_QUOTA = int(os.environ.get("SCHEDULER_DAILY_QUOTA", "250"))
