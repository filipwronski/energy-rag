"""Cross-encoder reranking for improved result quality"""

from typing import List, Dict, Tuple
from .config import RERANKER_MODEL, RERANKER_DEVICE


class CrossEncoderReranker:
    """
    Cross-encoder reranking using BAAI/bge-reranker-v2-m3
    Scores query-document pairs for better relevance
    """

    def __init__(self, model_name: str = RERANKER_MODEL, device: str = RERANKER_DEVICE):
        """
        Initialize cross-encoder reranker

        Args:
            model_name: Model name (default: BAAI/bge-reranker-v2-m3)
            device: Device to run on ("cpu" or "cuda")
        """
        self.model_name = model_name
        self.device = device
        self._model = None  # Lazy load

    def _load_model(self):
        """Lazy load the cross-encoder model"""
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
                self._model = CrossEncoder(self.model_name, device=self.device)
            except ImportError:
                raise ImportError(
                    "sentence-transformers is required for reranking. "
                    "Install it with: pip install sentence-transformers"
                )

    def rerank(self, query: str, candidates: List[Dict], top_k: int = 20) -> List[Dict]:
        """
        Rerank candidate results using cross-encoder

        Args:
            query: Search query
            candidates: List of candidate result dictionaries with 'text' field
            top_k: Number of top results to return

        Returns:
            Reranked results with added 'ce_score' field
        """
        if not candidates:
            return []

        # Load model if needed
        self._load_model()

        # Prepare query-document pairs
        pairs = [(query, candidate.get('text', '')) for candidate in candidates]

        # Score all pairs
        scores = self._model.predict(pairs)

        # Add scores to candidates
        for candidate, score in zip(candidates, scores):
            candidate['ce_score'] = float(score)

        # Sort by cross-encoder score
        reranked = sorted(candidates, key=lambda x: x.get('ce_score', 0), reverse=True)

        # Return top-K
        return reranked[:top_k]

    def get_model_info(self) -> Dict:
        """
        Get information about the loaded model

        Returns:
            Dictionary with model information
        """
        return {
            "model_name": self.model_name,
            "device": self.device,
            "loaded": self._model is not None
        }


class CohereReranker:
    """
    Alternative reranker using Cohere API
    Useful if you want to avoid local model downloads
    """

    def __init__(self, api_key: str):
        """
        Initialize Cohere reranker

        Args:
            api_key: Cohere API key
        """
        self.api_key = api_key
        self._client = None

    def _load_client(self):
        """Lazy load Cohere client"""
        if self._client is None:
            try:
                import cohere
                self._client = cohere.Client(self.api_key)
            except ImportError:
                raise ImportError(
                    "cohere is required for Cohere reranking. "
                    "Install it with: pip install cohere"
                )

    def rerank(self, query: str, candidates: List[Dict], top_k: int = 20) -> List[Dict]:
        """
        Rerank using Cohere API

        Args:
            query: Search query
            candidates: List of candidate dictionaries
            top_k: Number of results to return

        Returns:
            Reranked results with 'ce_score' field
        """
        if not candidates:
            return []

        self._load_client()

        # Prepare documents
        documents = [candidate.get('text', '') for candidate in candidates]

        # Call Cohere rerank API
        response = self._client.rerank(
            query=query,
            documents=documents,
            top_n=top_k,
            model="rerank-multilingual-v2.0"
        )

        # Map scores back to candidates
        reranked = []
        for result in response.results:
            idx = result.index
            candidate = candidates[idx].copy()
            candidate['ce_score'] = result.relevance_score
            reranked.append(candidate)

        return reranked

    def get_model_info(self) -> Dict:
        """Get reranker info"""
        return {
            "provider": "cohere",
            "model": "rerank-multilingual-v2.0",
            "loaded": self._client is not None
        }
