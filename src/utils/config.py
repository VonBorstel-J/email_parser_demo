# src/utils/config.py

import os

class Config:
    """Configuration settings."""

    # Local LLM Configuration
    LOCAL_LLM_API_ENDPOINT = os.getenv('LOCAL_LLM_API_ENDPOINT')
