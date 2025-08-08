import logging

def parse_with_fitz(page):
    """
    PyMuPDF(fitz) 기반 페이지 PARSER
    - 텍스트와 표(markdown 변환)를 추출
    """
    try:
        text = page.get_text().strip()
        tables = page.find_tables()
        table_md = ""
        if tables:
            for table in tables:
                try:
                    table_md += table.to_markdown() + "\n"
                except Exception as e:
                    logging.warning(f"[fitz table markdown 실패] {e}")
        return text, table_md
    except Exception as e:
        logging.warning(f"[fitz 파싱 실패] {e}")
        return "", ""