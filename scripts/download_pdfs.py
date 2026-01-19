#!/usr/bin/env python3
"""
Skrypt do pobierania plików PDF z pliku files.json
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
    Tworzy bezpieczną nazwę pliku usuwając/zamieniając problematyczne znaki.

    Args:
        filename: Oryginalna nazwa pliku

    Returns:
        Bezpieczna nazwa pliku
    """
    # Normalizuj unicode (zamień znaki akcentowane na podstawowe)
    # NFD = Normalization Form Canonical Decomposition
    nfkd_form = unicodedata.normalize('NFKD', filename)

    # Pozostaw tylko znaki ASCII
    ascii_string = nfkd_form.encode('ASCII', 'ignore').decode('ASCII')

    # Zamień pozostałe problematyczne znaki
    safe_string = re.sub(r'[<>:"/\\|?*]', '_', ascii_string)

    # Usuń wielokrotne podkreślenia i spacje
    safe_string = re.sub(r'[_\s]+', '_', safe_string)

    # Usuń podkreślenia na początku i końcu
    safe_string = safe_string.strip('_')

    return safe_string


def download_pdfs(json_file: str = "input/files.json", output_dir: str = "input"):
    """
    Pobiera wszystkie pliki PDF z tablicy w pliku JSON.

    Args:
        json_file: Ścieżka do pliku JSON z danymi
        output_dir: Katalog docelowy dla pobranych plików
    """
    # Wczytaj plik JSON
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Upewnij się, że katalog docelowy istnieje
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Liczniki
    total = len(data)
    downloaded = 0
    errors = 0

    print(f"Znaleziono {total} pozycji w pliku JSON")
    print(f"Katalog docelowy: {output_dir}\n")

    for idx, item in enumerate(data, 1):
        file_url = item.get('file', '')
        filename = item.get('filename', f'file_{idx}')

        if not file_url:
            print(f"[{idx}/{total}] Pominięto - brak URL")
            continue

        # Wyodrębnij nazwę pliku z URL
        parsed_url = urllib.parse.urlparse(file_url)
        url_filename = os.path.basename(urllib.parse.unquote(parsed_url.path))

        # Użyj nazwy z URL lub z pola filename jako fallback
        if url_filename.endswith('.pdf'):
            # Sanityzuj nazwę z URL
            local_filename = sanitize_filename(url_filename)
        else:
            # Sanityzuj nazwę pliku z JSON
            safe_filename = sanitize_filename(filename)
            local_filename = f"{safe_filename}.pdf"

        local_path = os.path.join(output_dir, local_filename)

        try:
            print(f"[{idx}/{total}] Pobieranie: {filename}")
            print(f"  URL: {file_url}")
            print(f"  Zapisywanie jako: {local_filename}")

            # Zakoduj URL (zamień znaki specjalne na %XX)
            # URL już zawiera częściowe kodowanie, ale trzeba dokodować ścieżkę
            parsed = urllib.parse.urlparse(file_url)
            # Zakoduj ścieżkę używając quote - safe='/' zachowuje slashe
            encoded_path = urllib.parse.quote(parsed.path, safe='/')
            # Zbuduj zakodowany URL
            encoded_url = urllib.parse.urlunparse((
                parsed.scheme,
                parsed.netloc,
                encoded_path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))

            # Pobierz plik - użyj urllib z odpowiednimi nagłówkami
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            req = urllib.request.Request(encoded_url, headers=headers)

            with urllib.request.urlopen(req) as response:
                with open(local_path, 'wb') as out_file:
                    out_file.write(response.read())

            downloaded += 1
            print(f"  ✓ Pobrano pomyślnie\n")

        except Exception as e:
            errors += 1
            import traceback
            print(f"  ✗ Błąd podczas pobierania: {str(e)}")
            print(f"  Szczegóły:\n{traceback.format_exc()}")

    # Podsumowanie
    print("=" * 60)
    print(f"Podsumowanie:")
    print(f"  Razem pozycji: {total}")
    print(f"  Pobrano pomyślnie: {downloaded}")
    print(f"  Błędy: {errors}")
    print("=" * 60)


if __name__ == "__main__":
    download_pdfs()
