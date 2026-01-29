"""Unit tests for RRF aggregator module"""

import pytest
from rag.rrf_aggregator import RRFAggregator


class TestGenerateChunkId:
    """Test _generate_chunk_id method"""

    def test_standard_result_dict(self):
        """Test chunk ID generation with standard result dict"""
        aggregator = RRFAggregator()
        result = {
            "source_file": "protocol_3.md",
            "page": 5,
            "chunk_index": 2
        }
        chunk_id = aggregator._generate_chunk_id(result)
        assert chunk_id == "protocol_3.md:5:2"

    def test_different_values(self):
        """Test chunk ID generation with different values"""
        aggregator = RRFAggregator()
        result = {
            "source_file": "meeting_notes.md",
            "page": 10,
            "chunk_index": 0
        }
        chunk_id = aggregator._generate_chunk_id(result)
        assert chunk_id == "meeting_notes.md:10:0"

    def test_uniqueness(self):
        """Test that different results produce different chunk IDs"""
        aggregator = RRFAggregator()
        result1 = {
            "source_file": "doc1.md",
            "page": 1,
            "chunk_index": 1
        }
        result2 = {
            "source_file": "doc1.md",
            "page": 1,
            "chunk_index": 2
        }
        chunk_id1 = aggregator._generate_chunk_id(result1)
        chunk_id2 = aggregator._generate_chunk_id(result2)
        assert chunk_id1 != chunk_id2
        assert chunk_id1 == "doc1.md:1:1"
        assert chunk_id2 == "doc1.md:1:2"
