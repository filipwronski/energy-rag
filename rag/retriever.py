"""Search and retrieval logic for protocol documents"""

from qdrant_client import QdrantClient
from .embedder import PolishEmbedder
from .config import QDRANT_URL, COLLECTION_NAME, MIN_SCORE_THRESHOLD


class ProtocolRetriever:
    """Retriever for searching protocol documents in Qdrant"""

    def __init__(self):
        """Initialize the retriever with Qdrant client and embedder"""
        self.client = QdrantClient(url=QDRANT_URL)
        self.embedder = PolishEmbedder()

    def search(self, query: str, top_k: int = 5):
        """
        Search for relevant document chunks

        Args:
            query: Search query text
            top_k: Number of top results to return

        Returns:
            List of dictionaries with search results
        """
        # 1. Embed query
        query_vector = self.embedder.embed(query)

        # 2. Search Qdrant
        results = self.client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=top_k
        ).points

        # 3. Format results
        formatted = []
        for hit in results:
            # Filter by score threshold
            if hit.score < MIN_SCORE_THRESHOLD:
                continue

            formatted.append({
                "text": hit.payload["text"],
                "source": hit.payload["source_title"],
                "source_file": hit.payload["source_file"],
                "page": hit.payload["page_number"],
                "score": hit.score,
                "protocol_number": hit.payload["protocol_number"],
                "date_range": hit.payload["date_range"],
                "chunk_index": hit.payload["chunk_index"],
                "total_chunks": hit.payload["total_chunks"]
            })

        return formatted
