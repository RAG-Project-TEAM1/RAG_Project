from pathlib import Path
from typing import Tuple

def remove_null_bytes(content: str) -> Tuple[str, int]:
    """텍스트 내 NULL Byte 제거"""
    null_count = content.count('\x00')
    cleaned_content = content.replace('\x00', '')
    return cleaned_content, null_count

def load_and_clean_file(path: str) -> Tuple[str, int]:
    input_file = Path(path)
    if not input_file.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {path}")

    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    return remove_null_bytes(content)