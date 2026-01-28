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

# Chunking parameters (optimized for better precision)
MAX_CHUNK_SIZE = 512  # Updated from 1000 to 512 characters
CHUNK_OVERLAP = 50    # Updated from 100 to 50 characters

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
