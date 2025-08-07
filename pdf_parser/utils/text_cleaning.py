import re
import hashlib

def clean_text(text):
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r'-\s*\d+\s*-', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s가-힣.,!?;:()\[\]{}"\'-]', '', text)
    text = re.sub(r'\.{2,}', '.', text)
    text = text.replace("<br>", "\n")
    return text.strip()

def get_title_level(text):
    text = text.strip()
    if len(text) > 100:
        return 0
    if re.match(r"^(Ⅰ|Ⅱ|Ⅲ|Ⅳ|Ⅴ|Ⅵ|Ⅶ|Ⅷ|Ⅸ|Ⅹ)[.\\s]?", text):
        return 1
    if re.match(r"^제\\s?\\d+\\s?장", text):
        return 1
    if re.match(r"^\\d+(\\.\\d+)*[.\\s]", text):
        return 2
    if re.match(r"^[가-힣]\\.", text) and len(text) < 25:
        return 3
    return 0

def generate_doc_id(pdf_stem, title_text=None):
    base = pdf_stem + (title_text or "")
    return hashlib.md5(base.encode("utf-8")).hexdigest()

def is_meaningless_block(block):
    """
    목차 또는 의미 없는 표 등 제거해야 할 블록인지 판단
    """
    from .text_cleaning import is_toc_block, is_valid_table_chunk

    # 목차 제거
    if is_toc_block(block):
        return True

    # 표 블록인데 유효하지 않으면 제거
    if block.get("type") == "table":
        return not is_valid_table_chunk(block.get("content", ""))

    return False

def remove_garbage_chunks(chunks):
    return [c for c in chunks if len(c.page_content.strip()) > 20]