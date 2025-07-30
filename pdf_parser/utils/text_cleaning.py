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