from pathlib import Path
import re
import json
import logging
from tqdm import tqdm
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pdf_parser.parsers.fitz_parser import parse_with_fitz
from pdf_parser.parsers.plumber_parser import parse_with_pdfplumber
from pdf_parser.parsers.unstructured_parser import parse_with_unstructured
from pdf_parser.utils.merging import merge_parsers
from pdf_parser.utils.text_cleaning import clean_text, get_title_level, generate_doc_id
from pdf_parser.utils.page_mapping import make_page_text_map, guess_page_range

class PDFConverter:
    def __init__(self, input_dir, output_dir="outputs", output_format="json"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_format = output_format.lower()
        self.success_count = 0
        self.failure_count = 0
        self.success_log = []

    def convert_single_pdf(self, pdf_path):
        import fitz, pdfplumber
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
                    clean = clean_text(text)
                    level = get_title_level(clean)
                    block_type = "title" if level > 0 else "text"
                    block = {"type": block_type, "content": clean}
                    if block_type == "title":
                        block["level"] = level
                        if level == 1 and not main_title_text:
                            main_title_text = clean
                    all_blocks.append(block)

                if table:
                    all_blocks.append({"type": "table", "content": table.strip()})

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
            splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
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
        self.success_log.append({"filename": pdf_path.name, "block_count": len(all_blocks)})

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
        print(f"\u2705 성공: {self.success_count}개")
        print(f"\u274c 실패: {self.failure_count}개")
        print(f"성공률: {success_rate:.1f}%")
        if self.success_log:
            avg_len = sum(log['block_count'] for log in self.success_log) / len(self.success_log)
            print(f"평균 블록 수: {avg_len:.0f}")
        print("=" * 50)

    def run_conversion(self):
        from pdf_parser.utils.logging_config import setup_logging
        setup_logging()
        print(f"PDF 변환 시작... 출력 형식: {self.output_format}")
        self.convert_documents()
        self.print_summary()