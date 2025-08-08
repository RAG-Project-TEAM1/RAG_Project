import argparse
import os
import shutil
from layout_parser import process_pdfs_with_mineru
from md_processor.pipeline import process_directory

def backup_original_files(output_dir):
    """MinerU 원본 .md 파일들을 백업"""
    backup_dir = os.path.join(output_dir, "_original_mineru")
    os.makedirs(backup_dir, exist_ok=True)
    
    backed_up_count = 0
    # MinerU 출력 구조: /data/filename/auto/filename.md
    for item in os.listdir(output_dir):
        item_path = os.path.join(output_dir, item)
        if os.path.isdir(item_path) and not item.startswith('_'):
            auto_dir = os.path.join(item_path, 'auto')
            if os.path.exists(auto_dir):
                for file in os.listdir(auto_dir):
                    if file.endswith('.md'):
                        src_path = os.path.join(auto_dir, file)
                        dst_path = os.path.join(backup_dir, file)
                        try:
                            shutil.copy2(src_path, dst_path)
                            backed_up_count += 1
                        except Exception as e:
                            print(f"⚠️ 백업 실패 {file}: {e}")
    
    if backed_up_count > 0:
        print(f"📋 원본 Markdown 파일 {backed_up_count}개 백업 완료")
    
    return backup_dir

def main():
    parser = argparse.ArgumentParser(description="PDF to Markdown 파이프라인")
    parser.add_argument('-i', '--input', required=True, help='PDF 파일들이 있는 디렉토리')
    parser.add_argument('-o', '--output', required=True, help='출력 디렉토리')
    parser.add_argument('--vram-size', default="16", help='MinerU 가상 RAM 크기 (기본값: 16GB)')
    parser.add_argument('--lang', default="korean", help='언어 설정 (기본값: korean)')

    args = parser.parse_args()

    # 입력 디렉토리 확인
    if not os.path.exists(args.input):
        print(f"❌ 입력 디렉토리가 존재하지 않습니다: {args.input}")
        return

    # 출력 디렉토리 생성
    os.makedirs(args.output, exist_ok=True)

    try:
        print("📄 1단계: PDF를 Markdown으로 변환 (MinerU)")
        print("-" * 50)
        
        # 1단계: PDF -> Markdown (MinerU)
        pdf_results = process_pdfs_with_mineru(
            input_dir=args.input,
            output_dir=args.output,
            vram_size=args.vram_size,
            lang=args.lang
        )
        
        if pdf_results["total"] == 0:
            print("❌ 처리할 PDF 파일이 없습니다.")
            return
            
        if len(pdf_results["success"]) == 0:
            print("❌ 성공적으로 변환된 PDF 파일이 없습니다.")
            return

        print(f"✅ PDF 변환 완료: {len(pdf_results['success'])}/{pdf_results['total']}")

        # 원본 파일 백업
        print("\n📋 원본 파일 백업 중...")
        backup_original_files(args.output)

        print("\n🧹 2단계: Markdown 파일 정제")
        print("-" * 50)
        
        # 2단계: Markdown 정제 - 인플레이스 처리
        process_directory(
            input_dir=args.output,
            output_dir=args.output
        )
        
        print("✅ 파이프라인 완료!")
        print(f"📂 출력: {args.output}")
        
        # 간단한 결과 요약
        print(f"\n📊 결과: {len(pdf_results['success'])}/{pdf_results['total']} 성공")
        if pdf_results['failed']:
            print("❌ 실패:")
            for failed_file in pdf_results['failed']:
                print(f"  - {os.path.basename(failed_file)}")

    except Exception as e:
        print(f"❌ 오류: {e}")
        raise

if __name__ == "__main__":
    main()