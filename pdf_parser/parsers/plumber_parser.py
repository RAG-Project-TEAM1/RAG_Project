import logging

def extract_text_plumber(page) -> str:
    return (page.extract_text() or "").strip()

def extract_table_markdown_plumber(page) -> str:
    table_md = ""
    try:
        table = page.extract_table()
        if table and len(table) > 0 and table[0]:
            header = table[0]
            table_md += "| " + " | ".join(str(cell or "") for cell in header) + " |\n"
            table_md += "| " + " | ".join(["---"] * len(header)) + " |\n"
            for row in table[1:]:
                table_md += "| " + " | ".join(str(cell or "") for cell in row) + " |\n"
    except Exception as e:
        logging.warning(f"[plumber table parsing 실패] {e}")
    return table_md

def parse_with_pdfplumber(page):
    """
    pdfplumber 기반 페이지 PARSER
    - 텍스트와 첫 번째 표(markdown 변환)를 추출한다.
    """
    try:
        text = extract_text_plumber(page)
        table_md = extract_table_markdown_plumber(page)
        return text, table_md
    except Exception as e:
        logging.warning(f"[plumber 전체 파싱 실패] {e}")
        return "", ""