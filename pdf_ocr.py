import pytesseract
import sys
from pdf2image import convert_from_path
from pikepdf import Pdf
from io import BytesIO

def pdf_ocr(pdf_path: str, output_pdf_path: str):
    # 需要安装pytesseract
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

if __name__ == "__main__":
    arg_count = len(sys.argv) - 1
    if arg_count == 0:
        print("Usage: crawl_mba_essay.py <filename>")
        sys.exit(1)
    
    filename = sys.argv[1]
    
    pdf_ocr(f"{filename}.pdf", f"{filename}_ocr.pdf")
