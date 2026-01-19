#!/usr/bin/env python3
"""
Konwersja pliku PDF na format Markdown przy użyciu EasyOCR.
Nie wymaga sudo - wszystko przez pip!
"""

import fitz  # PyMuPDF
import os
from pathlib import Path
import io
from PIL import Image

# Sprawdź czy EasyOCR jest dostępne
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    print("UWAGA: EasyOCR nie jest zainstalowane.")
    print("Zainstaluj: pip install easyocr")


class PDFToMarkdownConverter:
    """Konwerter PDF na Markdown z OCR"""

    def __init__(self, languages=['pl', 'en']):
        """
        Inicjalizacja konwertera.

        Args:
            languages: Lista języków do rozpoznawania (domyślnie polski i angielski)
        """
        self.languages = languages
        self.reader = None

        if EASYOCR_AVAILABLE:
            print(f"Inicjalizacja EasyOCR dla języków: {', '.join(languages)}")
            print("(Pierwsze uruchomienie pobierze modele ~100-200MB)")
            self.reader = easyocr.Reader(languages, gpu=False)
            print("✓ EasyOCR gotowe!")

    def extract_text_from_image(self, image):
        """
        Wyciąga tekst z obrazu używając OCR.

        Args:
            image: PIL Image object

        Returns:
            str: Rozpoznany tekst
        """
        if not self.reader:
            raise RuntimeError("EasyOCR nie jest zainicjalizowane!")

        # Konwertuj PIL Image na numpy array (EasyOCR wymaga tego formatu)
        import numpy as np
        img_array = np.array(image)

        # Wykonaj OCR
        results = self.reader.readtext(img_array, detail=0, paragraph=True)

        # Połącz wyniki w tekst
        text = '\n'.join(results)
        return text

    def pdf_to_markdown(self, pdf_path: str, output_path: str = None) -> str:
        """
        Konwertuje plik PDF na format Markdown.

        Args:
            pdf_path: Ścieżka do pliku PDF
            output_path: Ścieżka do pliku wyjściowego (opcjonalne)

        Returns:
            Tekst w formacie Markdown
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Plik nie został znaleziony: {pdf_path}")

        if not EASYOCR_AVAILABLE:
            raise RuntimeError("EasyOCR nie jest zainstalowane. Uruchom: pip install easyocr")

        # Otwórz dokument PDF
        doc = fitz.open(pdf_path)

        markdown_content = []
        markdown_content.append(f"# {Path(pdf_path).stem}\n")
        markdown_content.append(f"*Dokument zawiera {len(doc)} stron*\n")
        markdown_content.append("*Tekst rozpoznany automatycznie przez OCR*\n")

        print(f"\nPrzetwarzam PDF: {pdf_path}")
        print(f"Liczba stron: {len(doc)}\n")

        # Przetwórz każdą stronę
        for page_num in range(len(doc)):
            page = doc[page_num]

            print(f"Strona {page_num + 1}/{len(doc)}...")

            # Dodaj nagłówek strony
            markdown_content.append(f"\n---\n\n## Strona {page_num + 1}\n")

            # Sprawdź czy jest tekst w PDF
            text = page.get_text("text").strip()

            if text and len(text) > 50:
                # Jest tekst w PDF - użyj go
                print(f"  ✓ Znaleziono tekst w PDF ({len(text)} znaków)")
                markdown_content.append(text)
            else:
                # Brak tekstu - użyj OCR
                print(f"  → Używam OCR...")

                # Renderuj stronę jako obraz (wyższa rozdzielczość = lepsza jakość OCR)
                zoom = 2  # 2x zoom
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)

                # Konwertuj do PIL Image
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))

                # Wykonaj OCR
                try:
                    ocr_text = self.extract_text_from_image(img)

                    if ocr_text:
                        print(f"  ✓ OCR rozpoznał {len(ocr_text)} znaków")
                        markdown_content.append(ocr_text)
                    else:
                        print(f"  ⚠ OCR nie rozpoznał tekstu")
                        markdown_content.append("*[Brak rozpoznanego tekstu]*")

                except Exception as e:
                    print(f"  ✗ Błąd OCR: {e}")
                    markdown_content.append(f"*[Błąd OCR: {e}]*")

            # Informacja o obrazach
            image_list = page.get_images()
            if image_list:
                markdown_content.append(f"\n*[Strona zawiera {len(image_list)} obraz(ów)]*")

        # Zamknij dokument
        doc.close()

        # Połącz wszystko w jeden string
        markdown_text = "\n".join(markdown_content)

        # Zapisz do pliku jeśli podano ścieżkę
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_text)
            print(f"\n✓ Plik Markdown zapisany do: {output_path}")

        return markdown_text


def main():
    """Główna funkcja programu"""

    # Konfiguracja
    input_folder = "input"
    output_folder = "output"

    # Stwórz folder output jeśli nie istnieje
    os.makedirs(output_folder, exist_ok=True)

    # Znajdź wszystkie pliki PDF w folderze input
    input_path = Path(input_folder)
    pdf_files = list(input_path.glob("*.pdf"))

    if not pdf_files:
        print(f"Brak plików PDF w folderze '{input_folder}'")
        return

    print(f"Znaleziono {len(pdf_files)} plik(ów) PDF do przetworzenia:\n")
    for pdf_file in pdf_files:
        print(f"  - {pdf_file.name}")
    print()

    try:
        # Stwórz konwerter (tylko raz dla wszystkich plików)
        converter = PDFToMarkdownConverter(languages=['pl', 'en'])

        # Przetwórz każdy plik PDF
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"\n{'='*60}")
            print(f"Plik {i}/{len(pdf_files)}: {pdf_file.name}")
            print(f"{'='*60}")

            # Stwórz nazwę pliku wyjściowego (zamień .pdf na .md)
            output_file = os.path.join(output_folder, pdf_file.stem + ".md")

            try:
                # Konwertuj PDF na Markdown
                markdown_text = converter.pdf_to_markdown(str(pdf_file), output_file)

                print(f"\n✓ Konwersja zakończona pomyślnie!")
                print(f"Długość tekstu: {len(markdown_text)} znaków")

            except Exception as e:
                print(f"\n✗ Błąd podczas przetwarzania {pdf_file.name}: {e}")
                continue

        print(f"\n{'='*60}")
        print(f"✓ WSZYSTKIE PLIKI PRZETWORZONE!")
        print(f"{'='*60}")
        print(f"Przetworzone pliki: {len(pdf_files)}")
        print(f"Pliki zapisane w folderze: {output_folder}")

    except Exception as e:
        print(f"\n✗ Błąd krytyczny: {e}")
        raise


if __name__ == "__main__":
    main()
