"""Configuration settings for SymTrain."""

import os

# Ollama API settings
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "https://ollama.com/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud")

# Embedding model settings
EMBEDDING_MODEL = "distilbert-base-uncased"
MAX_TOKEN_LENGTH = 512
