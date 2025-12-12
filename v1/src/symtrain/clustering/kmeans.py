"""K-Means clustering on embeddings."""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans


def cluster_embeddings(
    df: pd.DataFrame,
    embedding_column: str,
    n_clusters: int = 5,
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Cluster transcripts based on their embeddings.

    Args:
        df: DataFrame containing embeddings.
        embedding_column: Name of the column containing embeddings.
        n_clusters: Number of clusters to create.
        random_state: Random seed for reproducibility.

    Returns:
        DataFrame with new 'cluster' column.
    """
    df = df.copy()
    embeddings_matrix = np.vstack(df[embedding_column].values)

    kmeans = KMeans(n_clusters=n_clusters, n_init="auto", random_state=random_state)
    df[f"{embedding_column}_cluster"] = kmeans.fit_predict(embeddings_matrix)

    return df


def print_cluster_summary(
    df: pd.DataFrame,
    name_column,
    cluster_column,
    max_per_cluster: int = 3,
) -> None:
    """
    Print a summary of clusters.

    Args:
        df: DataFrame with cluster and name columns.
        name_column: Name of the column containing item names.
        cluster_column: Name of the column containing cluster assignments.
        max_per_cluster: Maximum number of items to show per cluster.
    """
    if cluster_column not in df.columns:
        print(f"No '{cluster_column}' column found. Run cluster_embeddings() first.")
        return

    n_clusters = df[cluster_column].nunique()

    for cluster_id in range(n_clusters):
        print(f"\n=== Cluster {cluster_id} ===")
        cluster_sims = df[df[cluster_column] == cluster_id][name_column].tolist()
        for name in cluster_sims[:max_per_cluster]:
            print(f"  - {name}")
