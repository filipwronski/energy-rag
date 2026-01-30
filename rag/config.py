"""RAG system configuration"""

import os
from dotenv import load_dotenv

load_dotenv()

# Qdrant settings
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = "energy_protocols"

# Embedding settings (migrated to OpenRouter)
EMBEDDING_MODEL = "openai/text-embedding-3-small"
EMBEDDING_DIM = 1536  # Updated from 768 to 1536

# Chunking parameters (optimized for cost efficiency)
MAX_CHUNK_SIZE = 1024  # Maximum chunk size in characters (2x increase)
CHUNK_OVERLAP = 100    # Overlap between chunks in characters (2x increase for better context continuity)

# Query expansion settings
NUM_QUERY_VARIANTS = 5  # Total number of query variants to generate
NUM_LLM_VARIANTS = 2    # Number of LLM-based paraphrases
NUM_RULE_VARIANTS = 2   # Number of rule-based variants (including original)

# RRF settings
RRF_K = 60              # Standard RRF constant from literature
RESULTS_PER_VARIANT = 10  # Results to fetch per query variant before fusion

# Search parameters
DEFAULT_TOP_K = 20  # Maximum final results after RRF fusion
MIN_SCORE_THRESHOLD = 0.5  # Filter low-confidence results (for vector similarity)
MIN_RRF_SCORE = 0.04  # Minimum RRF score to include result (filters weak matches)

# Cache settings
ENABLE_CACHE = True
CACHE_DB_PATH = os.getenv("CACHE_DB_PATH", "embedding_cache.db")

# OpenRouter API
OPEN_ROUTER_API_KEY = os.getenv("OPEN_ROUTER_API_KEY")

# Paths
OUTPUT_DIR = "output"

# === RAG IMPROVEMENTS CONFIGURATION ===

# Query expansion enhancements (#4)
USE_LEMMATIZATION = True
USE_ABBREVIATION_EXPANSION = True
USE_ENTITY_EXTRACTION = False  # Optional, can be enabled for debugging

# Semantic chunking (#1)
USE_SEMANTIC_CHUNKING = True
MIN_CHUNK_SIZE = 450  # Minimum semantic chunk size (more aggressive merging of small sections)

# Contextual enrichment (#5)
ENABLE_CONTEXT_ENRICHMENT = True
KEYWORDS_TOP_K = 5
SUMMARY_MAX_LENGTH = 100

# Cross-encoder reranking (#3)
ENABLE_RERANKING = True
RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"
RERANKER_DEVICE = "cpu"  # or "cuda" if GPU available
RERANKING_CANDIDATES = 50
