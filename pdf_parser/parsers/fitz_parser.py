import logging



def extract_text_blocks(page) -> str:
    blocks = page.get_text("blocks")
    blocks.sort(key=lambda b: (round(b[1], 1), b[0]))
    
    merged_lines, current_line, current_y = [], [], None
    for b in blocks:
        x0, y0, x1, y1, text, *_ = b
        text = text.strip()
        if not text:
            continue
        if current_y is None or abs(y0 - current_y) < 5:
            current_line.append(text)
            current_y = y0
        else:
            merged_lines.append(" ".join(current_line))
            current_line, current_y = [text], y0
    if current_line:
        merged_lines.append(" ".join(current_line))
    return "\n".join(merged_lines)

def extract_tables_as_markdown(page) -> str:

    table_md = ""
    try:
        tables = page.find_tables()
        for table in tables:
            try:
                table_md += table.to_markdown() + "\n"
            except Exception as e:
                logging.warning(f"[fitz table markdown 실패] {e}")
    except Exception as e:
        logging.warning(f"[fitz table 추출 실패] {e}")
    return table_md

def parse_with_fitz(page):
    """
    PyMuPDF(fitz) 기반 페이지 PARSER
    - 블록 기준으로 병합된 텍스트와 표(markdown 변환)를 추출
    """
    try:
        text = extract_text_blocks(page)
        table_md = extract_tables_as_markdown(page)
        return text, table_md
    except Exception as e:
        logging.warning(f"[fitz 파싱 실패] {e}")
        return "", ""