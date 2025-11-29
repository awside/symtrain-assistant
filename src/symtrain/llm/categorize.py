"""Transcript categorization using Ollama."""

from symtrain.llm.client import chat


def categorize_with_ollama(transcript: str) -> str:
    """
    Categorize a customer service transcript.

    Args:
        transcript: The transcript text to categorize.

    Returns:
        Category name as a string.
    """
    prompt = f"""Categorize this customer service transcript into one category 
(e.g., Payment Issues, Insurance Claims, Order Status, Returns, Account Issues, etc.):

{transcript[:1000]}

Category must not be empty or Other. Try again if needed.

Return only the category name."""

    return chat(prompt)
