import argparse
from pdf_parser.converter import PDFConverter

def main():
    parser = argparse.ArgumentParser(description="PDF 변환 도구")
    parser.add_argument('-d', '--dir', required=True, help="PDF 파일이 있는 디렉토리 경로")
    parser.add_argument('-o', '--output', default="outputs", help="결과 파일 저장 경로")
    parser.add_argument('--format', default="json", choices=["json", "txt"], help="출력 형식")

    args = parser.parse_args()

    converter = PDFConverter(
        input_dir=args.dir,
        output_dir=args.output,
        output_format=args.format
    )

    converter.run_conversion()

if __name__ == "__main__":
    main()