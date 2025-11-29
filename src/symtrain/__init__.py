"""SymTrain - Customer service transcript analysis with embeddings and LLM."""

from symtrain.data import load_json_files, create_transcript_dataframe
from symtrain.embeddings import get_embedding, embed_dataframe_column
from symtrain.search import find_similar
from symtrain.clustering import cluster_embeddings
from symtrain.llm import categorize_with_ollama, generate_steps_with_ollama

__version__ = "0.1.0"

__all__ = [
    "load_json_files",
    "create_transcript_dataframe",
    "get_embedding",
    "embed_dataframe_column",
    "find_similar",
    "cluster_embeddings",
    "categorize_with_ollama",
    "generate_steps_with_ollama",
]
