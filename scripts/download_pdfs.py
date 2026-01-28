#!/usr/bin/env python3
"""
Script for downloading PDF files from files.json
"""

import json
import os
import urllib.request
import urllib.parse
from pathlib import Path
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


def download_pdfs(json_file: str = "input/files.json", output_dir: str = "input"):
    """
    Downloads all PDF files from the array in the JSON file.

    Args:
        json_file: Path to the JSON file with data
        output_dir: Target directory for downloaded files
    """
    # Load JSON file
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Ensure the target directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Counters
    total = len(data)
    downloaded = 0
    errors = 0

    print(f"Found {total} entries in JSON file")
    print(f"Target directory: {output_dir}\n")

    for idx, item in enumerate(data, 1):
        file_url = item.get('file', '')
        filename = item.get('filename', f'file_{idx}')
        filedesc = item.get('filedesc', '')

        if not file_url:
            print(f"[{idx}/{total}] Skipped - no URL")
            continue

        # Create filename from filename and filedesc
        if filedesc:
            combined_name = f"{filename} - {filedesc}"
        else:
            combined_name = filename

        # Sanitize filename
        safe_filename = sanitize_filename(combined_name)
        local_filename = f"{safe_filename}.pdf"

        local_path = os.path.join(output_dir, local_filename)

        try:
            print(f"[{idx}/{total}] Downloading: {filename}")
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
