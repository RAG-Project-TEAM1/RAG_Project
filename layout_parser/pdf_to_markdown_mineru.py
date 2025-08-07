import subprocess
import os
import glob

def process_pdfs_with_mineru(input_dir="/pdfs", output_dir="./output", vram_size="16", lang="korean"):
    """
    MinerU를 사용해 PDF 파일들을 마크다운으로 변환
    """
    # 환경 변수 설정
    env = os.environ.copy()
    env["MINERU_VIRTUAL_VRAM_SIZE"] = vram_size
    
    # PDF 파일 찾기
    pdf_files = glob.glob(f"{input_dir}/*.pdf")
    
    results = {
        "success": [],
        "failed": [],
        "total": len(pdf_files)
    }
    
    if not pdf_files:
        print("PDF 파일을 찾을 수 없습니다.")
        return results
        
    print(f"{len(pdf_files)}개의 PDF 파일을 발견했습니다.")
    
    for pdf_file in pdf_files:
        print(f"\n처리 중: {pdf_file}")
        
        cmd = [
            "mineru", 
            "-p", pdf_file,
            "-o", output_dir,
            "--lang", lang,
            "--output-format", "markdown"
        ]
        
        try:
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ 성공: {os.path.basename(pdf_file)}")
                results["success"].append(pdf_file)
                print(result.stdout)
            else:
                print(f"❌ 실패: {os.path.basename(pdf_file)}")
                print("에러:", result.stderr)
                results["failed"].append(pdf_file)
                
        except Exception as e:
            print(f"❌ 예외 발생: {pdf_file}")
            print(f"에러: {e}")
            results["failed"].append(pdf_file)
    
    print(f"\n처리 완료! 성공: {len(results['success'])}, 실패: {len(results['failed'])}")
    return results