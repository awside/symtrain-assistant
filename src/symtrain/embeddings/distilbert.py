"""DistilBERT embedding generation."""

import numpy as np
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModel

from symtrain.config import EMBEDDING_MODEL, MAX_TOKEN_LENGTH

# Load model and tokenizer (cached at module level)
_tokenizer = None
_model = None


def _get_model():
    """Lazy load the model and tokenizer."""
    global _tokenizer, _model
    if _tokenizer is None:
        _tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL)
        _model = AutoModel.from_pretrained(EMBEDDING_MODEL)
    return _tokenizer, _model


def get_embedding(text: str) -> np.ndarray:
    """
    Generate embedding for a text using DistilBERT.

    Args:
        text: Input text to embed.

    Returns:
        Numpy array of shape (768,) representing the embedding.
    """
    tokenizer, model = _get_model()

    inputs = tokenizer(
        text, return_tensors="pt", truncation=True, max_length=MAX_TOKEN_LENGTH
    )

    with torch.no_grad():
        outputs = model(**inputs)

    # Mean pooling
    return outputs.last_hidden_state.mean(dim=1).numpy()[0]


def embed_dataframe(df: pd.DataFrame, text_column: str = "transcript") -> pd.DataFrame:
    """
    Add embeddings to a DataFrame.

    Args:
        df: DataFrame containing text data.
        text_column: Name of the column containing text to embed.

    Returns:
        DataFrame with new 'embedding' column.
    """
    df = df.copy()
    df["embedding"] = df[text_column].apply(get_embedding)
    print(f"Generated {len(df)} embeddings of dimension {len(df['embedding'].iloc[0])}")
    return df
