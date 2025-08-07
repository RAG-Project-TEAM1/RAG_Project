import re
from pathlib import Path
from rapidfuzz import fuzz, process

def sanitize_filename(filename):
    name = Path(filename).stem
    name = re.sub(r'[\\/:*?"<>|()\u3000\s]+', '', name)
    return name.strip()

def find_closest_filename(target, candidates):
    match = process.extractOne(target, candidates, scorer=fuzz.ratio)
    if match and match[1] > 90:
        return match[0]
    return None