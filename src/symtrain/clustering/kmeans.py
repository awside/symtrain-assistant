"""K-Means clustering on embeddings."""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans


def cluster_embeddings(
    df: pd.DataFrame, n_clusters: int = 5, random_state: int = 42
) -> pd.DataFrame:
    """
    Cluster transcripts based on their embeddings.

    Args:
        df: DataFrame with 'embedding' column.
        n_clusters: Number of clusters to create.
        random_state: Random seed for reproducibility.

    Returns:
        DataFrame with new 'cluster' column.
    """
    df = df.copy()
    embeddings_matrix = np.vstack(df["embedding"].values)

    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state)
    df["cluster"] = kmeans.fit_predict(embeddings_matrix)

    return df


def print_cluster_summary(df: pd.DataFrame, max_per_cluster: int = 3) -> None:
    """
    Print a summary of clusters.

    Args:
        df: DataFrame with 'cluster' and 'name' columns.
        max_per_cluster: Maximum number of items to show per cluster.
    """
    if "cluster" not in df.columns:
        print("No 'cluster' column found. Run cluster_embeddings() first.")
        return

    n_clusters = df["cluster"].nunique()

    for cluster_id in range(n_clusters):
        print(f"\n=== Cluster {cluster_id} ===")
        cluster_sims = df[df["cluster"] == cluster_id]["name"].tolist()
        for name in cluster_sims[:max_per_cluster]:
            print(f"  - {name}")
