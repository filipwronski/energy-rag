"""Unit tests for query expander module"""

import pytest
from unittest.mock import Mock
from rag.query_expander import QueryExpander


class TestExpandWithSynonyms:
    """Test expand_with_synonyms method"""

    def test_replace_known_synonym(self):
        """Test replacement of a known synonym (non-key word)"""
        mock_client = Mock()
        expander = QueryExpander(mock_client)
        # Use "uchwała" which is in the synonyms list for "protokół" but not the key
        query = "uchwała zarządu"
        result = expander.expand_with_synonyms(query)
        # Should replace "uchwała" with a different synonym from the list
        # (could be "protokół", "dokument", or "zapis")
        assert result != query
        # Result should contain a different synonym
        assert any(word in result for word in ["protokół", "dokument", "zapis"])

    def test_no_replacement_if_no_synonym(self):
        """Test that words without synonyms remain unchanged"""
        mock_client = Mock()
        expander = QueryExpander(mock_client)
        query = "randomword xyz123"
        result = expander.expand_with_synonyms(query)
        # No synonyms for these words, should remain the same
        assert result == query

    def test_multiple_word_replacement(self):
        """Test replacement of multiple words with synonyms"""
        mock_client = Mock()
        expander = QueryExpander(mock_client)
        # Use non-key synonyms: "kontrakt" (synonym of "umowa") and "naprawa" (synonym of "remont")
        query = "kontrakt o naprawa"
        result = expander.expand_with_synonyms(query)
        # Both words should be replaced with different synonyms from their lists
        assert result != query

    def test_case_handling(self):
        """Test that synonym replacement handles case correctly"""
        mock_client = Mock()
        expander = QueryExpander(mock_client)
        query = "Protokół Zarządu"
        result = expander.expand_with_synonyms(query)
        # Function converts to lowercase for processing
        # Result should be lowercase
        assert result.islower() or result == query.lower()


class TestExpandWithWordOrder:
    """Test expand_with_word_order method"""

    def test_reorder_with_conjunctions(self):
        """Test word reordering with Polish conjunctions"""
        mock_client = Mock()
        expander = QueryExpander(mock_client)
        query = "budowa i remont budynku"
        result = expander.expand_with_word_order(query)
        # Should reorder parts around conjunction
        assert result != query or len(query.split()) <= 2

    def test_simple_word_reversal(self):
        """Test simple word reversal for queries without conjunctions"""
        mock_client = Mock()
        expander = QueryExpander(mock_client)
        query = "protokół zarządu komisji"
        result = expander.expand_with_word_order(query)
        # For queries with more than 2 words and no conjunctions,
        # should reverse word order
        assert result != query
        words_original = query.split()
        words_result = result.split()
        assert len(words_original) == len(words_result)

    def test_single_word_no_change(self):
        """Test that single word or two-word queries don't change"""
        mock_client = Mock()
        expander = QueryExpander(mock_client)
        query = "protokół"
        result = expander.expand_with_word_order(query)
        # Single word should remain unchanged
        assert result == query

        query_two = "protokół zarządu"
        result_two = expander.expand_with_word_order(query_two)
        # Two words should remain unchanged
        assert result_two == query_two
