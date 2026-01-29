"""Test RAG improvements"""

import pytest
from rag.query_expander import QueryExpander
from rag.semantic_chunker import SemanticChunker
from rag.context_enricher import ContextEnricher
from rag.bm25_index import BM25Index
from rag.reranker import CrossEncoderReranker
from rag.openrouter_client import OpenRouterClient


class TestQueryExpansion:
    """Test extended query expansion"""

    def test_abbreviation_expansion(self):
        """Test abbreviation expansion"""
        client = OpenRouterClient()
        expander = QueryExpander(client)

        # Test single abbreviation
        result = expander.expand_abbreviations("ZO osiedle")
        assert "zarząd osiedla" in result.lower()

        # Test multiple abbreviations
        result = expander.expand_abbreviations("c.o. i c.w.u.")
        assert "centralne" in result.lower()

    def test_entity_extraction(self):
        """Test entity extraction"""
        client = OpenRouterClient()
        expander = QueryExpander(client)

        query = "Protokół nr 15 dotyczący remontu na Bonifacego 66 za 50 000 zł"
        entities = expander.extract_entities(query)

        assert "15" in entities["protocol_numbers"]
        assert len(entities["amounts"]) > 0
        assert len(entities["addresses"]) > 0

    def test_extended_synonyms(self):
        """Test that extended synonym dictionary is larger"""
        client = OpenRouterClient()
        expander = QueryExpander(client)

        # Check that we have 100+ terms
        assert len(expander.SYNONYMS) >= 80  # At least 80 main categories

        # Check specific domains
        assert "ogrzewanie" in expander.SYNONYMS
        assert "elewacja" in expander.SYNONYMS
        assert "przetarg" in expander.SYNONYMS


class TestSemanticChunking:
    """Test semantic chunking"""

    def test_section_extraction(self):
        """Test section extraction from page content"""
        chunker = SemanticChunker()

        page_content = """## Strona 1

### Punkt porządku obrad

**Punkt 1.** Sprawy organizacyjne
Tekst dotyczący spraw organizacyjnych.

**Punkt 2.** Sprawy finansowe
Tekst dotyczący spraw finansowych.
"""

        sections = chunker.extract_sections(page_content)

        assert len(sections) >= 2
        assert any("Punkt 1" in s.get('header', '') for s in sections)

    def test_merge_small_sections(self):
        """Test merging of small sections"""
        chunker = SemanticChunker()

        sections = [
            {'header': 'H1', 'text': 'Short', 'type': 'section'},
            {'header': 'H2', 'text': 'Also short', 'type': 'section'},
            {'header': 'H3', 'text': 'x' * 300, 'type': 'section'}
        ]

        merged = chunker.merge_small_sections(sections)

        # Small sections should be merged
        assert len(merged) < len(sections)


class TestContextEnrichment:
    """Test contextual enrichment"""

    def test_keyword_extraction(self):
        """Test keyword extraction"""
        enricher = ContextEnricher()

        text = "Remont dachu budynku na ulicy Bonifacego. Koszt remontu wynosi 50000 złotych."
        keywords = enricher.extract_keywords(text, top_k=5)

        assert len(keywords) <= 5
        assert all(isinstance(kw, str) for kw in keywords)

    def test_summary_generation(self):
        """Test summary generation"""
        enricher = ContextEnricher()

        text = "To jest pierwsze zdanie. To jest drugie zdanie. To jest trzecie zdanie."
        summary = enricher.generate_chunk_summary(text)

        assert len(summary) > 0
        assert len(summary) <= 100 or '...' in summary

    def test_chunk_enrichment(self):
        """Test full chunk enrichment"""
        enricher = ContextEnricher()

        chunks = [
            {
                'text': 'Remont dachu na Bonifacego',
                'source_file': 'test.md',
                'page_number': 1
            }
        ]

        doc_context = {
            'source_title': 'Protokół 15',
            'protocol_number': 15,
            'date_range': '2025-01-01'
        }

        enriched = enricher.enrich_chunks(chunks, doc_context)

        assert len(enriched) == 1
        assert 'keywords' in enriched[0]
        assert 'summary' in enriched[0]
        assert enriched[0]['doc_protocol_number'] == 15


class TestBM25Index:
    """Test BM25 sparse retrieval"""

    def test_tokenization(self):
        """Test BM25 tokenization preserves important patterns"""
        index = BM25Index()

        # Test protocol number preservation
        tokens = index.tokenize("Protokół nr 15")
        assert any('protokol_15' in t for t in tokens)

        # Test amount preservation
        tokens = index.tokenize("50 000 zł")
        assert any('kwota' in t for t in tokens)

    def test_build_and_search(self):
        """Test building and searching BM25 index"""
        index = BM25Index()

        chunks = [
            {'text': 'Protokół nr 15 z zebrania zarządu'},
            {'text': 'Remont dachu na Bonifacego'},
            {'text': 'Wymiana okien w budynku'}
        ]

        index.build(chunks)

        # Search for protocol
        results = index.search("Protokół nr 15", top_k=1)
        assert len(results) > 0
        assert results[0][0] == 0  # First chunk should match


class TestCrossEncoderReranker:
    """Test cross-encoder reranking"""

    @pytest.mark.skip(reason="Requires model download, tested separately")
    def test_reranker_initialization(self):
        """Test reranker can be initialized"""
        reranker = CrossEncoderReranker()
        assert reranker is not None

    def test_reranker_config(self):
        """Test reranker configuration"""
        from rag.config import RERANKER_MODEL, RERANKER_DEVICE

        assert RERANKER_MODEL == "BAAI/bge-reranker-v2-m3"
        assert RERANKER_DEVICE in ["cpu", "cuda"]
