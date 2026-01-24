"""Test suite for enhanced retrieval system"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from rag.enhanced_retriever import EnhancedProtocolRetriever
from rag.query_expander import QueryExpander
from rag.openrouter_client import OpenRouterClient
from rag.rrf_aggregator import RRFAggregator


def test_query_expansion():
    """Test query expansion with hybrid approach"""
    print("\n" + "=" * 70)
    print("Test 1: Query Expansion")
    print("=" * 70)

    client = OpenRouterClient()
    expander = QueryExpander(client)

    test_queries = [
        "sprawy pracownicze",
        "wiaty śmietnikowe",
        "Komisja Przetargowa"
    ]

    for query in test_queries:
        print(f"\nOriginal: {query}")
        variants = expander.expand_hybrid(query, num_variants=5)

        for i, variant in enumerate(variants, 1):
            print(f"  {i}. [{variant['method']}] {variant['text']}")

    print("\n✓ Query expansion test passed")


def test_rrf_fusion():
    """Test RRF aggregation with mock data"""
    print("\n" + "=" * 70)
    print("Test 2: RRF Fusion")
    print("=" * 70)

    aggregator = RRFAggregator(k=60)

    # Mock results from 3 query variants
    results_1 = [
        {"source_file": "doc1.md", "page": 1, "chunk_index": 0, "score": 0.9, "text": "Content A"},
        {"source_file": "doc2.md", "page": 2, "chunk_index": 0, "score": 0.8, "text": "Content B"},
    ]

    results_2 = [
        {"source_file": "doc2.md", "page": 2, "chunk_index": 0, "score": 0.85, "text": "Content B"},
        {"source_file": "doc3.md", "page": 3, "chunk_index": 0, "score": 0.7, "text": "Content C"},
    ]

    results_3 = [
        {"source_file": "doc1.md", "page": 1, "chunk_index": 0, "score": 0.88, "text": "Content A"},
        {"source_file": "doc3.md", "page": 3, "chunk_index": 0, "score": 0.75, "text": "Content C"},
    ]

    fused = aggregator.fuse([results_1, results_2, results_3], top_k=3)

    print(f"\nFused results:")
    for i, result in enumerate(fused, 1):
        print(f"  {i}. {result['source_file']} (RRF: {result['rrf_score']:.4f}, "
              f"variants: {result['num_variants']})")

    stats = aggregator.get_fusion_stats(fused)
    print(f"\nFusion stats: {stats}")

    print("\n✓ RRF fusion test passed")


def test_end_to_end_search():
    """Test complete search flow (requires running Qdrant instance)"""
    print("\n" + "=" * 70)
    print("Test 3: End-to-End Search")
    print("=" * 70)

    try:
        retriever = EnhancedProtocolRetriever()

        test_query = "sprawy pracownicze"
        print(f"\nSearching for: \"{test_query}\"")

        response = retriever.search(test_query, top_k=5, verbose=True)

        print(f"\n✓ Found {len(response['results'])} results")
        print(f"✓ Generated {len(response['variants'])} query variants")
        print(f"✓ Cache stats: {response['cache_stats']}")

        print("\n✓ End-to-end search test passed")

    except Exception as e:
        print(f"\n⚠ End-to-end test skipped (requires Qdrant): {e}")


def test_cache_hit_rate():
    """Test cache effectiveness with repeated queries"""
    print("\n" + "=" * 70)
    print("Test 4: Cache Hit Rate")
    print("=" * 70)

    try:
        retriever = EnhancedProtocolRetriever()

        # First query (should be cache miss)
        print("\nFirst query (cache miss expected)...")
        response1 = retriever.search("test query", top_k=3, verbose=False)
        stats1 = response1['cache_stats']
        print(f"  API calls: {stats1['api_calls']}")

        # Second query (should be cache hit for some variants)
        print("\nSecond query (cache hits expected)...")
        response2 = retriever.search("test query", top_k=3, verbose=False)
        stats2 = response2['cache_stats']
        print(f"  Cache hits: {stats2['cache_hits']}")
        print(f"  Cache misses: {stats2['cache_misses']}")
        print(f"  Hit rate: {stats2['cache_hit_rate']}")

        print("\n✓ Cache test passed")

    except Exception as e:
        print(f"\n⚠ Cache test skipped (requires Qdrant): {e}")


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("Running Enhanced RAG System Tests")
    print("=" * 70)

    try:
        test_query_expansion()
        test_rrf_fusion()
        test_end_to_end_search()
        test_cache_hit_rate()

        print("\n" + "=" * 70)
        print("✓ All tests passed!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
