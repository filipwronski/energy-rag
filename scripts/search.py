#!/usr/bin/env python3
"""CLI search interface for protocol documents"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from rag.enhanced_retriever import EnhancedProtocolRetriever


def format_result(result, index):
    """
    Format a single search result

    Args:
        result: Result dictionary
        index: Result index (1-based)
    """
    print(f"\n{'=' * 70}")
    print(f"{index}. [Protocol No. {result['protocol_number']}, Page {result['page']}] "
          f"(RRF: {result['rrf_score']:.4f})")
    print(f"Source: {result['source']}")
    print(f"Date: {result['date_range']}")

    # Show contributing variants
    if "contributing_variants" in result:
        print(f"Found by {result['num_variants']} query variants")

    print(f"\n{result['text'][:800]}")  # Show first 800 chars
    if len(result['text']) > 800:
        print("...")
    print(f"{'=' * 70}")


def format_metadata(search_response, verbose=False):
    """
    Format search metadata

    Args:
        search_response: Response from enhanced_retriever.search()
        verbose: Show detailed information
    """
    if not verbose:
        return

    print("\n" + "-" * 70)
    print("Search details:")
    print(f"  Query variants: {len(search_response['variants'])}")

    if verbose:
        for i, variant in enumerate(search_response['variants'], 1):
            print(f"    {i}. [{variant['method']}] {variant['text']}")

    fusion_stats = search_response['fusion_stats']
    print(f"\n  Fusion statistics (RRF):")
    print(f"    Average variants per result: {fusion_stats['avg_variants_per_result']}")

    cache_stats = search_response['cache_stats']
    print(f"\n  Cache:")
    print(f"    Hits: {cache_stats['cache_hits']}")
    print(f"    Misses: {cache_stats['cache_misses']}")
    print(f"    Hit rate: {cache_stats['cache_hit_rate']}")
    print(f"    API calls: {cache_stats['api_calls']}")

    print("-" * 70)


def print_header():
    """Print application header"""
    print("\n" + "=" * 70)
    print("RAG Search - MSM Energetyka Board Protocols")
    print("Enhanced with Query Expansion + RRF")
    print("=" * 70)


def single_query_mode(query, retriever, top_k=5, verbose=False):
    """
    Handle single query mode

    Args:
        query: Search query
        retriever: EnhancedProtocolRetriever instance
        top_k: Number of results to return
        verbose: Show detailed information
    """
    print_header()
    print(f"\nSearch results for: \"{query}\"")

    search_response = retriever.search(query, top_k=top_k, verbose=verbose)
    results = search_response["results"]

    if not results:
        print("\nNo results found.")
        print("Try changing your query or check if the index has been built.")
        return

    print(f"Found {len(results)} results\n")

    for idx, result in enumerate(results, 1):
        format_result(result, idx)

    # Show metadata
    format_metadata(search_response, verbose=verbose)


def interactive_mode(retriever, top_k=5, verbose=False):
    """
    Handle interactive query mode

    Args:
        retriever: EnhancedProtocolRetriever instance
        top_k: Number of results to return
        verbose: Show detailed information
    """
    print_header()
    print("\nInteractive mode - type your query or 'exit' to quit")
    print("Special commands:")
    print("  --verbose      - toggle verbose mode")
    print("  --stats        - show statistics")
    print("  exit/quit      - quit")
    print("\nExample queries:")
    print("  - employee matters")
    print("  - garbage shelters")
    print("  - Konstancinska street")
    print("  - Tender Commission")
    print()

    while True:
        try:
            query = input("Query: ").strip()

            if query.lower() in ['exit', 'quit', 'q', 'wyjście', 'koniec']:
                print("\nGoodbye!")
                break

            if query == "--verbose":
                verbose = not verbose
                print(f"Verbose mode: {'enabled' if verbose else 'disabled'}")
                continue

            if query == "--stats":
                stats = retriever.get_stats()
                print("\nStatistics:")
                print(f"  Queries processed: {stats['queries_processed']}")
                print(f"  Variants generated: {stats['total_variants_generated']}")
                print(f"  Cache - hits: {stats['embedder_stats']['cache_hits']}")
                print(f"  Cache - misses: {stats['embedder_stats']['cache_misses']}")
                print(f"  Cache - hit rate: {stats['embedder_stats']['cache_hit_rate']}")
                continue

            if not query:
                continue

            search_response = retriever.search(query, top_k=top_k, verbose=verbose)
            results = search_response["results"]

            if not results:
                print("\nNo results found.")
                continue

            print(f"\nFound {len(results)} results\n")

            for idx, result in enumerate(results, 1):
                format_result(result, idx)

            # Show metadata
            format_metadata(search_response, verbose=verbose)

            print()

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            if verbose:
                traceback.print_exc()


def main():
    """Main entry point"""
    try:
        # Parse arguments
        verbose = "--verbose" in sys.argv
        if verbose:
            sys.argv.remove("--verbose")

        # Initialize retriever
        print("Initializing search engine...")
        retriever = EnhancedProtocolRetriever()
        print("✓ Ready!\n")

        if len(sys.argv) > 1:
            # Single query mode
            query = " ".join(sys.argv[1:])
            single_query_mode(query, retriever, verbose=verbose)
        else:
            # Interactive mode
            interactive_mode(retriever, verbose=verbose)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure that:")
        print("1. Qdrant is running (docker run -p 6333:6333 qdrant/qdrant)")
        print("2. Index has been built (python scripts/build_index.py)")
        print("3. .env file contains OPEN_ROUTER_API_KEY")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
