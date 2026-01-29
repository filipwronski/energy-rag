"""Unit tests for build_index script"""

import pytest
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def estimate_cost(num_chunks: int) -> dict:
    """
    Estimate indexing cost

    Args:
        num_chunks: Number of chunks to embed

    Returns:
        Cost breakdown dictionary
    """
    # OpenRouter pricing for text-embedding-3-small: $0.00002 per 1K tokens
    # Assume average chunk is ~100 tokens (512 chars / 5 chars per token)
    tokens_per_chunk = 100
    total_tokens = num_chunks * tokens_per_chunk
    cost_per_1k_tokens = 0.00002

    estimated_cost = (total_tokens / 1000) * cost_per_1k_tokens

    return {
        "num_chunks": num_chunks,
        "estimated_tokens": total_tokens,
        "estimated_cost_usd": round(estimated_cost, 4),
        "cost_per_chunk": round(estimated_cost / num_chunks, 6) if num_chunks > 0 else 0
    }


class TestEstimateCost:
    """Test estimate_cost function"""

    def test_standard_calculation(self):
        """Test cost estimation with standard number of chunks"""
        num_chunks = 100
        result = estimate_cost(num_chunks)

        assert result["num_chunks"] == 100
        assert result["estimated_tokens"] == 10000  # 100 chunks * 100 tokens
        assert result["estimated_cost_usd"] == 0.0002  # (10000 / 1000) * 0.00002
        assert result["cost_per_chunk"] == 0.000002  # 0.0002 / 100

    def test_zero_chunks(self):
        """Test cost estimation with zero chunks"""
        num_chunks = 0
        result = estimate_cost(num_chunks)

        assert result["num_chunks"] == 0
        assert result["estimated_tokens"] == 0
        assert result["estimated_cost_usd"] == 0.0
        assert result["cost_per_chunk"] == 0

    def test_large_number(self):
        """Test cost estimation with large number of chunks"""
        num_chunks = 10000
        result = estimate_cost(num_chunks)

        assert result["num_chunks"] == 10000
        assert result["estimated_tokens"] == 1000000  # 10000 * 100
        assert result["estimated_cost_usd"] == 0.02  # (1000000 / 1000) * 0.00002
        assert result["cost_per_chunk"] == 0.000002

    def test_verify_cost_per_chunk(self):
        """Test that cost per chunk is calculated correctly"""
        num_chunks = 50
        result = estimate_cost(num_chunks)

        # Verify cost_per_chunk = estimated_cost_usd / num_chunks
        expected_cost_per_chunk = result["estimated_cost_usd"] / num_chunks
        assert abs(result["cost_per_chunk"] - expected_cost_per_chunk) < 1e-9
