"""Polish text embedding using sdadas/mmlw-retrieval-roberta-base"""

from sentence_transformers import SentenceTransformer
from .config import EMBEDDING_MODEL


class PolishEmbedder:
    """Wrapper for Polish embedding model"""

    def __init__(self):
        """Initialize the embedding model"""
        print(f"Loading embedding model: {EMBEDDING_MODEL}")
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        print("✓ Model loaded")

    def embed(self, text: str):
        """
        Generate embedding for a single text

        Args:
            text: Input text to embed

        Returns:
            List of floats representing the embedding vector
        """
        return self.model.encode(text, normalize_embeddings=True).tolist()

    def embed_batch(self, texts: list):
        """
        Generate embeddings for multiple texts

        Args:
            texts: List of input texts to embed

        Returns:
            List of embedding vectors
        """
        return self.model.encode(texts, normalize_embeddings=True).tolist()
