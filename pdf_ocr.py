import pytesseract
from pdf2image import convert_from_path
from pdfminer.high_level import extract_text
from pikepdf import Pdf, Page
from io import BytesIO
from PIL import Image

def pdf_ocr(pdf_path: str, output_pdf_path: str):
    # Convert PDF to images
    images = convert_from_path(pdf_path)

    # OCR text extraction
    ocr_text = []
    for img in images:
        text = pytesseract.image_to_pdf_or_hocr(img, extension='pdf')
        ocr_text.append(text)

    # Merge OCR text into original PDF
    pdf = Pdf.open(pdf_path)
    for i, page in enumerate(pdf.pages):
        overlay_pdf = Pdf.open(BytesIO(ocr_text[i]))
        page.contents.stream = overlay_pdf.pages[0].contents.stream

    # Save final PDF
    pdf.save(output_pdf_path)
    pdf.close()
