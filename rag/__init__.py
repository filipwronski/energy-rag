"""RAG system for Polish protocol documents"""

from .config import (
    QDRANT_URL,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    EMBEDDING_DIM,
    MAX_CHUNK_SIZE,
    CHUNK_OVERLAP,
    DEFAULT_TOP_K,
    MIN_SCORE_THRESHOLD,
    OUTPUT_DIR,
)

__all__ = [
    "QDRANT_URL",
    "COLLECTION_NAME",
    "EMBEDDING_MODEL",
    "EMBEDDING_DIM",
    "MAX_CHUNK_SIZE",
    "CHUNK_OVERLAP",
    "DEFAULT_TOP_K",
    "MIN_SCORE_THRESHOLD",
    "OUTPUT_DIR",
]
