"""Text extraction from PDFs using Tesseract OCR."""
from typing import Optional


def extract_text_from_pdf(file_path: str, use_ocr: bool = True) -> str:
    """
    Extract text from a PDF file.
    
    First attempts to extract text directly from PDF.
    If that fails or returns little text, falls back to OCR.
    
    Args:
        file_path: Path to the PDF file
        use_ocr: Whether to use OCR if direct extraction fails
        
    Returns:
        Extracted text
    """
    text = ""
    
    # Try direct text extraction first
    try:
        from PyPDF2 import PdfReader
        
        reader = PdfReader(file_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        print(f"Direct PDF extraction failed: {e}")
    
    # If direct extraction didn't work well, use OCR
    if use_ocr and (not text or len(text) < 100):
        text = extract_text_with_tesseract(file_path)
    
    return text


def extract_text_with_tesseract(file_path: str) -> str:
    """
    Extract text from PDF using Tesseract OCR.
    
    Converts PDF pages to images and runs OCR on each.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Extracted text
    """
    try:
        import pytesseract
        from pdf2image import convert_from_path
        
        # Convert PDF to images
        images = convert_from_path(file_path)
        
        text = ""
        for image in images:
            # Run OCR on each page
            page_text = pytesseract.image_to_string(image)
            text += page_text + "\n"
        
        return text
    except ImportError:
        # Tesseract not available, return stub message
        return "OCR not available. Install pytesseract and pdf2image: pip install pytesseract pdf2image"
    except Exception as e:
        return f"OCR failed: {e}"

