"""Few-shot learning pipeline for generating customer service steps."""

import json
import pandas as pd

from symtrain.search import find_similar
from symtrain.llm.client import chat


def get_few_shot_examples(
    query: str,
    df: pd.DataFrame,
    embedding_column: str = "transcript_emb",
    n_examples: int = 2,
) -> list[dict]:
    """
    Find similar transcripts to use as few-shot examples.

    Args:
        query: The customer query to find examples for.
        df: DataFrame with embeddings.
        embedding_column: Name of the column containing embeddings.
        n_examples: Number of examples to retrieve.

    Returns:
        List of dicts with 'name' and 'transcript' keys.
    """
    similar = find_similar(df, embedding_column, query, top_k=n_examples)

    examples = []
    for idx in similar.index:
        examples.append(
            {
                "name": df.loc[idx, "name"],
                "transcript": df.loc[idx, "transcript"][:500],  # Truncate for prompt
            }
        )
    return examples


def generate_steps_with_ollama(query: str, df: pd.DataFrame) -> dict:
    """
    Use few-shot learning to generate steps for handling a customer query.

    Args:
        query: The customer query to handle.
        df: DataFrame with embeddings for finding similar examples.

    Returns:
        Dict with 'category', 'reason', and 'steps' keys.
    """
    # Get similar examples from dataset
    examples = get_few_shot_examples(query, df, n_examples=2)

    # Build few-shot prompt
    examples_text = ""
    for i, ex in enumerate(examples, 1):
        examples_text += f"\n--- Example {i}: {ex['name']} ---\n{ex['transcript']}\n"

    prompt = f"""You are a customer service training assistant. Based on the examples below, 
analyze the customer query and generate appropriate handling steps.

{examples_text}

--- New Customer Query ---
{query}

Respond with JSON only in this exact format:
{{
    "category": "the category of this query (e.g., Payment Issues, Insurance Claims, Order Status)",
    "reason": "brief explanation of why this category was chosen",
    "steps": ["step 1", "step 2", "step 3", ...]
}}"""

    content = chat(prompt)

    # Parse JSON from response - extract first JSON object only
    try:
        # Find the first { and match its closing }
        start = content.find("{")
        if start == -1:
            return {"raw_response": content, "error": "No JSON found"}

        # Count braces to find matching closing brace
        depth = 0
        for i, char in enumerate(content[start:], start):
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    json_str = content[start : i + 1]
                    return json.loads(json_str)

        return {"raw_response": content, "error": "Unmatched braces"}
    except json.JSONDecodeError:
        return {"raw_response": content, "error": "Failed to parse JSON"}
