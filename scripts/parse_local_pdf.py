#!/usr/bin/env python3
"""Quick helper to parse a local PDF using the app's parser utilities.

Usage:
  python scripts/parse_local_pdf.py /path/to/file.pdf

This will print JSON output similar to what the API stores in Document.parsed_data.
"""
import sys
import json
from io import BytesIO

try:
    import pdfplumber
except Exception:
    pdfplumber = None
try:
    import pytesseract
    from PIL import Image
except Exception:
    pytesseract = None
    Image = None

from app.utils.ocr import extract_wr_entries, extract_wr_fields


def parse_pdf(path: str):
    content = None
    try:
        with open(path, 'rb') as fh:
            content = fh.read()
    except Exception as e:
        print(f"Cannot read file {path}: {e}")
        return 1
    text = ''
    if pdfplumber and path.lower().endswith('.pdf'):
        try:
            with pdfplumber.open(BytesIO(content)) as pdf:
                pages = [p.extract_text() or '' for p in pdf.pages]
                text = '\n'.join(pages)
        except Exception:
            # fallback to raw bytes decode
            try:
                text = content.decode('utf-8')
            except Exception:
                text = ''
        # if no text and pytesseract is installed try OCR
        if (not text or len(text.strip()) == 0) and pytesseract is not None:
            try:
                with pdfplumber.open(BytesIO(content)) as pdf:
                    ocr_pages = []
                    for page in pdf.pages:
                        try:
                            pil_image = page.to_image(resolution=200).original
                            page_text = pytesseract.image_to_string(pil_image)
                            ocr_pages.append(page_text)
                        except Exception:
                            continue
                    if ocr_pages:
                        text = '\n'.join(ocr_pages)
            except Exception:
                pass
    else:
        try:
            text = content.decode('utf-8')
        except Exception:
            text = ''

    if not text:
        print('Warning: no text extracted; the PDF might be image-only (scanned). Try OCR fallback in the app.')
    # Attempt to split into multiple entries
    entries = []
    try:
        entries = extract_wr_entries(text)
    except Exception:
        entries = []
    if not entries:
        # fallback entry
        try:
            entries = [extract_wr_fields(text)]
        except Exception:
            entries = []

    out = {
        'raw_text': text,
        'entries': entries,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python scripts/parse_local_pdf.py /path/to/file.pdf')
        raise SystemExit(1)
    raise SystemExit(parse_pdf(sys.argv[1]))
