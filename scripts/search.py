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
    print(f"{index}. [Protokół nr {result['protocol_number']}, Strona {result['page']}] "
          f"(RRF: {result['rrf_score']:.4f})")
    print(f"Źródło: {result['source']}")
    print(f"Data: {result['date_range']}")

    # Show contributing variants
    if "contributing_variants" in result:
        print(f"Znalezione przez {result['num_variants']} wariantów zapytania")

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
    print("Szczegóły wyszukiwania:")
    print(f"  Warianty zapytań: {len(search_response['variants'])}")

    if verbose:
        for i, variant in enumerate(search_response['variants'], 1):
            print(f"    {i}. [{variant['method']}] {variant['text']}")

    fusion_stats = search_response['fusion_stats']
    print(f"\n  Statystyki fuzji (RRF):")
    print(f"    Średnia wariantów na wynik: {fusion_stats['avg_variants_per_result']}")

    cache_stats = search_response['cache_stats']
    print(f"\n  Cache:")
    print(f"    Trafienia: {cache_stats['cache_hits']}")
    print(f"    Chybienia: {cache_stats['cache_misses']}")
    print(f"    Współczynnik trafień: {cache_stats['cache_hit_rate']}")
    print(f"    Wywołania API: {cache_stats['api_calls']}")

    print("-" * 70)


def print_header():
    """Print application header"""
    print("\n" + "=" * 70)
    print("RAG Search - Protokoły Zarządu MSM Energetyka")
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
    print(f"\nWyniki wyszukiwania dla: \"{query}\"")

    search_response = retriever.search(query, top_k=top_k, verbose=verbose)
    results = search_response["results"]

    if not results:
        print("\nNie znaleziono wyników.")
        print("Spróbuj zmienić zapytanie lub sprawdź czy indeks został zbudowany.")
        return

    print(f"Znaleziono {len(results)} wyników\n")

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
    print("\nTryb interaktywny - wpisz zapytanie lub 'exit' aby zakończyć")
    print("Komendy specjalne:")
    print("  --verbose      - włącz tryb szczegółowy")
    print("  --stats        - pokaż statystyki")
    print("  exit/quit      - zakończ")
    print("\nPrzykładowe zapytania:")
    print("  - sprawy pracownicze")
    print("  - wiaty śmietnikowe")
    print("  - ul. Konstancińska")
    print("  - Komisja Przetargowa")
    print()

    while True:
        try:
            query = input("Zapytanie: ").strip()

            if query.lower() in ['exit', 'quit', 'q', 'wyjście', 'koniec']:
                print("\nDo widzenia!")
                break

            if query == "--verbose":
                verbose = not verbose
                print(f"Tryb szczegółowy: {'włączony' if verbose else 'wyłączony'}")
                continue

            if query == "--stats":
                stats = retriever.get_stats()
                print("\nStatystyki:")
                print(f"  Przetworzone zapytania: {stats['queries_processed']}")
                print(f"  Wygenerowane warianty: {stats['total_variants_generated']}")
                print(f"  Cache - trafienia: {stats['embedder_stats']['cache_hits']}")
                print(f"  Cache - chybienia: {stats['embedder_stats']['cache_misses']}")
                print(f"  Cache - współczynnik: {stats['embedder_stats']['cache_hit_rate']}")
                continue

            if not query:
                continue

            search_response = retriever.search(query, top_k=top_k, verbose=verbose)
            results = search_response["results"]

            if not results:
                print("\nNie znaleziono wyników.")
                continue

            print(f"\nZnaleziono {len(results)} wyników\n")

            for idx, result in enumerate(results, 1):
                format_result(result, idx)

            # Show metadata
            format_metadata(search_response, verbose=verbose)

            print()

        except KeyboardInterrupt:
            print("\n\nDo widzenia!")
            break
        except Exception as e:
            print(f"\n❌ Błąd: {e}")
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
        print("Inicjalizacja wyszukiwarki...")
        retriever = EnhancedProtocolRetriever()
        print("✓ Gotowe!\n")

        if len(sys.argv) > 1:
            # Single query mode
            query = " ".join(sys.argv[1:])
            single_query_mode(query, retriever, verbose=verbose)
        else:
            # Interactive mode
            interactive_mode(retriever, verbose=verbose)

    except Exception as e:
        print(f"\n❌ Błąd: {e}")
        print("\nUpewnij się, że:")
        print("1. Qdrant działa (docker run -p 6333:6333 qdrant/qdrant)")
        print("2. Indeks został zbudowany (python scripts/build_index.py)")
        print("3. Plik .env zawiera OPEN_ROUTER_API_KEY")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
