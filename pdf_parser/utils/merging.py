def score(text, table_md):
    return len(text.strip()) + table_md.count("|") * 10

def is_valid(text, table_md):
    rows = [r for r in table_md.strip().split("\n") if r.strip()]
    if table_md and (len(rows) <= 2 or all(not any(c.strip() for c in r.split("|")) for r in rows[2:])):
        return False
    return bool(text and len(text.strip()) > 20) or (table_md and table_md.count("|") > 3)

def merge_parsers(fitz_result, plumber_result):
    candidates = [("fitz", *fitz_result), ("plumber", *plumber_result)]
    best = max(candidates, key=lambda x: score(x[1], x[2]))
    if is_valid(best[1], best[2]):
        return best[1], best[2]
    return None, None