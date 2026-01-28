"""Reciprocal Rank Fusion (RRF) for result aggregation"""

from typing import List, Dict
from collections import defaultdict


class RRFAggregator:
    """
    Reciprocal Rank Fusion aggregator for merging search results from multiple queries
    """

    def __init__(self, k: int = 60):
        """
        Initialize RRF aggregator

        Args:
            k: RRF constant (default: 60, standard value from literature)
                Higher k gives more weight to lower ranks
        """
        self.k = k

    def _generate_chunk_id(self, result: Dict) -> str:
        """
        Generate unique identifier for a chunk

        Args:
            result: Result dictionary with metadata

        Returns:
            Unique string identifier for the chunk
        """
        return f"{result['source_file']}:{result['page']}:{result['chunk_index']}"

    def fuse(self, result_sets: List[List[Dict]], top_k: int = 5, min_score: float = 0.0) -> List[Dict]:
        """
        Fuse multiple result sets using Reciprocal Rank Fusion

        RRF Formula: score(d) = Σ 1/(k + rank(d))
        where k is a constant (default 60) and rank is 1-indexed position

        Args:
            result_sets: List of result lists from different query variants
            top_k: Maximum number of final results to return
            min_score: Minimum RRF score threshold (filters weak results)

        Returns:
            Fused and deduplicated results sorted by RRF score (filtered by min_score)
        """
        # Track RRF scores and metadata
        rrf_scores = defaultdict(float)
        chunk_data = {}  # chunk_id -> result dict
        chunk_sources = defaultdict(list)  # chunk_id -> list of contributing variants

        # Calculate RRF scores
        for variant_idx, results in enumerate(result_sets):
            for rank, result in enumerate(results, start=1):
                chunk_id = self._generate_chunk_id(result)

                # RRF formula: score(d) = Σ 1/(k + rank(d))
                rrf_scores[chunk_id] += 1.0 / (self.k + rank)

                # Store result data (use first occurrence)
                if chunk_id not in chunk_data:
                    chunk_data[chunk_id] = result

                # Track which variants contributed to this chunk
                chunk_sources[chunk_id].append({
                    "variant_index": variant_idx,
                    "rank": rank,
                    "original_score": result.get("score", 0.0)
                })

        # Sort by RRF score (highest first)
        sorted_chunks = sorted(
            rrf_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Build final results with enriched metadata
        # Filter by min_score and limit to top_k
        final_results = []
        for chunk_id, rrf_score in sorted_chunks:
            # Stop if we have enough results
            if len(final_results) >= top_k:
                break

            # Skip results below threshold
            if rrf_score < min_score:
                continue

            result = chunk_data[chunk_id].copy()
            result["rrf_score"] = rrf_score
            result["contributing_variants"] = chunk_sources[chunk_id]
            result["num_variants"] = len(chunk_sources[chunk_id])
            final_results.append(result)

        return final_results

    def get_fusion_stats(self, fused_results: List[Dict]) -> Dict:
        """
        Get statistics about fusion results

        Args:
            fused_results: Results from fuse() method

        Returns:
            Dictionary with fusion statistics
        """
        if not fused_results:
            return {"total_results": 0}

        # Count variant contributions
        variant_contributions = defaultdict(int)
        for result in fused_results:
            for contrib in result["contributing_variants"]:
                variant_contributions[contrib["variant_index"]] += 1

        # Average number of variants per result
        avg_variants = sum(r["num_variants"] for r in fused_results) / len(fused_results)

        return {
            "total_results": len(fused_results),
            "avg_variants_per_result": round(avg_variants, 2),
            "variant_contributions": dict(variant_contributions),
            "rrf_score_range": {
                "min": round(min(r["rrf_score"] for r in fused_results), 4),
                "max": round(max(r["rrf_score"] for r in fused_results), 4)
            }
        }
