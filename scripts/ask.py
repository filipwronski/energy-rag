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
    print(f"  {index}. Protocol No. {source['protocol_number']}, "
          f"Page {source['page']} (Date: {source['date_range']})")
    print(f"     RRF Score: {source['rrf_score']:.4f}")
    print(f"     {source['source']}")


def print_header():
    """Print application header"""
    print("\n" + "=" * 70)
    print("Q&A System - MSM Energetyka Board Protocols")
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
    print(f"\nQuestion: {question}\n")

    response = qa_system.ask(question, top_k=top_k, verbose=verbose)

    print("=" * 70)
    print("ANSWER:")
    print("=" * 70)
    print(response["answer"])
    print("=" * 70)

    if show_sources and response["sources"]:
        print(f"\n📚 Sources ({len(response['sources'])} documents):")
        for idx, source in enumerate(response["sources"], 1):
            format_source(source, idx)

    if verbose:
        print("\n" + "-" * 70)
        print("Search statistics:")
        metadata = response["search_metadata"]
        print(f"  Query variants: {len(metadata['variants'])}")
        print(f"  Cache - hits: {metadata['cache_stats']['cache_hits']}")
        print(f"  Cache - misses: {metadata['cache_stats']['cache_misses']}")
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
    print("\nInteractive mode - ask a question or type 'exit' to quit")
    print("\nSpecial commands:")
    print("  --verbose      - toggle verbose mode")
    print("  --sources      - toggle source display")
    print("  --stats        - show system statistics")
    print("  exit/quit      - exit")
    print("\nExample questions:")
    print("  - What renovations were carried out at ul. Bonifacego 66?")
    print("  - What decisions were made regarding waste shelters?")
    print("  - Who was hired in 2023?")
    print("  - What were the renovation expenses in 2024?")
    print()

    while True:
        try:
            question = input("\n💬 Question: ").strip()

            if question.lower() in ['exit', 'quit', 'q']:
                print("\nGoodbye!")
                break

            if question == "--verbose":
                verbose = not verbose
                print(f"✓ Verbose mode: {'enabled' if verbose else 'disabled'}")
                continue

            if question == "--sources":
                show_sources = not show_sources
                print(f"✓ Source display: {'enabled' if show_sources else 'disabled'}")
                continue

            if question == "--stats":
                stats = qa_system.get_stats()
                print("\n📊 System statistics:")
                print(f"  Processed queries: {stats['queries_processed']}")
                print(f"  Generated variants: {stats['total_variants_generated']}")
                print(f"  Cache - hits: {stats['embedder_stats']['cache_hits']}")
                print(f"  Cache - misses: {stats['embedder_stats']['cache_misses']}")
                print(f"  Cache - hit rate: {stats['embedder_stats']['cache_hit_rate']}")
                continue

            if not question:
                continue

            response = qa_system.ask(question, top_k=top_k, verbose=verbose)

            print("\n" + "=" * 70)
            print("ANSWER:")
            print("=" * 70)
            print(response["answer"])
            print("=" * 70)

            if show_sources and response["sources"]:
                print(f"\n📚 Sources ({len(response['sources'])} documents):")
                for idx, source in enumerate(response["sources"][:10], 1):  # Show top 10
                    format_source(source, idx)
                if len(response["sources"]) > 10:
                    print(f"  ... and {len(response['sources']) - 10} more")

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

        no_sources = "--no-sources" in sys.argv
        if no_sources:
            sys.argv.remove("--no-sources")

        # Initialize QA system
        print("Initializing Q&A system...")
        qa_system = ProtocolQASystem()
        print("✓ Ready!\n")

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
