#!/usr/bin/env python3
"""Build Qdrant index from markdown files in output/"""

from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import sys
import time

sys.path.append(str(Path(__file__).parent.parent))

from rag.chunker import chunk_all_documents
from rag.openrouter_embedder import OpenRouterEmbedder
from rag.config import QDRANT_URL, COLLECTION_NAME, EMBEDDING_DIM, ENABLE_CACHE, CACHE_DB_PATH


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


def main():
    """Build the Qdrant index from markdown documents"""
    print("=" * 70)
    print("Building Qdrant index for protocol documents")
    print("=" * 70)

    # 1. Initialize
    print("\n1. Initializing Qdrant client and embedder...")
    client = QdrantClient(url=QDRANT_URL)
    embedder = OpenRouterEmbedder(use_cache=ENABLE_CACHE, cache_path=CACHE_DB_PATH)
    print(f"   ✓ OpenRouter embedder initialized (cache: {'enabled' if ENABLE_CACHE else 'disabled'})")

    # 2. Recreate collection
    print(f"\n2. Creating collection '{COLLECTION_NAME}'...")
    try:
        client.delete_collection(collection_name=COLLECTION_NAME)
        print(f"   ✓ Deleted existing collection")
    except Exception:
        print(f"   ℹ No existing collection to delete")

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE)
    )
    print(f"   ✓ Created collection with {EMBEDDING_DIM}-dim vectors, cosine distance")

    # 3. Process documents
    print("\n3. Processing documents...")
    output_dir = Path("output")
    chunks = chunk_all_documents(output_dir)

    if not chunks:
        print("   ⚠ No chunks created. Check if output/ contains markdown files.")
        return

    # 4. Estimate cost
    print("\n4. Estimating indexing cost...")
    cost_info = estimate_cost(len(chunks))
    print(f"   Chunks to embed: {cost_info['num_chunks']}")
    print(f"   Estimated tokens: {cost_info['estimated_tokens']:,}")
    print(f"   Estimated cost: ${cost_info['estimated_cost_usd']:.4f}")
    print(f"   Cost per chunk: ${cost_info['cost_per_chunk']:.6f}")

    # Confirm before proceeding
    response = input("\n   Proceed with indexing? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("   Indexing cancelled.")
        return

    # 5. Generate embeddings and batch insert
    print(f"\n5. Generating embeddings and indexing {len(chunks)} chunks...")

    start_time = time.time()
    batch_size = 50  # Process 50 chunks at a time
    points = []

    for i in range(0, len(chunks), batch_size):
        batch_chunks = chunks[i:i+batch_size]
        batch_texts = [chunk["text"] for chunk in batch_chunks]

        print(f"   Processing chunks {i+1}-{min(i+batch_size, len(chunks))}/{len(chunks)}...")

        # Get embeddings for batch
        embeddings = embedder.embed_batch(batch_texts)

        # Create points
        for j, (chunk, embedding) in enumerate(zip(batch_chunks, embeddings)):
            point = PointStruct(
                id=i + j,
                vector=embedding,
                payload=chunk
            )
            points.append(point)

        # Insert batch into Qdrant
        client.upsert(collection_name=COLLECTION_NAME, points=points)
        points = []

        # Small delay to avoid rate limiting
        if i + batch_size < len(chunks):
            time.sleep(0.5)

    elapsed_time = time.time() - start_time

    # 6. Verify indexing
    print("\n6. Verifying index...")
    collection_info = client.get_collection(collection_name=COLLECTION_NAME)
    vector_count = collection_info.points_count
    print(f"   ✓ Collection contains {vector_count} vectors")

    # 7. Cache stats
    if ENABLE_CACHE:
        print("\n7. Cache statistics...")
        stats = embedder.get_stats()
        print(f"   Cache hits: {stats['cache_hits']}")
        print(f"   Cache misses: {stats['cache_misses']}")
        print(f"   API calls: {stats['api_calls']}")
        print(f"   Hit rate: {stats['cache_hit_rate']}")

    # 8. Final stats
    print("\n" + "=" * 70)
    print("✓ Indexing complete!")
    print(f"✓ Indexed {len(chunks)} chunks from {len(list(output_dir.glob('*.md')))} files")
    print(f"✓ Time elapsed: {elapsed_time:.1f}s ({elapsed_time/len(chunks):.2f}s per chunk)")
    print(f"✓ Actual cost: ~${cost_info['estimated_cost_usd']:.4f}")
    print("=" * 70)
    print("\nYou can now search using: python scripts/search.py \"your query\"")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
