#!/usr/bin/env python3
"""
Script for downloading PDF files from CSV file with URLs
"""

import csv
import os
import urllib.request
import urllib.parse
from pathlib import Path
import unicodedata
import re


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


def download_pdfs(csv_file: str = "input/urls.csv", output_dir: str = "input"):
    """
    Downloads all PDF files from CSV file with URLs.

    Args:
        csv_file: Path to the CSV file with URLs (columns: url, filename)
        output_dir: Target directory for downloaded files
    """
    # Read CSV file
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        data = list(reader)

    # Ensure the target directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Counters
    total = len(data)
    downloaded = 0
    errors = 0

    print(f"Found {total} entries in CSV file")
    print(f"Target directory: {output_dir}\n")

    for idx, item in enumerate(data, 1):
        file_url = item.get('url', '').strip()
        custom_filename = item.get('filename', '').strip()

        if not file_url:
            print(f"[{idx}/{total}] Skipped - no URL")
            continue

        # Extract original filename from URL
        url_filename = extract_filename_from_url(file_url)
        if not url_filename:
            url_filename = f'file_{idx}'

        # Limit URL filename to 50 characters
        if len(url_filename) > 50:
            url_filename = url_filename[:50]

        # Combine URL filename with custom filename
        if custom_filename:
            combined_filename = f"{url_filename} - {custom_filename}"
        else:
            combined_filename = url_filename

        # Sanitize filename (max 200 chars total)
        safe_filename = sanitize_filename(combined_filename)
        local_filename = f"{safe_filename}.pdf"

        local_path = os.path.join(output_dir, local_filename)

        try:
            print(f"[{idx}/{total}] Downloading: {custom_filename if custom_filename else url_filename}")
            print(f"  URL: {file_url}")
            print(f"  Saving as: {local_filename}")

            # Encode URL (replace special characters with %XX)
            # URL already contains partial encoding, but need to encode the path
            parsed = urllib.parse.urlparse(file_url)
            # Encode path using quote - safe='/' preserves slashes
            encoded_path = urllib.parse.quote(parsed.path, safe='/')
            # Build encoded URL
            encoded_url = urllib.parse.urlunparse((
                parsed.scheme,
                parsed.netloc,
                encoded_path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))

            # Download file - use urllib with appropriate headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            req = urllib.request.Request(encoded_url, headers=headers)

            with urllib.request.urlopen(req) as response:
                with open(local_path, 'wb') as out_file:
                    out_file.write(response.read())

            downloaded += 1
            print(f"  ✓ Downloaded successfully\n")

        except Exception as e:
            errors += 1
            import traceback
            print(f"  ✗ Error while downloading: {str(e)}")
            print(f"  Details:\n{traceback.format_exc()}")

    # Summary
    print("=" * 60)
    print(f"Summary:")
    print(f"  Total entries: {total}")
    print(f"  Downloaded successfully: {downloaded}")
    print(f"  Errors: {errors}")
    print("=" * 60)


if __name__ == "__main__":
    download_pdfs()
