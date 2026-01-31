"""Unit tests for download_pdfs script"""

import pytest
import unicodedata
import re
import urllib.parse
import os


def sanitize_filename(filename: str, max_length: int = 200) -> str:
    """
    Creates a safe filename by removing/replacing problematic characters.

    Args:
        filename: Original filename
        max_length: Maximum length for the filename (default: 200)

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

    # Truncate if too long
    if len(safe_string) > max_length:
        safe_string = safe_string[:max_length].rstrip('_')

    return safe_string


def extract_filename_from_url(url: str) -> str:
    """
    Extracts filename from URL path.

    Args:
        url: The URL to extract filename from

    Returns:
        Filename without extension, or empty string if not found
    """
    try:
        parsed = urllib.parse.urlparse(url)
        path = parsed.path
        # Get the last part of the path
        filename = os.path.basename(path)
        # Remove .pdf extension if present
        if filename.lower().endswith('.pdf'):
            filename = filename[:-4]
        return filename
    except Exception:
        return ""


class TestExtractFilenameFromUrl:
    """Test extract_filename_from_url function"""

    def test_simple_url(self):
        """Test extracting filename from simple URL"""
        url = "https://example.com/document.pdf"
        result = extract_filename_from_url(url)
        assert result == "document"

    def test_url_with_path(self):
        """Test extracting filename from URL with path"""
        url = "https://example.com/files/reports/annual-report-2024.pdf"
        result = extract_filename_from_url(url)
        assert result == "annual-report-2024"

    def test_url_with_query_params(self):
        """Test extracting filename from URL with query parameters"""
        url = "https://example.com/download.pdf?id=123&token=abc"
        result = extract_filename_from_url(url)
        assert result == "download"

    def test_url_without_pdf_extension(self):
        """Test URL without .pdf extension"""
        url = "https://example.com/document"
        result = extract_filename_from_url(url)
        assert result == "document"

    def test_empty_url(self):
        """Test empty URL returns empty string"""
        url = ""
        result = extract_filename_from_url(url)
        assert result == ""

    def test_url_with_encoded_characters(self):
        """Test URL with percent-encoded characters"""
        url = "https://example.com/my%20document.pdf"
        result = extract_filename_from_url(url)
        assert result == "my%20document"


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

    def test_long_filename_truncation(self):
        """Test that long filenames are truncated to max_length"""
        # Create a very long filename
        long_filename = "a" * 250 + ".pdf"
        result = sanitize_filename(long_filename, max_length=200)
        # Should be truncated to 200 characters
        assert len(result) <= 200
        # Should not end with underscore
        assert not result.endswith('_')

    def test_long_filename_with_description(self):
        """Test realistic case with long combined filename and description"""
        filename = "Very_Long_Filename_With_Many_Words_And_Details_About_Energy_Regulation"
        description = "Additional_Description_With_More_Information_About_The_Document_Contents_And_Metadata"
        combined = f"{filename} - {description}"
        result = sanitize_filename(combined, max_length=200)
        # Should be truncated
        assert len(result) <= 200
        # Should still be a valid string
        assert len(result) > 0
