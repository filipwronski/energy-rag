#!/usr/bin/env python3
"""Build Qdrant index from markdown files in output/"""

from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import sys

sys.path.append(str(Path(__file__).parent.parent))

from rag.chunker import chunk_all_documents
from rag.embedder import PolishEmbedder
from rag.config import QDRANT_URL, COLLECTION_NAME, EMBEDDING_DIM


def main():
    """Build the Qdrant index from markdown documents"""
    print("=" * 70)
    print("Building Qdrant index for protocol documents")
    print("=" * 70)

    # 1. Initialize
    print("\n1. Initializing Qdrant client and embedder...")
    client = QdrantClient(url=QDRANT_URL)
    embedder = PolishEmbedder()

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

    # 4. Generate embeddings and batch insert
    print(f"\n4. Generating embeddings and indexing {len(chunks)} chunks...")

    # Batch processing for efficiency
    batch_size = 10
    points = []

    for idx, chunk in enumerate(chunks):
        if (idx + 1) % 5 == 0:
            print(f"   Processing chunk {idx + 1}/{len(chunks)}...")

        embedding = embedder.embed(chunk["text"])
        point = PointStruct(
            id=idx,
            vector=embedding,
            payload=chunk
        )
        points.append(point)

        # Insert in batches
        if len(points) >= batch_size or idx == len(chunks) - 1:
            client.upsert(collection_name=COLLECTION_NAME, points=points)
            points = []

    # 5. Verify indexing
    print("\n5. Verifying index...")
    collection_info = client.get_collection(collection_name=COLLECTION_NAME)
    vector_count = collection_info.points_count

    print(f"   ✓ Collection contains {vector_count} vectors")

    # 6. Stats
    print("\n" + "=" * 70)
    print("✓ Indexing complete!")
    print(f"✓ Indexed {len(chunks)} chunks from {len(list(output_dir.glob('*.md')))} files")
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
