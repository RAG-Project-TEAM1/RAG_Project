from md_processor.null_cleaner import load_and_clean_file
from md_processor.header_converter import OptimizedMarkdownConverter
from pathlib import Path
from typing import Optional

def process_md_file(input_path: str, output_path: Optional[str] = None, remove_consecutive: bool = True) -> bool:
    """단일 파일 처리 파이프라인: NULL 제거 + 헤더 구조 변환"""
    try:
        print(f"🚀 시작: {input_path}")

        cleaned_text, null_count = load_and_clean_file(input_path)
        print(f"🔹 NULL 제거 완료: {null_count}개, 길이: {len(cleaned_text)}")

        converter = OptimizedMarkdownConverter()
        converter.set_consecutive_header_removal_enabled(remove_consecutive)
        converted_text = converter.convert_document(cleaned_text)
        print(f"🔹 변환 후 길이: {len(converted_text)}")

        input_file = Path(input_path)
        output_path = Path(output_path) if output_path else input_file.parent / f"{input_file.stem}_final.md"
        print(f"💾 저장 위치: {output_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(converted_text)

        print(f"✅ 완료: {input_file.name} → {output_path.name} (NULL 제거: {null_count}개)")
        return True

    except Exception as e:
        print(f"❌ 오류: {input_path} → {e}")
        return False

def process_directory(input_dir: str, output_dir: str = None, remove_consecutive: bool = True):
    """디렉토리 내 모든 .md 파일 일괄 처리 파이프라인"""
    input_dir_path = Path(input_dir)
    md_files = list(input_dir_path.rglob("*.md"))

    if not md_files:
        print(f"❌ {input_dir} 내에 .md 파일이 없습니다.")
        return

    print(f"📁 총 {len(md_files)}개의 Markdown 파일을 처리합니다.")

    for md_file in md_files:
        if any(suffix in md_file.stem for suffix in ['_clean', '_cleaned']):
            continue  # 중복 처리 방지

        # 출력 경로 지정
        if output_dir:
            relative = md_file.relative_to(input_dir_path)
            output_path = Path(output_dir) / relative
        else:
            output_path = md_file  # 덮어쓰기

        output_path.parent.mkdir(parents=True, exist_ok=True)

        process_md_file(
            input_path=str(md_file),
            output_path=str(output_path),
            remove_consecutive=remove_consecutive
        )