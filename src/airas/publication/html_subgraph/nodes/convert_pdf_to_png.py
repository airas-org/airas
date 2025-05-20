import glob
import os
from logging import getLogger

import fitz

logger = getLogger(__name__)


def convert_pdf_to_png(
    save_dir: str, 
    scale: float = 2.0,     
) -> bool:
    pdf_dir = os.path.join(save_dir, "images")
    pdf_files = glob.glob(os.path.join(pdf_dir, "*.pdf"))
    if not pdf_files:        
        logger.info(f"No PDF files found in {pdf_dir}")
        return False

    success = True
    for pdf_file in pdf_files:
        try:
            doc = fitz.open(pdf_file)
            page = doc.load_page(0)
            mat = fitz.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=mat)
            png_path = pdf_file.replace(".pdf", ".png")
            pix.save(png_path)
            logger.info(f"Converted {pdf_file} → {png_path}")
        except Exception as e:
            logger.warning(f"Failed to convert {pdf_file} to PNG: {e}")
            success = False
    return success
