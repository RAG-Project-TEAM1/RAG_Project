def make_page_text_map(blocks, page_size=1000):
    page_text_map = {}
    buffer = ""
    page = 1
    for b in blocks:
        buffer += b["content"] + "\n\n"
        if len(buffer) > page_size:
            page_text_map[page] = buffer.strip()
            buffer = ""
            page += 1
    if buffer.strip():
        page_text_map[page] = buffer.strip()
    return page_text_map

def guess_page_range(chunk_text, page_text_map):
    start, end = None, None
    for p, t in page_text_map.items():
        if chunk_text[:30] in t and start is None:
            start = p
        if chunk_text[-30:] in t:
            end = p
    return start, end