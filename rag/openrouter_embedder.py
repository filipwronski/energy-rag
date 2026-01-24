"""OpenRouter-based embedder with caching support"""

from typing import List
from .openrouter_client import OpenRouterClient
from .cache import EmbeddingCache


class OpenRouterEmbedder:
    """
    Embedder using OpenRouter API with optional caching
    """

    def __init__(self, use_cache: bool = True, cache_path: str = "embedding_cache.db"):
        """
        Initialize OpenRouter embedder

        Args:
            use_cache: Enable embedding cache to reduce API costs
            cache_path: Path to SQLite cache database
        """
        self.client = OpenRouterClient()
        self.use_cache = use_cache

        if use_cache:
            self.cache = EmbeddingCache(cache_path)
        else:
            self.cache = None

        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "api_calls": 0
        }

    def embed(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Input text to embed

        Returns:
            1536-dimensional embedding vector
        """
        # Check cache first
        if self.cache:
            cached = self.cache.get(text)
            if cached is not None:
                self.stats["cache_hits"] += 1
                return cached
            self.stats["cache_misses"] += 1

        # Call API if not in cache
        embedding = self.client.get_embedding(text)
        self.stats["api_calls"] += 1

        # Store in cache
        if self.cache:
            self.cache.put(text, embedding)

        return embedding

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts with cache optimization

        Args:
            texts: List of input texts to embed

        Returns:
            List of 1536-dimensional embedding vectors
        """
        results = [None] * len(texts)
        uncached_indices = []
        uncached_texts = []

        # Check cache for each text
        for i, text in enumerate(texts):
            if self.cache:
                cached = self.cache.get(text)
                if cached is not None:
                    results[i] = cached
                    self.stats["cache_hits"] += 1
                else:
                    uncached_indices.append(i)
                    uncached_texts.append(text)
                    self.stats["cache_misses"] += 1
            else:
                uncached_indices.append(i)
                uncached_texts.append(text)

        # Fetch uncached embeddings from API
        if uncached_texts:
            new_embeddings = self.client.get_embeddings_batch(uncached_texts)
            self.stats["api_calls"] += len(uncached_texts)

            # Store in cache and results
            for i, embedding in zip(uncached_indices, new_embeddings):
                results[i] = embedding
                if self.cache:
                    self.cache.put(texts[i], embedding)

        return results

    def get_stats(self) -> dict:
        """
        Get cache and API usage statistics

        Returns:
            Dictionary with statistics including cache hit rate
        """
        total_requests = self.stats["cache_hits"] + self.stats["cache_misses"]
        hit_rate = (self.stats["cache_hits"] / total_requests * 100) if total_requests > 0 else 0

        return {
            **self.stats,
            "total_requests": total_requests,
            "cache_hit_rate": f"{hit_rate:.1f}%"
        }
