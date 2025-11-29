"""Ollama API client."""

import requests
from symtrain.config import OLLAMA_API_KEY, OLLAMA_API_URL, OLLAMA_MODEL


def get_headers() -> dict:
    """Get authorization headers for Ollama API."""
    return {
        "Authorization": f"Bearer {OLLAMA_API_KEY}",
        "Content-Type": "application/json",
    }


def chat(prompt: str, model: str = None) -> str:
    """
    Send a chat message to Ollama API.

    Args:
        prompt: The user prompt to send.
        model: Model to use (defaults to config setting).

    Returns:
        The model's response content.

    Raises:
        requests.HTTPError: If the API request fails.
    """
    payload = {
        "model": model or OLLAMA_MODEL,
        "stream": False,
        "messages": [{"role": "user", "content": prompt}],
    }

    response = requests.post(OLLAMA_API_URL, json=payload, headers=get_headers())
    response.raise_for_status()

    return response.json()["message"]["content"].strip()
