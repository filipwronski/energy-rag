"""SQLite-based cache for query embeddings"""

import sqlite3
import json
import hashlib
from typing import List, Optional
from pathlib import Path


class EmbeddingCache:
    """
    SQLite cache for storing and retrieving query embeddings
    """

    def __init__(self, db_path: str = "embedding_cache.db"):
        """
        Initialize embedding cache

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Create database schema if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create embeddings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                query_hash TEXT PRIMARY KEY,
                query_text TEXT NOT NULL,
                embedding BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create index for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_query_text
            ON embeddings(query_text)
        """)

        conn.commit()
        conn.close()

    def _hash_query(self, query: str) -> str:
        """
        Generate SHA256 hash for query text

        Args:
            query: Query text

        Returns:
            SHA256 hash as hexadecimal string
        """
        return hashlib.sha256(query.encode('utf-8')).hexdigest()

    def get(self, query: str) -> Optional[List[float]]:
        """
        Retrieve embedding from cache

        Args:
            query: Query text

        Returns:
            Embedding vector or None if not found in cache
        """
        query_hash = self._hash_query(query)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT embedding FROM embeddings WHERE query_hash = ?",
            (query_hash,)
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            # Deserialize JSON to list of floats
            return json.loads(row[0])
        return None

    def put(self, query: str, embedding: List[float]):
        """
        Store embedding in cache

        Args:
            query: Query text
            embedding: Embedding vector (list of floats)
        """
        query_hash = self._hash_query(query)
        embedding_json = json.dumps(embedding)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Insert or replace existing entry
        cursor.execute("""
            INSERT OR REPLACE INTO embeddings (query_hash, query_text, embedding)
            VALUES (?, ?, ?)
        """, (query_hash, query, embedding_json))

        conn.commit()
        conn.close()

    def clear(self):
        """Clear all cache entries"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM embeddings")
        conn.commit()
        conn.close()

    def get_stats(self) -> dict:
        """
        Get cache statistics

        Returns:
            Dictionary with cache statistics (total entries, database size)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Count total entries
        cursor.execute("SELECT COUNT(*) FROM embeddings")
        total_entries = cursor.fetchone()[0]

        # Get database size
        try:
            cursor.execute("SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()")
            db_size_bytes = cursor.fetchone()[0]
        except:
            # Fallback if pragma doesn't work
            db_size_bytes = Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0

        conn.close()

        return {
            "total_entries": total_entries,
            "db_size_mb": round(db_size_bytes / (1024 * 1024), 2)
        }
