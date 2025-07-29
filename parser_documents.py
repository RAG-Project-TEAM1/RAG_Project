import fitz  # PyMuPDF
import pdfplumber
from unstructured.partition.pdf import partition_pdf
from pathlib import Path
import json
import re
import logging
from tqdm import tqdm
import hashlib
from langchain.text_splitter import RecursiveCharacterTextSplitter
# from concurrent.futures import ProcessPoolExecutor, as_completed

"""
parser_document.py
전체 구조:
PDF -> [fitz] + [plumber] 분석 -> [unstructured] 병합 -> 블록 정제/중복 제거 -> 저장

PDF 문서를 페이지 단위로 분석하여 .json 또는 .txt로 저장하는 파서 파이프라인
PDFConverter(input_dir="/home/shared_rag", output_dir="outputs_2", output_format="json")
input_dir: PDF 파일이 있는 디렉토리 경로
output_dir: 변환된 결과를 저장할 디렉토리 경로
output_format: "json" 또는 "txt" 중 하나, 기본값은 "json"
"""

logging.basicConfig(
    filename="parse_failures.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def generate_doc_id(pdf_stem, title_text=None):
    base = pdf_stem + (title_text or "")
    return hashlib.md5(base.encode("utf-8")).hexdigest()

# fitz 기반 PARSER
def parse_with_fitz(page):
    """
    PyMuPDF(fitz) 기반 페이지 PARSER
    - 텍스트와 표(markdown 변환)를 추출
    """
    try:
        text = page.get_text().strip()
        tables = page.find_tables()
        
        table_md = ""
        if tables:
            for table in tables:
                try:
                    table_md += table.to_markdown() + "\n"
                except Exception as e:
                    logging.warning(f"[fitz table markdown 실패] {e}")
        return text, table_md

    except Exception as e:
        logging.warning(f"[fitz 파싱 실패] {e}")
        return "", ""
    
# pdfplumber 기반 PARSER
def parse_with_pdfplumber(page):
    """
    pdfplumber 기반 페이지 PARSER
    - 텍스트와 첫 번째 표(markdown 변환)를 추출한다.
    """
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

def parse_with_unstructured(pdf_path):
    """
    unstructured 라이브러리 기반 PDF PARSER
    - 페이지 단위로 텍스트와 메타데이터를 추출
    """
    try:
        elements = partition_pdf(
            filename=str(pdf_path),
            languages=["ko"],
            strategy="hi_res",
            extract_images_in_pdf=False,
            infer_table_structure=True,
            pdf_infer_table_structure=True
        )
        blocks = []
        for el in elements:
            text = (el.text or "").strip()
            if not text:
                continue
            block = {
                "type": el.category.lower(),
                "content": text
            }
            blocks.append(block)
        return blocks
    except Exception as e:
        logging.warning(f"[{pdf_path.name}] Unstructured 실패: {e}")
        return []

# fitz + pdfplumber 병합 전략
def is_valid(text, table_md):
    """
    텍스트 또는 테이블이 유의미한지 판단하는 로직
    - 테이블 유효성 검사:
        - 줄 수가 2줄 이하이면 제거 (헤더 + 구분선만 존재하는 빈 테이블)
        - 3번째 줄부터의 셀 내용이 모두 비어 있으면 제거 (실제 데이터가 없음)
    - 텍스트 유효성 검사:
        - 텍스트가 20자 이상이거나
        - 유효한 테이블(markdown 파이프가 3개 이상)이 존재하면 True
    위 조건을 모두 만족하지 않으면 False 처리하여 블록 제거 대상
    """
    if table_md:
        rows = [r for r in table_md.strip().split("\n") if r.strip()]
        if len(rows) <= 2:
            return False
        if all(not any(cell.strip() for cell in row.split("|")) for row in rows[2:]):
            return False
    return bool(text and len(text.strip()) > 20) or (table_md and table_md.count("|") > 3)

def score(text, table_md):
    return len(text.strip()) + table_md.count("|") * 10

def merge_parsers(fitz_result, plumber_result):
    candidates = [("fitz", *fitz_result), ("plumber", *plumber_result)]
    best = max(candidates, key=lambda x: score(x[1], x[2]))
    if is_valid(best[1], best[2]):
        return best[1], best[2]
    return None, None

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

def convert_pdf_file(pdf_path_str, output_dir, output_format):
    converter = PDFConverter(input_dir="", output_dir=output_dir, output_format=output_format)
    converter.convert_single_pdf(Path(pdf_path_str))

class PDFConverter:
    def __init__(self, input_dir, output_dir="outputs", output_format="json"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_format = output_format.lower()
        self.success_count = 0
        self.failure_count = 0
        self.success_log = []

    def clean_text(self, text):
        if not text:
            return ""
        text = text.strip()
        text = re.sub(r'-\s*\d+\s*-', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s가-힣.,!?;:()\[\]{}"\'-]', '', text)
        text = re.sub(r'\.{2,}', '.', text)
        text = text.replace("<br>", "\n")
        return text.strip()

    def get_title_level(self, text):
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

    def convert_single_pdf(self, pdf_path):
        try:
            doc_fitz = fitz.open(pdf_path)
            doc_plumber = pdfplumber.open(pdf_path)
        except Exception as e:
            logging.warning(f"[{pdf_path.name}] PDF 열기 실패: {e}")
            self.failure_count += 1
            return

        if len(doc_fitz) != len(doc_plumber.pages):
            logging.warning(f"[{pdf_path.name}] 페이지 수 불일치")
            self.failure_count += 1
            return

        all_blocks = []
        main_title_text = None

        for i in tqdm(range(len(doc_fitz)), desc=pdf_path.name, leave=False):
            try:
                f_result = parse_with_fitz(doc_fitz[i])
                p_result = parse_with_pdfplumber(doc_plumber.pages[i])
                text, table = merge_parsers(f_result, p_result)

                if text:
                    clean = self.clean_text(text)
                    level = self.get_title_level(clean)
                    block_type = "title" if level > 0 else "text"
                    block = {
                        "type": block_type,
                        "content": clean
                    }
                    if block_type == "title":
                        block["level"] = level
                        if level == 1 and not main_title_text:
                            main_title_text = clean
                    all_blocks.append(block)

                if table:
                    all_blocks.append({
                        "type": "table",
                        "content": table.strip()
                    })

            except Exception as e:
                logging.warning(f"[{pdf_path.name}] Page {i+1} 처리 오류: {e}")
                continue

        doc_fitz.close()
        doc_plumber.close()

        u_blocks = parse_with_unstructured(pdf_path)
        existing_contents = set(b["content"] for b in all_blocks)
        for ub in u_blocks:
            if ub["content"] not in existing_contents:
                all_blocks.append(ub)
                existing_contents.add(ub["content"])

        if not all_blocks:
            self.failure_count += 1
            return

        self.output_dir.mkdir(parents=True, exist_ok=True)
        doc_id = generate_doc_id(pdf_path.stem, main_title_text)

        if self.output_format == "json":
            full_text = "\n\n".join(b["content"] for b in all_blocks)
            splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            chunks = splitter.create_documents([full_text])
            page_map = make_page_text_map(all_blocks)

            chunked_result = []
            for i, chunk in enumerate(chunks):
                p_start, p_end = guess_page_range(chunk.page_content, page_map)
                chunked_result.append({
                    "doc_id": doc_id,
                    "chunk_id": f"{doc_id}_{i}",
                    "file_name": pdf_path.name,
                    "content": chunk.page_content,
                    "metadata": {
                        "page_start": p_start,
                        "page_end": p_end,
                        "chunk_index": i
                    }
                })
            
            output_path = self.output_dir / f"{pdf_path.stem}_chunked.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(chunked_result, f, ensure_ascii=False, indent=2)
                print(f"[저장 완료] {output_path}")
                

        self.success_count += 1
        self.success_log.append({
            "filename": pdf_path.name,
            "block_count": len(all_blocks)
        })


def convert_documents(self):
    pdf_files = list(self.input_dir.glob("*.pdf"))
    for pdf_path in tqdm(pdf_files, desc="전체 PDF 순차 처리", unit="file"):
        try:
            self.convert_single_pdf(pdf_path)
        except Exception as e:
            logging.warning(f"[{pdf_path.name}] 순차 처리 중 예외 발생: {e}")

    def print_summary(self):
        total = self.success_count + self.failure_count
        success_rate = (self.success_count / total * 100) if total > 0 else 0

        print("\n" + "=" * 50)
        print("변환 결과 요약")
        print("=" * 50)
        print(f"총 파일 수: {total}개")
        print(f"✅ 성공: {self.success_count}개")
        print(f"❌ 실패: {self.failure_count}개")
        print(f"성공률: {success_rate:.1f}%")
        if self.success_log:
            avg_len = sum(log['block_count'] for log in self.success_log) / len(self.success_log)
            print(f"평균 블록 수: {avg_len:.0f}")
        print("=" * 50)

    def run_conversion(self):
        print(f"PDF 변환 시작...출력 형식: {self.output_format}")
        self.convert_documents()
        self.print_summary()

# 폴더 내 전체 PDF 처리 pipeline
def main():
    print("PDF 변환 파이프라인 시작...")

    converter = PDFConverter(input_dir="/home/shared_rag", output_dir="outputs_2", output_format="json")
    converter.run_conversion()

if __name__ == "__main__":
    main()