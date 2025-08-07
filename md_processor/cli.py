import argparse
from md_processor.pipeline import process_md_file, process_directory
from pathlib import Path
import os

def main():
    parser = argparse.ArgumentParser(description="Markdown 클리너 파이프라인")
    parser.add_argument('-f', '--file', help='단일 .md 파일 경로')
    parser.add_argument('-d', '--dir', help='입력 디렉토리 경로')
    parser.add_argument('-o', '--output', help='출력 경로 (파일 또는 디렉토리)')
    parser.add_argument('--no-remove-consecutive', action='store_false', dest='remove_consecutive',
                        help='연속 헤더 제거 비활성화')

    args = parser.parse_args()

    if not args.file and not args.dir:
        print("❌ 파일(-f) 또는 디렉토리(-d) 중 하나는 지정해야 합니다.")
        return

    if args.file:
        if not os.path.exists(args.file):
            print(f"❌ 파일이 존재하지 않습니다: {args.file}")
            return

        process_md_file(
            input_path=args.file,
            output_path=args.output,
            remove_consecutive=args.remove_consecutive
        )

    if args.dir:
        if not os.path.exists(args.dir):
            print(f"❌ 디렉토리가 존재하지 않습니다: {args.dir}")
            return

        process_directory(
            input_dir=args.dir,
            output_dir=args.output,
            remove_consecutive=args.remove_consecutive
        )

if __name__ == "__main__":
    main()