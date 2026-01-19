"""RAG system configuration"""

# Qdrant settings
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "energy_protocols"

# Embedding model
EMBEDDING_MODEL = "sdadas/mmlw-retrieval-roberta-base"
EMBEDDING_DIM = 768

# Chunking parameters
MAX_CHUNK_SIZE = 1000  # characters
CHUNK_OVERLAP = 100    # characters

# Search parameters
DEFAULT_TOP_K = 5
MIN_SCORE_THRESHOLD = 0.5  # Filter low-confidence results

# Paths
OUTPUT_DIR = "output"
