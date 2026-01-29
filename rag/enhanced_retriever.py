"""Enhanced retriever with query expansion and RRF aggregation"""

from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from .openrouter_embedder import OpenRouterEmbedder
from .openrouter_client import OpenRouterClient
from .query_expander import QueryExpander
from .rrf_aggregator import RRFAggregator
from .reranker import CrossEncoderReranker
from .config import (
    QDRANT_URL, COLLECTION_NAME,
    NUM_QUERY_VARIANTS, RESULTS_PER_VARIANT,
    DEFAULT_TOP_K, RRF_K, MIN_RRF_SCORE,
    ENABLE_CACHE, CACHE_DB_PATH,
    ENABLE_RERANKING, RERANKING_CANDIDATES
)


class EnhancedProtocolRetriever:
    """
    Enhanced retriever with query expansion and RRF aggregation
    """

    def __init__(self):
        """Initialize enhanced retriever with all components"""
        self.client = QdrantClient(url=QDRANT_URL)
        self.embedder = OpenRouterEmbedder(use_cache=ENABLE_CACHE, cache_path=CACHE_DB_PATH)
        self.openrouter_client = OpenRouterClient()
        self.query_expander = QueryExpander(self.openrouter_client)
        self.rrf_aggregator = RRFAggregator(k=RRF_K)

        # Initialize reranker if enabled
        self.reranker: Optional[CrossEncoderReranker] = None
        if ENABLE_RERANKING:
            try:
                self.reranker = CrossEncoderReranker()
            except Exception as e:
                print(f"Warning: Failed to initialize reranker: {e}")
                print("Reranking will be disabled.")

        self.stats = {
            "queries_processed": 0,
            "total_variants_generated": 0,
            "total_api_calls": 0
        }

    def _search_single_variant(self, variant_text: str, top_k: int) -> List[Dict]:
        """
        Search for a single query variant

        Args:
            variant_text: Query variant text
            top_k: Number of results to retrieve

        Returns:
            List of search results with metadata
        """
        # Embed query variant
        query_vector = self.embedder.embed(variant_text)

        # Search Qdrant
        results = self.client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=top_k
        ).points

        # Format results
        formatted = []
        for hit in results:
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

    def search(self, query: str,
               top_k: int = DEFAULT_TOP_K,
               num_variants: int = NUM_QUERY_VARIANTS,
               results_per_variant: int = RESULTS_PER_VARIANT,
               min_rrf_score: float = MIN_RRF_SCORE,
               verbose: bool = False) -> Dict:
        """
        Enhanced search with query expansion and RRF

        Args:
            query: Original search query
            top_k: Maximum number of final results to return after RRF
            num_variants: Number of query variants to generate
            results_per_variant: Number of results to fetch per variant
            min_rrf_score: Minimum RRF score threshold (filters weak results)
            verbose: Print detailed progress information

        Returns:
            Dictionary with results and metadata:
            {
                "results": [...],  # Top K fused results (filtered by min_rrf_score)
                "query": str,  # Original query
                "variants": [...],  # Generated variants with methods
                "fusion_stats": {...},  # RRF fusion statistics
                "cache_stats": {...}  # Embedding cache statistics
            }
        """
        return self._dense_search(query, top_k, num_variants, results_per_variant, min_rrf_score, verbose)

    def _dense_search(self, query: str,
                     top_k: int,
                     num_variants: int,
                     results_per_variant: int,
                     min_rrf_score: float,
                     verbose: bool) -> Dict:
        """Dense vector search with query expansion and reranking"""
        if verbose:
            print(f"\n🔍 Processing query: \"{query}\"")
            print(f"   Generating {num_variants} query variants...")

        # 1. Generate query variants
        variants = self.query_expander.expand_hybrid(query, num_variants=num_variants)

        if verbose:
            print(f"   Query variants:")
            for i, variant in enumerate(variants, 1):
                print(f"      {i}. [{variant['method']}] {variant['text']}")

        # 2. Search for each variant
        if verbose:
            print(f"\n   Searching Qdrant ({results_per_variant} results per variant)...")

        all_results = []
        for i, variant in enumerate(variants):
            results = self._search_single_variant(variant["text"], results_per_variant)
            all_results.append(results)

            if verbose:
                print(f"      Variant {i+1}: {len(results)} results")

        # 3. Apply RRF aggregation
        if verbose:
            print(f"\n   Applying Reciprocal Rank Fusion...")
            print(f"      Min RRF score threshold: {min_rrf_score}")

        fused_results = self.rrf_aggregator.fuse(all_results, top_k=top_k, min_score=min_rrf_score)

        if verbose:
            print(f"      ✓ Fused to {len(fused_results)} final results (filtered by quality)")
            fusion_stats = self.rrf_aggregator.get_fusion_stats(fused_results)
            print(f"      Avg variants per result: {fusion_stats['avg_variants_per_result']}")

        # 4. Apply reranking if enabled
        if ENABLE_RERANKING and self.reranker and fused_results:
            if verbose:
                print(f"\n   Applying cross-encoder reranking...")

            # Get more candidates for reranking
            candidates = fused_results[:RERANKING_CANDIDATES]
            fused_results = self.reranker.rerank(query, candidates, top_k=top_k)

            if verbose:
                print(f"      ✓ Reranked to top {len(fused_results)} results")

        # 5. Update stats
        self.stats["queries_processed"] += 1
        self.stats["total_variants_generated"] += len(variants)

        # 6. Return results with metadata
        return {
            "results": fused_results,
            "query": query,
            "variants": variants,
            "fusion_stats": self.rrf_aggregator.get_fusion_stats(fused_results),
            "cache_stats": self.embedder.get_stats()
        }

    def get_stats(self) -> Dict:
        """
        Get retriever statistics

        Returns:
            Dictionary with query and cache statistics
        """
        return {
            **self.stats,
            "embedder_stats": self.embedder.get_stats()
        }
