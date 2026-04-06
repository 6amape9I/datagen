"""
Optional private overrides for local development.

Copy this file to `config/generate_conf.py` if you want file-based local overrides.
Environment variables take precedence over everything in this file.
"""

MODEL_NAME = "gemini-flash-latest"
LOCAL_API_URL = "http://127.0.0.1:8080/generate"
LOCAL_INFER_URL = "http://127.0.0.1:8000/infer"
API_KEYS_STR = ""
ALL_KEYS_FOR_SHEDULE = ""
