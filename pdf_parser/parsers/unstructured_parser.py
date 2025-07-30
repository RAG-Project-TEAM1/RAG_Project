import logging
from unstructured.partition.pdf import partition_pdf

def parse_with_unstructured(pdf_path):
    try:
        elements = partition_pdf(
            filename=str(pdf_path),
            languages=["ko"],
            strategy="fast",
            extract_images_in_pdf=False,
            infer_table_structure=True,
            pdf_infer_table_structure=True
        )
        blocks = []
        for el in elements:
            text = (el.text or "").strip()
            if not text:
                continue
            block = {
                "type": el.category.lower(),
                "content": text
            }
            blocks.append(block)
        return blocks
    except Exception as e:
        logging.warning(f"[{pdf_path.name}] Unstructured 실패: {e}")
        return []
