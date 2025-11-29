"""Similarity search using embeddings."""

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from symtrain.embeddings import get_embedding


def find_similar(
    df: pd.DataFrame,
    embedding_column: str,
    query: str,
    top_k: int = 5,
) -> pd.DataFrame:
    """
    Find the most similar simulations to a query.

    Args:
        query: Text query to search for.
        df: DataFrame containing embeddings.
        embedding_column: Name of the column containing embeddings.
        top_k: Number of results to return.

    Returns:
        DataFrame with top matching simulations and their similarity scores.
    """
    query_emb = get_embedding(query).reshape(1, -1)
    embeddings_matrix = np.vstack(df[embedding_column].values)

    similarities = cosine_similarity(query_emb, embeddings_matrix)[0]
    top_indices = similarities.argsort()[::-1][:top_k]

    results = df.iloc[top_indices][["name"]].copy()
    results["similarity"] = similarities[top_indices]
    return results
