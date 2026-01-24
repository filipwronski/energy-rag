"""OpenRouter API client for embeddings and LLM calls"""

import os
import time
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()


class OpenRouterClient:
    """Client for OpenRouter API with retry logic and rate limiting"""

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenRouter client

        Args:
            api_key: OpenRouter API key (reads from OPEN_ROUTER_API_KEY env var if not provided)
        """
        self.api_key = api_key or os.getenv("OPEN_ROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPEN_ROUTER_API_KEY not found in environment")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/fwronski/energy-rag",
            "X-Title": "Energy RAG System",
            "Content-Type": "application/json"
        }

    def _call_api(self, endpoint: str, payload: Dict,
                  max_retries: int = 3, timeout: int = 30) -> Dict:
        """
        Make API call with retry logic and error handling

        Args:
            endpoint: API endpoint path (e.g., "embeddings", "chat/completions")
            payload: Request payload dictionary
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds

        Returns:
            API response as dictionary

        Raises:
            Exception: If all retries fail or non-retryable error occurs
        """
        url = f"{self.BASE_URL}/{endpoint}"

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers=self.headers,
                    timeout=timeout
                )
                response.raise_for_status()
                return response.json()

            except requests.exceptions.Timeout:
                if attempt == max_retries - 1:
                    raise Exception(f"Request timeout after {max_retries} attempts")
                wait_time = 2 ** attempt
                print(f"Timeout. Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)

            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code

                # Rate limiting (429) - wait and retry
                if status_code == 429:
                    retry_after = int(e.response.headers.get("Retry-After", 5))
                    print(f"Rate limited. Waiting {retry_after}s...")
                    time.sleep(retry_after)
                    continue

                # Server errors (5xx) - retry with backoff
                elif 500 <= status_code < 600:
                    if attempt == max_retries - 1:
                        raise Exception(f"Server error {status_code} after {max_retries} attempts: {e.response.text}")
                    wait_time = 2 ** attempt
                    print(f"Server error {status_code}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                # Client errors (4xx) - don't retry
                else:
                    raise Exception(f"API error {status_code}: {e.response.text}")

            except Exception as e:
                if attempt == max_retries - 1:
                    raise Exception(f"API call failed: {str(e)}")
                wait_time = 2 ** attempt
                print(f"Error: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)

        raise Exception(f"Failed after {max_retries} attempts")

    def get_embedding(self, text: str, model: str = "openai/text-embedding-3-small") -> List[float]:
        """
        Get embedding for a single text

        Args:
            text: Input text to embed
            model: Embedding model name

        Returns:
            Embedding vector (1536 dimensions for text-embedding-3-small)
        """
        payload = {
            "model": model,
            "input": text
        }

        response = self._call_api("embeddings", payload)
        return response["data"][0]["embedding"]

    def get_embeddings_batch(self, texts: List[str],
                            model: str = "openai/text-embedding-3-small",
                            batch_size: int = 100) -> List[List[float]]:
        """
        Get embeddings for multiple texts in batches

        Args:
            texts: List of input texts to embed
            model: Embedding model name
            batch_size: Number of texts to process per API call

        Returns:
            List of embedding vectors
        """
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            payload = {
                "model": model,
                "input": batch
            }

            response = self._call_api("embeddings", payload)
            batch_embeddings = [item["embedding"] for item in response["data"]]
            all_embeddings.extend(batch_embeddings)

            # Small delay between batches to avoid rate limiting
            if i + batch_size < len(texts):
                time.sleep(0.5)

        return all_embeddings

    def generate_query_variants(self, query: str, num_variants: int = 2) -> List[str]:
        """
        Generate paraphrased query variants using GPT-4o-mini

        Args:
            query: Original search query
            num_variants: Number of paraphrased variants to generate (2-3 recommended)

        Returns:
            List of paraphrased queries in Polish
        """
        prompt = f"""Jesteś ekspertem w przeformułowywaniu zapytań wyszukiwania dla systemu RAG.

Oryginalne zapytanie: "{query}"

Wygeneruj {num_variants} różne warianty tego zapytania w języku polskim. Każdy wariant powinien:
- Zachować oryginalny sens i intencję zapytania
- Używać synonimów, różnych form gramatycznych lub odmiennego układu słów
- Być naturalny w języku polskim
- Być krótki (max 2-3 zdania)

Zwróć TYLKO warianty, każdy w nowej linii, bez numeracji i dodatkowych wyjaśnień."""

        payload = {
            "model": "openai/gpt-4o-mini",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 200
        }

        response = self._call_api("chat/completions", payload)
        content = response["choices"][0]["message"]["content"].strip()

        # Parse variants (one per line)
        variants = [line.strip() for line in content.split('\n') if line.strip()]

        # Ensure we return exactly num_variants (take first N)
        return variants[:num_variants]
