"""
Optional private overrides for local development.

Copy this file to `config/generate_conf.py` if you want file-based local overrides.
Environment variables take precedence over everything in this file.
"""

GOOGLE_MODEL_NAME = "gemma-4-31b-it"
LOCAL_MODEL_NAME = "local_http"
LOCAL_API_URL = "http://127.0.0.1:8080/generate"
GOOGLE_API_KEYS_STR = ""
GOOGLE_SCHEDULER_KEYS_STR = ""
GOOGLE_THINKING_LEVEL = "HIGH"
GOOGLE_ENABLE_SEARCH_TOOL = False
MAX_OUTPUT_TOKENS = 32760
TEMPERATURE = 0.0
GENERATION_PROFILE = "standard"
