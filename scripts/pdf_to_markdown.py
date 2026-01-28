#!/usr/bin/env python3
"""
Convert PDF files to Markdown format using EasyOCR.
No sudo required - everything via pip!
"""

import fitz  # PyMuPDF
import os
from pathlib import Path
import io
from PIL import Image

# Check if EasyOCR is available
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    print("WARNING: EasyOCR is not installed.")
    print("Install with: pip install easyocr")


class PDFToMarkdownConverter:
    """PDF to Markdown converter with OCR"""

    def __init__(self, languages=['pl', 'en']):
        """
        Initialize the converter.

        Args:
            languages: List of languages to recognize (default: Polish and English)
        """
        self.languages = languages
        self.reader = None

        if EASYOCR_AVAILABLE:
            print(f"Initializing EasyOCR for languages: {', '.join(languages)}")
            print("(First run will download models ~100-200MB)")
            self.reader = easyocr.Reader(languages, gpu=False)
            print("✓ EasyOCR ready!")

    def extract_text_from_image(self, image):
        """
        Extract text from image using OCR.

        Args:
            image: PIL Image object

        Returns:
            str: Recognized text
        """
        if not self.reader:
            raise RuntimeError("EasyOCR is not initialized!")

        # Convert PIL Image to numpy array (EasyOCR requires this format)
        import numpy as np
        img_array = np.array(image)

        # Perform OCR
        results = self.reader.readtext(img_array, detail=0, paragraph=True)

        # Combine results into text
        text = '\n'.join(results)
        return text

    def pdf_to_markdown(self, pdf_path: str, output_path: str = None) -> str:
        """
        Convert PDF file to Markdown format.

        Args:
            pdf_path: Path to PDF file
            output_path: Path to output file (optional)

        Returns:
            Text in Markdown format
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"File not found: {pdf_path}")

        if not EASYOCR_AVAILABLE:
            raise RuntimeError("EasyOCR is not installed. Run: pip install easyocr")

        # Open PDF document
        doc = fitz.open(pdf_path)

        markdown_content = []
        markdown_content.append(f"# {Path(pdf_path).stem}\n")
        markdown_content.append(f"*Document contains {len(doc)} pages*\n")
        markdown_content.append("*Text automatically recognized by OCR*\n")

        print(f"\nProcessing PDF: {pdf_path}")
        print(f"Number of pages: {len(doc)}\n")

        # Process each page
        for page_num in range(len(doc)):
            page = doc[page_num]

            print(f"Page {page_num + 1}/{len(doc)}...")

            # Add page header
            markdown_content.append(f"\n---\n\n## Page {page_num + 1}\n")

            # Check if there's text in PDF
            text = page.get_text("text").strip()

            if text and len(text) > 50:
                # Text found in PDF - use it
                print(f"  ✓ Found text in PDF ({len(text)} characters)")
                markdown_content.append(text)
            else:
                # No text - use OCR
                print(f"  → Using OCR...")

                # Render page as image (higher resolution = better OCR quality)
                zoom = 2  # 2x zoom
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)

                # Convert to PIL Image
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))

                # Perform OCR
                try:
                    ocr_text = self.extract_text_from_image(img)

                    if ocr_text:
                        print(f"  ✓ OCR recognized {len(ocr_text)} characters")
                        markdown_content.append(ocr_text)
                    else:
                        print(f"  ⚠ OCR did not recognize text")
                        markdown_content.append("*[No recognized text]*")

                except Exception as e:
                    print(f"  ✗ OCR error: {e}")
                    markdown_content.append(f"*[OCR error: {e}]*")

            # Information about images
            image_list = page.get_images()
            if image_list:
                markdown_content.append(f"\n*[Page contains {len(image_list)} image(s)]*")

        # Close document
        doc.close()

        # Combine everything into one string
        markdown_text = "\n".join(markdown_content)

        # Save to file if path provided
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_text)
            print(f"\n✓ Markdown file saved to: {output_path}")

        return markdown_text


def main():
    """Main program function"""

    # Configuration
    input_folder = "input"
    output_folder = "output"

    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Find all PDF files in input folder
    input_path = Path(input_folder)
    pdf_files = list(input_path.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in folder '{input_folder}'")
        return

    print(f"Found {len(pdf_files)} PDF file(s) to process:\n")
    for pdf_file in pdf_files:
        print(f"  - {pdf_file.name}")
    print()

    try:
        # Create converter (only once for all files)
        converter = PDFToMarkdownConverter(languages=['pl', 'en'])

        # Process each PDF file
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"\n{'='*60}")
            print(f"File {i}/{len(pdf_files)}: {pdf_file.name}")
            print(f"{'='*60}")

            # Create output file name (replace .pdf with .md)
            output_file = os.path.join(output_folder, pdf_file.stem + ".md")

            try:
                # Convert PDF to Markdown
                markdown_text = converter.pdf_to_markdown(str(pdf_file), output_file)

                print(f"\n✓ Conversion completed successfully!")
                print(f"Text length: {len(markdown_text)} characters")

            except Exception as e:
                print(f"\n✗ Error processing {pdf_file.name}: {e}")
                continue

        print(f"\n{'='*60}")
        print(f"✓ ALL FILES PROCESSED!")
        print(f"{'='*60}")
        print(f"Processed files: {len(pdf_files)}")
        print(f"Files saved in folder: {output_folder}")

    except Exception as e:
        print(f"\n✗ Critical error: {e}")
        raise


if __name__ == "__main__":
    main()
