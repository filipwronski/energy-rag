"""Unit tests for download_pdfs script"""

import pytest
import unicodedata
import re


def sanitize_filename(filename: str) -> str:
    """
    Creates a safe filename by removing/replacing problematic characters.

    Args:
        filename: Original filename

    Returns:
        Safe filename
    """
    # Normalize unicode (convert accented characters to base characters)
    # NFD = Normalization Form Canonical Decomposition
    nfkd_form = unicodedata.normalize('NFKD', filename)

    # Keep only ASCII characters
    ascii_string = nfkd_form.encode('ASCII', 'ignore').decode('ASCII')

    # Replace remaining problematic characters
    safe_string = re.sub(r'[<>:"/\\|?*]', '_', ascii_string)

    # Remove multiple underscores and spaces
    safe_string = re.sub(r'[_\s]+', '_', safe_string)

    # Remove underscores at the beginning and end
    safe_string = safe_string.strip('_')

    return safe_string


class TestSanitizeFilename:
    """Test sanitize_filename function"""

    def test_remove_special_characters(self):
        """Test removal of special characters from filename"""
        filename = "file<name>:with*special|chars?.pdf"
        result = sanitize_filename(filename)
        # Should replace special characters with underscores
        assert '<' not in result
        assert '>' not in result
        assert ':' not in result
        assert '*' not in result
        assert '|' not in result
        assert '?' not in result
        # Result should be safe
        assert result == "file_name_with_special_chars_.pdf"

    def test_handle_unicode_accents(self):
        """Test handling of unicode characters and accents"""
        filename = "Protokół_ząbądź.pdf"
        result = sanitize_filename(filename)
        # Should normalize unicode to ASCII
        # Polish characters should be converted or removed
        # Note: "ł" is removed completely as it has no ASCII equivalent
        assert result == "Protoko_zabadz.pdf"

    def test_multiple_spaces_underscores(self):
        """Test removal of multiple consecutive spaces/underscores"""
        filename = "file___name   with    spaces.pdf"
        result = sanitize_filename(filename)
        # Should collapse multiple underscores/spaces into single underscore
        assert result == "file_name_with_spaces.pdf"

    def test_empty_string(self):
        """Test handling of empty string"""
        filename = ""
        result = sanitize_filename(filename)
        assert result == ""

    def test_already_clean_filename(self):
        """Test that already clean filename remains unchanged"""
        filename = "clean_filename_123.pdf"
        result = sanitize_filename(filename)
        assert result == filename
