#!/usr/bin/env python3
"""CLI search interface for protocol documents"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from rag.retriever import ProtocolRetriever


def format_result(result, index):
    """
    Format a single search result

    Args:
        result: Result dictionary
        index: Result index (1-based)
    """
    print(f"\n{'=' * 70}")
    print(f"{index}. [Protokół nr {result['protocol_number']}, Strona {result['page']}] (podobieństwo: {result['score']:.2f})")
    print(f"Źródło: {result['source']}")
    print(f"Data: {result['date_range']}")
    print(f"\n{result['text'][:800]}")  # Show first 800 chars
    if len(result['text']) > 800:
        print("...")
    print(f"{'=' * 70}")


def print_header():
    """Print application header"""
    print("\n" + "=" * 70)
    print("RAG Search - Protokoły Zarządu MSM Energetyka")
    print("=" * 70)


def single_query_mode(query, retriever, top_k=5):
    """
    Handle single query mode

    Args:
        query: Search query
        retriever: ProtocolRetriever instance
        top_k: Number of results to return
    """
    print_header()
    print(f"\nWyniki wyszukiwania dla: \"{query}\"")

    results = retriever.search(query, top_k=top_k)

    if not results:
        print("\nNie znaleziono wyników.")
        print("Spróbuj zmienić zapytanie lub sprawdź czy indeks został zbudowany.")
        return

    print(f"Znaleziono {len(results)} wyników\n")

    for idx, result in enumerate(results, 1):
        format_result(result, idx)


def interactive_mode(retriever, top_k=5):
    """
    Handle interactive query mode

    Args:
        retriever: ProtocolRetriever instance
        top_k: Number of results to return
    """
    print_header()
    print("\nTryb interaktywny - wpisz zapytanie lub 'exit' aby zakończyć")
    print("Przykładowe zapytania:")
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

            if not query:
                continue

            results = retriever.search(query, top_k=top_k)

            if not results:
                print("\nNie znaleziono wyników.")
                continue

            print(f"\nZnaleziono {len(results)} wyników\n")

            for idx, result in enumerate(results, 1):
                format_result(result, idx)

            print()

        except KeyboardInterrupt:
            print("\n\nDo widzenia!")
            break
        except Exception as e:
            print(f"\n❌ Błąd: {e}")


def main():
    """Main entry point"""
    try:
        # Initialize retriever
        retriever = ProtocolRetriever()

        if len(sys.argv) > 1:
            # Single query mode
            query = " ".join(sys.argv[1:])
            single_query_mode(query, retriever)
        else:
            # Interactive mode
            interactive_mode(retriever)

    except Exception as e:
        print(f"\n❌ Błąd: {e}")
        print("\nUpewnij się, że:")
        print("1. Qdrant działa (docker run -p 6333:6333 qdrant/qdrant)")
        print("2. Indeks został zbudowany (python scripts/build_index.py)")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
