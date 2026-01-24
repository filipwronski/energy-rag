"""Hybrid query expansion combining LLM and rule-based methods"""

import re
from typing import List, Dict


class QueryExpander:
    """
    Hybrid query expansion using LLM paraphrasing and rule-based transformations
    """

    # Polish synonyms dictionary (extensible)
    SYNONYMS = {
        "protokół": ["protokół", "uchwała", "dokument", "zapis"],
        "zarząd": ["zarząd", "kierownictwo", "dyrekcja"],
        "pracownik": ["pracownik", "zatrudniony", "personel", "kadra"],
        "budowa": ["budowa", "konstrukcja", "montaż", "wzniesienie"],
        "remont": ["remont", "naprawa", "modernizacja", "odnowa"],
        "inwestycja": ["inwestycja", "nakład", "wydatek kapitałowy"],
        "komisja": ["komisja", "zespół", "grupa robocza"],
        "przetarg": ["przetarg", "konkurs", "postępowanie przetargowe"],
        "umowa": ["umowa", "kontrakt", "porozumienie", "ugoda"],
        "koszt": ["koszt", "wydatek", "nakład finansowy", "kwota"],
        "sprawa": ["sprawa", "kwestia", "zagadnienie"],
        "posiedzenie": ["posiedzenie", "spotkanie", "zebranie"],
        "decyzja": ["decyzja", "postanowienie", "rozstrzygnięcie"],
        "wniosek": ["wniosek", "propozycja", "sugestia"],
        "wymiana": ["wymiana", "zamiana", "podmiana"],
        "naprawa": ["naprawa", "reperacja", "odnowienie"],
        "zgoda": ["zgoda", "akceptacja", "przyzwolenie"],
        "wybór": ["wybór", "selekcja", "wyłonienie"]
    }

    def __init__(self, openrouter_client):
        """
        Initialize query expander

        Args:
            openrouter_client: OpenRouterClient instance for LLM-based expansion
        """
        self.client = openrouter_client

    def expand_with_synonyms(self, query: str) -> str:
        """
        Generate query variant by replacing words with synonyms

        Args:
            query: Original query text

        Returns:
            Query variant with synonym substitutions
        """
        words = query.lower().split()
        expanded_words = []

        for word in words:
            # Clean punctuation
            clean_word = re.sub(r'[^\w\s]', '', word)

            # Find synonyms
            replaced = False
            for key, synonyms in self.SYNONYMS.items():
                if clean_word in synonyms and key != clean_word:
                    # Use a different synonym from the list
                    for syn in synonyms:
                        if syn != clean_word:
                            expanded_words.append(syn)
                            replaced = True
                            break
                    break

            if not replaced:
                expanded_words.append(word)

        return " ".join(expanded_words)

    def expand_with_word_order(self, query: str) -> str:
        """
        Generate query variant by reordering words

        Args:
            query: Original query text

        Returns:
            Query variant with reordered words
        """
        # Split by common Polish conjunctions and prepositions
        parts = re.split(r'(\s+(?:i|oraz|w|z|o|na|do|dla|przez|pod|nad)\s+)', query, flags=re.IGNORECASE)

        # If we have multiple parts, try reversing main parts
        if len(parts) > 1:
            # Separate main parts from separators
            main_parts = [parts[i] for i in range(0, len(parts), 2)]
            separators = [parts[i] for i in range(1, len(parts), 2)]

            if len(main_parts) > 1:
                main_parts.reverse()

                # Reconstruct with separators
                result = []
                for i, part in enumerate(main_parts):
                    result.append(part)
                    if i < len(separators):
                        result.append(separators[i])

                return "".join(result)

        # Fallback: simple word reversal for short queries
        words = query.split()
        if len(words) > 2:
            return " ".join(reversed(words))

        return query

    def expand_hybrid(self, query: str, num_variants: int = 5) -> List[Dict[str, str]]:
        """
        Generate hybrid query variants combining LLM and rule-based methods

        Args:
            query: Original search query
            num_variants: Total number of variants to generate (default: 5)

        Returns:
            List of variant dictionaries with 'text' and 'method' keys
        """
        variants = []

        # 1. Original query (always included)
        variants.append({
            "text": query,
            "method": "original"
        })

        # 2. LLM-based variants (2-3)
        num_llm = min(2, num_variants - 1)  # At least keep 1 slot for rule-based
        try:
            llm_variants = self.client.generate_query_variants(query, num_variants=num_llm)
            for variant in llm_variants:
                if variant and variant != query:  # Skip empty or duplicate
                    variants.append({
                        "text": variant,
                        "method": "llm"
                    })
        except Exception as e:
            print(f"Warning: LLM expansion failed: {e}")
            # Continue with rule-based only

        # 3. Rule-based variants
        # Synonym variant
        if len(variants) < num_variants:
            synonym_variant = self.expand_with_synonyms(query)
            if synonym_variant != query and synonym_variant not in [v["text"] for v in variants]:
                variants.append({
                    "text": synonym_variant,
                    "method": "synonym"
                })

        # Word order variant
        if len(variants) < num_variants:
            word_order_variant = self.expand_with_word_order(query)
            if word_order_variant != query and word_order_variant not in [v["text"] for v in variants]:
                variants.append({
                    "text": word_order_variant,
                    "method": "word_order"
                })

        # 4. Pad with original query if we don't have enough variants
        while len(variants) < num_variants:
            variants.append({
                "text": query,
                "method": "duplicate_original"
            })

        return variants[:num_variants]
