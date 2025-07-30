import logging

def parse_with_pdfplumber(page):
    try:
        text = page.extract_text() or ""
        table = page.extract_table()
        table_md = ""
        if table and len(table) > 0 and table[0]:
            table_md += "| " + " | ".join(str(cell or "") for cell in table[0]) + " |\n"
            table_md += "| " + " | ".join(["---"] * len(table[0])) + " |\n"
            for row in table[1:]:
                table_md += "| " + " | ".join(str(cell or "") for cell in row) + " |\n"
        return text.strip(), table_md
    except Exception as e:
        logging.warning(f"[plumber fail] {e}")
        return "", ""