"""Compatibility exports for legacy 03_annotation provider imports."""

from .google_genai_client import GoogleGenAIProvider
from .local_http_client import LocalHTTPProvider

__all__ = ["GoogleGenAIProvider", "LocalHTTPProvider"]
