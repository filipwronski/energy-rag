"""Unit tests for chunker module"""

import pytest
from rag.chunker import extract_h1_title, extract_protocol_number, extract_date_range


class TestExtractH1Title:
    """Test extract_h1_title function"""

    def test_standard_h1_single_hash(self):
        """Test extraction of standard H1 with single hash"""
        content = "# Protokół nr 3 z ustaleń\nContent here"
        result = extract_h1_title(content)
        assert result == "Protokół nr 3 z ustaleń"

    def test_multiple_hashes(self):
        """Test extraction with multiple hashes"""
        content = "### Protokół nr 5 z zebrania\nMore content"
        result = extract_h1_title(content)
        assert result == "Protokół nr 5 z zebrania"

    def test_empty_content(self):
        """Test extraction from empty content"""
        content = ""
        result = extract_h1_title(content)
        assert result == ""

    def test_no_h1_marker(self):
        """Test extraction when no H1 marker present"""
        content = "Plain text without hash\nSecond line"
        result = extract_h1_title(content)
        assert result == "Plain text without hash"


class TestExtractProtocolNumber:
    """Test extract_protocol_number function"""

    def test_standard_format(self):
        """Test extraction of protocol number in standard format"""
        title = "Protokół nr 3 z ustaleń"
        result = extract_protocol_number(title)
        assert result == 3

    def test_no_number_found(self):
        """Test when no number is found"""
        title = "Protokół z zebrania"
        result = extract_protocol_number(title)
        assert result == 0

    def test_case_insensitive(self):
        """Test case insensitive matching (Nr vs nr)"""
        title = "Protokół Nr 42 z posiedzenia"
        result = extract_protocol_number(title)
        assert result == 42

    def test_multiple_spaces(self):
        """Test extraction with multiple spaces"""
        title = "Protokół nr    15 z komisji"
        result = extract_protocol_number(title)
        assert result == 15


class TestExtractDateRange:
    """Test extract_date_range function"""

    def test_valid_date_range(self):
        """Test extraction of valid date range"""
        title = "Protokół nr 3 z ustaleń 29.01. - 11.02.2025"
        result = extract_date_range(title)
        assert result == "29.01. - 11.02.2025"

    def test_no_date_range(self):
        """Test when no date range is present"""
        title = "Protokół nr 5 z zebrania"
        result = extract_date_range(title)
        assert result == ""

    def test_different_spacing(self):
        """Test date range with different spacing"""
        title = "Spotkanie 15.03.-20.03.2025 z zarządem"
        result = extract_date_range(title)
        assert result == "15.03.-20.03.2025"
