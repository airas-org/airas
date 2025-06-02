import glob
import os
from logging import getLogger

import fitz

logger = getLogger(__name__)


def convert_pdf_to_png(
    pdf_dir: str, 
    to_png_dir: str, 
    scale: float = 2.0,     
) -> bool:
    os.makedirs(to_png_dir, exist_ok=True)

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

            filename = os.path.splitext(os.path.basename(pdf_file))[0]
            png_path = os.path.join(to_png_dir, f"{filename}.png")
            pix.save(png_path)
            
            logger.info(f"Converted {pdf_file} → {png_path}")
        except Exception as e:
            logger.warning(f"Failed to convert {pdf_file} to PNG: {e}")
            success = False
    return success
