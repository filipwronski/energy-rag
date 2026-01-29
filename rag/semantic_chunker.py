"""Semantic chunking that respects document structure and hierarchy"""

import re
from typing import List, Dict, Tuple
from .config import MAX_CHUNK_SIZE, MIN_CHUNK_SIZE, CHUNK_OVERLAP


class SemanticChunker:
    """
    Semantic chunking that respects document structure:
    - Page headers (## Strona X)
    - Section headers (### headings)
    - Agenda items (**Punkt X.**)
    - Paragraphs and natural breaks
    """

    def extract_sections(self, page_content: str) -> List[Dict[str, str]]:
        """
        Parse page content into semantic sections

        Args:
            page_content: Content of a single page

        Returns:
            List of section dictionaries with text and metadata
        """
        sections = []

        # Extract page header
        lines = page_content.split('\n')
        page_header = lines[0] if lines and lines[0].startswith('##') else None

        # Split by different header types (priority order)
        # 1. ### Level 3 headers (main sections)
        # 2. **Punkt X.** style items
        # 3. Paragraph breaks (\n\n)

        current_section = {
            'header': page_header,
            'text': '',
            'type': 'page'
        }

        i = 1 if page_header else 0

        while i < len(lines):
            line = lines[i]

            # Check for ### headers (section headers)
            if line.startswith('###'):
                # Save previous section if it has content
                if current_section['text'].strip():
                    sections.append(current_section)

                # Start new section
                current_section = {
                    'header': line.lstrip('#').strip(),
                    'text': '',
                    'type': 'section'
                }

            # Check for **Punkt X.** style items
            elif re.match(r'\*\*Punkt\s+\d+\.?\*\*', line):
                # Save previous section if it has content
                if current_section['text'].strip():
                    sections.append(current_section)

                # Start new agenda item section
                punkt_match = re.match(r'\*\*(Punkt\s+\d+\.?)\*\*\s*(.*)', line)
                current_section = {
                    'header': punkt_match.group(1) if punkt_match else line.strip('*'),
                    'text': punkt_match.group(2) if punkt_match else '',
                    'type': 'agenda_item'
                }

            else:
                # Add line to current section
                current_section['text'] += line + '\n'

            i += 1

        # Add last section
        if current_section['text'].strip():
            sections.append(current_section)

        return sections

    def merge_small_sections(self, sections: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Merge sections smaller than MIN_CHUNK_SIZE with adjacent sections

        Args:
            sections: List of section dictionaries

        Returns:
            List of merged sections
        """
        if not sections:
            return []

        merged = []
        i = 0

        while i < len(sections):
            current = sections[i]
            current_size = len(current['text'])

            # If section is too small and not the last one, try to merge with next
            if current_size < MIN_CHUNK_SIZE and i + 1 < len(sections):
                next_section = sections[i + 1]

                # Merge with next section
                merged_text = current['text'] + '\n' + next_section['text']
                merged_header = current['header'] or next_section['header']

                merged.append({
                    'header': merged_header,
                    'text': merged_text,
                    'type': current['type']
                })

                i += 2  # Skip next section since we merged it
            else:
                merged.append(current)
                i += 1

        return merged

    def split_large_section(self, section: Dict[str, str]) -> List[Dict[str, str]]:
        """
        Intelligently split sections larger than MAX_CHUNK_SIZE

        Args:
            section: Section dictionary to split

        Returns:
            List of split section dictionaries
        """
        text = section['text']

        if len(text) <= MAX_CHUNK_SIZE:
            return [section]

        chunks = []
        start = 0

        while start < len(text):
            end = min(start + MAX_CHUNK_SIZE, len(text))

            # Try to break at natural boundaries
            if end < len(text):
                # Look for paragraph break first
                last_para = text[start:end].rfind('\n\n')
                if last_para > MAX_CHUNK_SIZE // 2:
                    end = start + last_para + 2
                else:
                    # Look for sentence break
                    last_sentence = text[start:end].rfind('. ')
                    if last_sentence > MAX_CHUNK_SIZE // 2:
                        end = start + last_sentence + 2
                    else:
                        # Look for any newline
                        last_newline = text[start:end].rfind('\n')
                        if last_newline > MAX_CHUNK_SIZE // 2:
                            end = start + last_newline + 1

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append({
                    'header': section['header'],
                    'text': chunk_text,
                    'type': section['type']
                })

            # Move start with overlap
            start = end - CHUNK_OVERLAP if end < len(text) else end

        return chunks

    def chunk_page(self, page_content: str, page_num: int) -> List[Dict[str, str]]:
        """
        Main entry point for semantic chunking of a single page

        Args:
            page_content: Content of the page
            page_num: Page number

        Returns:
            List of semantically chunked sections with metadata
        """
        # 1. Extract sections based on document structure
        sections = self.extract_sections(page_content)

        # 2. Merge small sections
        sections = self.merge_small_sections(sections)

        # 3. Split large sections
        final_chunks = []
        for section in sections:
            split_sections = self.split_large_section(section)
            final_chunks.extend(split_sections)

        # 4. Add page number to metadata
        for chunk in final_chunks:
            chunk['page_number'] = page_num

        return final_chunks
