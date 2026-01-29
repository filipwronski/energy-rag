"""Unit tests for cache module"""

import pytest
from rag.cache import EmbeddingCache


class TestHashQuery:
    """Test _hash_query method"""

    def test_standard_text_hashing(self):
        """Test hashing of standard text"""
        cache = EmbeddingCache(db_path=":memory:")
        query = "test query"
        hash_result = cache._hash_query(query)
        # SHA256 hash should be 64 characters (hexadecimal)
        assert len(hash_result) == 64
        assert all(c in '0123456789abcdef' for c in hash_result)

    def test_same_text_produces_same_hash(self):
        """Test that same text produces same hash"""
        cache = EmbeddingCache(db_path=":memory:")
        query = "identical query"
        hash1 = cache._hash_query(query)
        hash2 = cache._hash_query(query)
        assert hash1 == hash2

    def test_different_text_produces_different_hash(self):
        """Test that different text produces different hash"""
        cache = EmbeddingCache(db_path=":memory:")
        query1 = "first query"
        query2 = "second query"
        hash1 = cache._hash_query(query1)
        hash2 = cache._hash_query(query2)
        assert hash1 != hash2

    def test_unicode_special_characters(self):
        """Test hashing with unicode and special characters"""
        cache = EmbeddingCache(db_path=":memory:")
        query = "Protokół nr 3 z ustaleń 29.01. - 11.02.2025 ąćęłńóśźż"
        hash_result = cache._hash_query(query)
        # Should produce valid SHA256 hash
        assert len(hash_result) == 64
        assert all(c in '0123456789abcdef' for c in hash_result)
