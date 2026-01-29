"""Contextual enrichment for chunks with keywords, summaries, and navigation"""

import re
from typing import List, Dict
from collections import Counter
from .config import KEYWORDS_TOP_K, SUMMARY_MAX_LENGTH


class ContextEnricher:
    """
    Enrich chunks with contextual metadata:
    - Keywords (TF-IDF based)
    - Summaries (first sentence or truncated)
    - Navigation (prev/next chunk references)
    """

    # Polish stopwords for keyword extraction
    STOPWORDS = {
        'i', 'w', 'z', 'na', 'do', 'o', 'z', 'się', 'to', 'że', 'lub',
        'oraz', 'jak', 'a', 'ale', 'od', 'po', 'dla', 'przez', 'przy',
        'ze', 'za', 'pod', 'nad', 'przed', 'między', 'bez', 'przy',
        'jest', 'są', 'był', 'była', 'było', 'być', 'być', 'mieć', 'ma',
        'jego', 'jej', 'ich', 'ten', 'ta', 'to', 'te', 'tym', 'tej',
        'który', 'która', 'które', 'którzy', 'pan', 'pani', 'nr', 'str',
        'strona', 'punkt', 'pkt', 'rok', 'r', 'ul', 'os', 'm', 'co',
        'czy', 'nie', 'tylko', 'już', 'jeszcze', 'bardzo', 'też', 'także'
    }

    def extract_keywords(self, text: str, top_k: int = KEYWORDS_TOP_K) -> List[str]:
        """
        Extract top-K keywords from text using simple frequency analysis

        Args:
            text: Text to extract keywords from
            top_k: Number of keywords to extract

        Returns:
            List of top keywords
        """
        # Tokenize and clean
        words = re.findall(r'\b[a-ząćęłńóśźż]{3,}\b', text.lower())

        # Filter stopwords
        words = [w for w in words if w not in self.STOPWORDS]

        # Count frequencies
        word_counts = Counter(words)

        # Get top-K
        keywords = [word for word, count in word_counts.most_common(top_k)]

        return keywords

    def generate_chunk_summary(self, text: str) -> str:
        """
        Generate a brief summary of the chunk

        Args:
            text: Chunk text

        Returns:
            Summary text (first sentence or truncated)
        """
        # Remove page headers and image markers
        clean_text = re.sub(r'##\s+Strona\s+\d+', '', text)
        clean_text = re.sub(r'!\[.*?\]\(.*?\)', '', clean_text)
        clean_text = clean_text.strip()

        # Try to get first sentence
        sentences = re.split(r'[.!?]\s+', clean_text)
        if sentences and len(sentences[0]) > 10:
            summary = sentences[0]
        else:
            summary = clean_text

        # Truncate if too long
        if len(summary) > SUMMARY_MAX_LENGTH:
            summary = summary[:SUMMARY_MAX_LENGTH].rsplit(' ', 1)[0] + '...'

        return summary

    def enrich_chunks(self, chunks: List[Dict], doc_context: Dict) -> List[Dict]:
        """
        Enrich all chunks with contextual metadata

        Args:
            chunks: List of chunk dictionaries
            doc_context: Document-level context (title, protocol_number, etc.)

        Returns:
            Enriched chunks with additional metadata
        """
        enriched_chunks = []

        for i, chunk in enumerate(chunks):
            # Extract keywords from chunk text
            keywords = self.extract_keywords(chunk['text'])

            # Generate summary
            summary = self.generate_chunk_summary(chunk['text'])

            # Add navigation references
            prev_chunk_idx = i - 1 if i > 0 else None
            next_chunk_idx = i + 1 if i < len(chunks) - 1 else None

            # Enrich chunk
            enriched_chunk = chunk.copy()
            enriched_chunk.update({
                'keywords': keywords,
                'summary': summary,
                'prev_chunk_idx': prev_chunk_idx,
                'next_chunk_idx': next_chunk_idx,
                'doc_title': doc_context.get('source_title', ''),
                'doc_protocol_number': doc_context.get('protocol_number', 0),
                'doc_date_range': doc_context.get('date_range', '')
            })

            enriched_chunks.append(enriched_chunk)

        return enriched_chunks

    def format_context_for_display(self, chunk: Dict) -> str:
        """
        Format chunk context for user display

        Args:
            chunk: Enriched chunk dictionary

        Returns:
            Formatted context string
        """
        parts = []

        # Protocol info
        if chunk.get('doc_protocol_number'):
            parts.append(f"Protokół {chunk['doc_protocol_number']}")

        # Section header
        if chunk.get('section_header'):
            parts.append(chunk['section_header'])

        # Page number
        if chunk.get('page_number'):
            parts.append(f"Strona {chunk['page_number']}")

        context_str = "[" + ", ".join(parts) + "]" if parts else ""

        return context_str

    def format_keywords_for_display(self, chunk: Dict) -> str:
        """
        Format keywords for display

        Args:
            chunk: Enriched chunk dictionary

        Returns:
            Formatted keywords string
        """
        keywords = chunk.get('keywords', [])
        if keywords:
            return "Słowa kluczowe: " + ", ".join(keywords)
        return ""
