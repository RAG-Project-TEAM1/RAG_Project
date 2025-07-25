import fitz  # PyMuPDF
import pdfplumber
from unstructured.partition.pdf import partition_pdf
from pathlib import Path
import contextlib
import json
import os
import re
import logging
from itertools import groupby
from collections import defaultdict
from tqdm import tqdm 

"""
parser_document.py

PDF 문서를 페이지 단위로 분석하여 txt으로 저장하는 파서 파이프라인

로그 파일: parse_failures.log (현재 디렉토리)
출력 디렉토리: txt_results/
"""

logging.basicConfig(
    filename="parse_failures.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

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

# fitz + pdfplumber 병합 전략
def is_valid(text, table_md):
    """
    텍스트나 표 결과가 유의미한 경우만 True를 반환.
    - 텍스트가 충분히 긴 경우 (20자 이상)
    - 혹은 표가 포함된 경우 (Markdown의 구분자 '|' 존재)
    """
    return bool(text and len(text.strip()) > 20) or (table_md and table_md.count("|") > 3)

def score(text, table_md):
    return len(text.strip()) + table_md.count("|") * 10

def merge_parsers(fitz_result, plumber_result):
    candidates = [("fitz", *fitz_result), ("plumber", *plumber_result)]
    best = max(candidates, key=lambda x: score(x[1], x[2]))
    if is_valid(best[1], best[2]):
        return best[1], best[2]
    return None, None

class PDFConverter:
    def __init__(self, input_dir, output_dir="txt_results"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.success_count = 0
        self.failure_count = 0
        self.success_log = []

    def clean_text(self, text):
        import re
        if not text:
            return ""
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s가-힣.,!?;:()\[\]{}"\'-]', '', text)
        text = re.sub(r'\.{2,}', '.', text)
        text = text.replace("<br>", "\n")
        return text.strip()

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

        all_text = ""
        for i in tqdm(range(len(doc_fitz)), desc=pdf_path.name, leave=False):
            try:
                f_result = parse_with_fitz(doc_fitz[i])
                p_result = parse_with_pdfplumber(doc_plumber.pages[i])
                text, table = merge_parsers(f_result, p_result)

                if text:
                    # print(f"[DEBUG] {pdf_path.name} - Page {i+1} 텍스트 길이: {len(text)}")
                    text = self.clean_text(text)
                    all_text += f"\n{text}\n"
                    if table:
                        # print(f"[DEBUG] {pdf_path.name} - Page {i+1} 텍스트 길이: {len(text)}")
                        all_text += f"{table.strip()}\n"
                    all_text += "\n"
                else:
                    # print(f"[WARNING] {pdf_path.name} - Page {i+1} 텍스트 없음")
                    logging.warning(f"[{pdf_path.name}] Page {i+1} 추출 실패: 텍스트 없음")
            except Exception as e:
                logging.warning(f"[{pdf_path.name}] Page {i+1} 처리 오류: {e}")
                continue

        doc_fitz.close()
        doc_plumber.close()

        if not all_text.strip():
            self.failure_count += 1
            return

        # 저장
        output_path = self.output_dir / f"{pdf_path.stem}.txt"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(all_text.strip())

        self.success_count += 1
        self.success_log.append({
            "filename": pdf_path.name,
            "text_length": len(all_text)
        })

    def convert_documents(self):
        pdf_files = list(self.input_dir.glob("*.pdf"))
        for pdf_file in tqdm(pdf_files, desc="전체 PDF 처리", unit="file"):
            self.convert_single_pdf(pdf_file)

    def print_summary(self):
        total = self.success_count + self.failure_count
        success_rate = (self.success_count / total * 100) if total > 0 else 0

        print("\n" + "=" * 50)
        print("📊 변환 결과 요약")
        print("=" * 50)
        print(f"📄 총 파일 수: {total}개")
        print(f"✅ 성공: {self.success_count}개")
        print(f"❌ 실패: {self.failure_count}개")
        print(f"🔥 성공률: {success_rate:.1f}%")
        if self.success_log:
            avg_len = sum(log['text_length'] for log in self.success_log) / len(self.success_log)
            print(f"📝 평균 텍스트 길이: {avg_len:.0f}자")
        print("=" * 50)

    def run_conversion(self):
        print("🚀 PDF 변환 시작...")
        self.convert_documents()
        self.print_summary()

# 폴더 내 전체 PDF 처리 pipeline
def main():
    converter = PDFConverter(input_dir="/home/shared_rag", output_dir="txt_results")
    converter.run_conversion()

if __name__ == "__main__":
    main()