"""Markdown document chunking with header-aware splitting"""

import re
from pathlib import Path
from typing import List, Dict
from .config import MAX_CHUNK_SIZE, CHUNK_OVERLAP, OUTPUT_DIR, USE_SEMANTIC_CHUNKING, ENABLE_CONTEXT_ENRICHMENT
from .semantic_chunker import SemanticChunker
from .context_enricher import ContextEnricher


def extract_h1_title(content: str) -> str:
    """
    Extract H1 title from first line

    Args:
        content: Full markdown content

    Returns:
        Title text without '#' prefix
    """
    first_line = content.split('\n')[0]
    return first_line.lstrip('#').strip()


def extract_protocol_number(title: str) -> int:
    """
    Extract protocol number from title

    Args:
        title: Protocol title (e.g., "Protokół nr 3 z ustaleń...")

    Returns:
        Protocol number or 0 if not found
    """
    match = re.search(r'nr\s+(\d+)', title, re.IGNORECASE)
    return int(match.group(1)) if match else 0


def extract_date_range(title: str) -> str:
    """
    Extract date range from title

    Args:
        title: Protocol title

    Returns:
        Date range string (e.g., "29.01. - 11.02.2025") or empty string
    """
    match = re.search(r'(\d{2}\.\d{2}\.\s*-\s*\d{2}\.\d{2}\.\d{4})', title)
    return match.group(1) if match else ""


def split_by_pages(content: str) -> List[tuple]:
    """
    Split content by '## Strona X' headers

    Args:
        content: Full markdown content

    Returns:
        List of tuples (page_number, page_content)
    """
    page_pattern = r'##\s+Strona\s+(\d+)'
    pages = []

    matches = list(re.finditer(page_pattern, content))

    for i, match in enumerate(matches):
        page_num = int(match.group(1))
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        page_content = content[start:end].strip()
        pages.append((page_num, page_content))

    return pages


def chunk_long_section(text: str, max_size: int, overlap: int) -> List[str]:
    """
    Split long sections with overlap

    Args:
        text: Text to split
        max_size: Maximum chunk size in characters
        overlap: Overlap size in characters

    Returns:
        List of text chunks
    """
    if len(text) <= max_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + max_size, len(text))

        # Try to break at sentence or paragraph boundary
        if end < len(text):
            # Look for last sentence break
            for sep in ['\n\n', '. ', '\n']:
                last_sep = text[start:end].rfind(sep)
                if last_sep > max_size // 2:  # Don't break too early
                    end = start + last_sep + len(sep)
                    break

        chunks.append(text[start:end].strip())
        start = end - overlap if end < len(text) else end

    return chunks


def chunk_document(filepath: Path) -> List[Dict]:
    """
    Chunk a single markdown document

    Args:
        filepath: Path to markdown file

    Returns:
        List of chunk dictionaries with metadata
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract metadata
    source_title = extract_h1_title(content)
    protocol_number = extract_protocol_number(source_title)
    date_range = extract_date_range(source_title)

    # Split by pages
    pages = split_by_pages(content)

    # Create chunks
    all_chunks = []
    chunk_index = 0

    # Initialize semantic chunker if enabled
    semantic_chunker = SemanticChunker() if USE_SEMANTIC_CHUNKING else None

    for page_num, page_content in pages:
        # Skip pages with no recognized text
        if "*[Brak rozpoznanego tekstu]*" in page_content:
            continue

        # Skip pages that are too short (less than 50 chars of actual content)
        # This filters out pages with only headers and image markers
        text_without_header = page_content.split('\n', 2)[-1] if '\n' in page_content else page_content
        if len(text_without_header.strip()) < 50:
            continue

        # Use semantic chunking or fallback to old method
        if USE_SEMANTIC_CHUNKING and semantic_chunker:
            semantic_sections = semantic_chunker.chunk_page(page_content, page_num)

            for section in semantic_sections:
                chunk = {
                    "text": section['text'],
                    "source_file": filepath.name,
                    "source_title": source_title,
                    "page_number": page_num,
                    "chunk_index": chunk_index,
                    "protocol_number": protocol_number,
                    "date_range": date_range,
                    "section_header": section.get('header', ''),
                    "chunk_type": section.get('type', 'unknown')
                }
                all_chunks.append(chunk)
                chunk_index += 1
        else:
            # Fallback to old chunking method
            sections = chunk_long_section(page_content, MAX_CHUNK_SIZE, CHUNK_OVERLAP)

            for section in sections:
                chunk = {
                    "text": section,
                    "source_file": filepath.name,
                    "source_title": source_title,
                    "page_number": page_num,
                    "chunk_index": chunk_index,
                    "protocol_number": protocol_number,
                    "date_range": date_range
                }
                all_chunks.append(chunk)
                chunk_index += 1

    # Add total_chunks to all chunks
    for chunk in all_chunks:
        chunk["total_chunks"] = len(all_chunks)

    # Apply contextual enrichment if enabled
    if ENABLE_CONTEXT_ENRICHMENT and all_chunks:
        enricher = ContextEnricher()
        doc_context = {
            'source_title': source_title,
            'protocol_number': protocol_number,
            'date_range': date_range
        }
        all_chunks = enricher.enrich_chunks(all_chunks, doc_context)

    return all_chunks


def chunk_all_documents(output_dir: Path = None) -> List[Dict]:
    """
    Chunk all markdown documents in output directory

    Args:
        output_dir: Path to output directory (defaults to OUTPUT_DIR from config)

    Returns:
        List of all chunks from all documents
    """
    if output_dir is None:
        output_dir = Path(OUTPUT_DIR)

    all_chunks = []
    md_files = list(output_dir.glob("*.md"))

    print(f"Chunking {len(md_files)} documents...")

    for filepath in md_files:
        chunks = chunk_document(filepath)
        all_chunks.extend(chunks)
        print(f"  ✓ {filepath.name}: {len(chunks)} chunks")

    print(f"✓ Total: {len(all_chunks)} chunks")
    return all_chunks
