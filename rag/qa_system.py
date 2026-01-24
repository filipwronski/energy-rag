#!/usr/bin/env python3
"""Question Answering system using RAG + LLM"""

import os
import requests
from typing import List, Dict, Any
from .enhanced_retriever import EnhancedProtocolRetriever
from .config import OPEN_ROUTER_API_KEY


class ProtocolQASystem:
    """Question Answering system for protocol documents"""

    def __init__(self, model: str = "deepseek/deepseek-chat"):
        """
        Initialize QA system

        Args:
            model: LLM model to use for answer generation (default: DeepSeek V3.2)
        """
        self.retriever = EnhancedProtocolRetriever()
        self.model = model
        self.api_key = OPEN_ROUTER_API_KEY

        if not self.api_key:
            raise ValueError("OPEN_ROUTER_API_KEY not found in environment")

    def _format_context(self, results: List[Dict[str, Any]]) -> str:
        """
        Format search results as context for LLM

        Args:
            results: List of search results

        Returns:
            Formatted context string
        """
        context_parts = []

        for idx, result in enumerate(results, 1):
            context_parts.append(
                f"[Dokument {idx}]\n"
                f"Protokół nr {result['protocol_number']}, Strona {result['page']}\n"
                f"Data: {result['date_range']}\n"
                f"Źródło: {result['source']}\n"
                f"Treść: {result['text']}\n"
            )

        return "\n---\n\n".join(context_parts)

    def _generate_answer(self, question: str, context: str) -> str:
        """
        Generate answer using LLM

        Args:
            question: User's question
            context: Retrieved context

        Returns:
            Generated answer
        """
        system_prompt = """Jesteś asystentem pomagającym w analizie protokołów Zarządu MSM Energetyka.
Twoim zadaniem jest udzielanie precyzyjnych odpowiedzi na podstawie dostarczonych dokumentów.

Zasady:
1. Odpowiadaj TYLKO na podstawie dostarczonych dokumentów
2. Jeśli informacja nie znajduje się w dokumentach, powiedz to wprost
3. Cytuj konkretne numery protokołów i daty
4. Odpowiadaj w języku polskim
5. Strukturyzuj odpowiedź w punktach gdy jest wiele informacji
6. Podawaj źródła (numer protokołu, stronę) dla każdej informacji"""

        user_prompt = f"""Pytanie użytkownika: {question}

Dostępne dokumenty:
{context}

Udziel odpowiedzi na pytanie użytkownika na podstawie powyższych dokumentów."""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,  # Lower temperature for more factual responses
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        response.raise_for_status()

        result = response.json()
        return result["choices"][0]["message"]["content"]

    def ask(self, question: str, top_k: int = 20, verbose: bool = False) -> Dict[str, Any]:
        """
        Answer a question using RAG + LLM

        Args:
            question: User's question
            top_k: Number of documents to retrieve
            verbose: Show detailed information

        Returns:
            Dictionary containing:
                - answer: Generated answer
                - sources: List of source documents
                - search_metadata: Search metadata
        """
        # Retrieve relevant documents
        if verbose:
            print(f"🔍 Szukam informacji w {top_k} dokumentach...")

        search_response = self.retriever.search(question, top_k=top_k, verbose=False)
        results = search_response["results"]

        if not results:
            return {
                "answer": "Nie znaleziono żadnych dokumentów odpowiadających na to pytanie.",
                "sources": [],
                "search_metadata": search_response
            }

        if verbose:
            print(f"✓ Znaleziono {len(results)} dokumentów")
            print("🤖 Generuję odpowiedź...")

        # Format context and generate answer
        context = self._format_context(results)
        answer = self._generate_answer(question, context)

        if verbose:
            print("✓ Odpowiedź wygenerowana\n")

        return {
            "answer": answer,
            "sources": results,
            "search_metadata": search_response
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        return self.retriever.get_stats()
