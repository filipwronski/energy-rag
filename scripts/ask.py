#!/usr/bin/env python3
"""CLI interface for asking questions about protocol documents"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from rag.qa_system import ProtocolQASystem


def format_source(source, index):
    """
    Format a single source document

    Args:
        source: Source document dictionary
        index: Source index (1-based)
    """
    print(f"  {index}. Protokół nr {source['protocol_number']}, "
          f"Strona {source['page']} (Data: {source['date_range']})")
    print(f"     RRF Score: {source['rrf_score']:.4f}")
    print(f"     {source['source']}")


def print_header():
    """Print application header"""
    print("\n" + "=" * 70)
    print("Q&A System - Protokoły Zarządu MSM Energetyka")
    print("Powered by RAG + DeepSeek V3.2")
    print("=" * 70)


def single_question_mode(question, qa_system, top_k=20, verbose=False, show_sources=True):
    """
    Handle single question mode

    Args:
        question: User's question
        qa_system: ProtocolQASystem instance
        top_k: Number of documents to retrieve
        verbose: Show detailed information
        show_sources: Show source documents
    """
    print_header()
    print(f"\nPytanie: {question}\n")

    response = qa_system.ask(question, top_k=top_k, verbose=verbose)

    print("=" * 70)
    print("ODPOWIEDŹ:")
    print("=" * 70)
    print(response["answer"])
    print("=" * 70)

    if show_sources and response["sources"]:
        print(f"\n📚 Źródła ({len(response['sources'])} dokumentów):")
        for idx, source in enumerate(response["sources"], 1):
            format_source(source, idx)

    if verbose:
        print("\n" + "-" * 70)
        print("Statystyki wyszukiwania:")
        metadata = response["search_metadata"]
        print(f"  Warianty zapytań: {len(metadata['variants'])}")
        print(f"  Cache - trafienia: {metadata['cache_stats']['cache_hits']}")
        print(f"  Cache - chybienia: {metadata['cache_stats']['cache_misses']}")
        print("-" * 70)


def interactive_mode(qa_system, top_k=20, verbose=False, show_sources=True):
    """
    Handle interactive question mode

    Args:
        qa_system: ProtocolQASystem instance
        top_k: Number of documents to retrieve
        verbose: Show detailed information
        show_sources: Show source documents
    """
    print_header()
    print("\nTryb interaktywny - zadaj pytanie lub wpisz 'exit' aby zakończyć")
    print("\nKomendy specjalne:")
    print("  --verbose      - włącz/wyłącz tryb szczegółowy")
    print("  --sources      - włącz/wyłącz wyświetlanie źródeł")
    print("  --stats        - pokaż statystyki systemu")
    print("  exit/quit      - zakończ")
    print("\nPrzykładowe pytania:")
    print("  - Jakie remonty były przeprowadzane przy ul. Bonifacego 66?")
    print("  - Jakie decyzje podjęto w sprawie wiat śmietnikowych?")
    print("  - Kto został zatrudniony w 2023 roku?")
    print("  - Jakie były wydatki na remonty w 2024 roku?")
    print()

    while True:
        try:
            question = input("\n💬 Pytanie: ").strip()

            if question.lower() in ['exit', 'quit', 'q', 'wyjście', 'koniec']:
                print("\nDo widzenia!")
                break

            if question == "--verbose":
                verbose = not verbose
                print(f"✓ Tryb szczegółowy: {'włączony' if verbose else 'wyłączony'}")
                continue

            if question == "--sources":
                show_sources = not show_sources
                print(f"✓ Wyświetlanie źródeł: {'włączone' if show_sources else 'wyłączone'}")
                continue

            if question == "--stats":
                stats = qa_system.get_stats()
                print("\n📊 Statystyki systemu:")
                print(f"  Przetworzone zapytania: {stats['queries_processed']}")
                print(f"  Wygenerowane warianty: {stats['total_variants_generated']}")
                print(f"  Cache - trafienia: {stats['embedder_stats']['cache_hits']}")
                print(f"  Cache - chybienia: {stats['embedder_stats']['cache_misses']}")
                print(f"  Cache - współczynnik: {stats['embedder_stats']['cache_hit_rate']}")
                continue

            if not question:
                continue

            response = qa_system.ask(question, top_k=top_k, verbose=verbose)

            print("\n" + "=" * 70)
            print("ODPOWIEDŹ:")
            print("=" * 70)
            print(response["answer"])
            print("=" * 70)

            if show_sources and response["sources"]:
                print(f"\n📚 Źródła ({len(response['sources'])} dokumentów):")
                for idx, source in enumerate(response["sources"][:10], 1):  # Show top 10
                    format_source(source, idx)
                if len(response["sources"]) > 10:
                    print(f"  ... i {len(response['sources']) - 10} więcej")

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

        no_sources = "--no-sources" in sys.argv
        if no_sources:
            sys.argv.remove("--no-sources")

        # Initialize QA system
        print("Inicjalizacja systemu Q&A...")
        qa_system = ProtocolQASystem()
        print("✓ Gotowe!\n")

        if len(sys.argv) > 1:
            # Single question mode
            question = " ".join(sys.argv[1:])
            single_question_mode(
                question,
                qa_system,
                verbose=verbose,
                show_sources=not no_sources
            )
        else:
            # Interactive mode
            interactive_mode(
                qa_system,
                verbose=verbose,
                show_sources=not no_sources
            )

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
