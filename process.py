import os
import pandas as pd
import json
from pathlib import Path
import re
import fitz  # PyMuPDF
import olefile
from datetime import datetime
import subprocess
import sys

class ImprovedDocumentConverter:
    def __init__(self, input_dir, output_dir, logs_dir):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.logs_dir = Path(logs_dir)
        self.success_count = 0
        self.failure_count = 0
        self.success_log = []
        self.failure_log = []
        
    def clean_text(self, text, filename):
        """텍스트 정리 및 전처리"""
        if not text:
            return ""
        
        # 기본 정리
        text = text.strip()
        
        # 불필요한 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        # 특수 문자 정리 (한글, 영문, 숫자, 기본 문장부호만 유지)
        text = re.sub(r'[^\w\s가-힣.,!?;;:()\[\]{}"\'-]', '', text)
        
        # 연속된 마침표 제거
        text = re.sub(r'\.{2,}', '.', text)
        
        # 빈 줄 제거
        text = re.sub(r'\n\s*\n', '\n', text)
        
        return text.strip()
    
    def extract_pdf_text(self, pdf_path):
        """PDF에서 텍스트 추출"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            print(f"PDF 추출 오류 ({pdf_path}): {e}")
            return ""
    
    def extract_hwp_text_improved(self, hwp_path):
        """HWP에서 텍스트 추출 (개선된 방법)"""
        try:
            if not olefile.isOleFile(hwp_path):
                return ""
            
            ole = olefile.OleFileIO(hwp_path)
            text = ""
            
            # 모든 스트림 확인
            all_streams = ole.listdir()
            print(f"  HWP 스트림 목록: {[stream[0] for stream in all_streams]}")
            
            # 여러 스트림에서 텍스트 추출 시도
            streams_to_try = [
                'PrvText',      # 미리보기 텍스트
                'Contents',     # 내용
                'BodyText',     # 본문 텍스트
                'Section0',     # 섹션 0
                'Section1',     # 섹션 1
                'DocInfo',      # 문서 정보
                'HwpSummaryInformation',  # 요약 정보
                'FileHeader',   # 파일 헤더
                'DocOptions',   # 문서 옵션
            ]
            
            for stream_name in streams_to_try:
                if ole.exists(stream_name):
                    try:
                        stream_content = ole.openstream(stream_name).read()
                        print(f"  스트림 {stream_name} 크기: {len(stream_content)} bytes")
                        
                        # 여러 인코딩 시도
                        for encoding in ['utf-8', 'cp949', 'euc-kr', 'utf-16', 'latin1', 'ascii']:
                            try:
                                decoded_text = stream_content.decode(encoding, errors='ignore')
                                if len(decoded_text.strip()) > len(text):
                                    text = decoded_text
                                    print(f"  인코딩 {encoding}로 {len(decoded_text)}자 추출")
                            except:
                                continue
                    except Exception as e:
                        print(f"  스트림 {stream_name} 처리 오류: {e}")
                        continue
            
            # 모든 스트림에서 텍스트 찾기 시도
            if len(text.strip()) < 500:
                for stream_path in all_streams:
                    stream_name = stream_path[0]
                    if stream_name not in streams_to_try:
                        try:
                            stream_content = ole.openstream(stream_name).read()
                            for encoding in ['utf-8', 'cp949', 'euc-kr']:
                                try:
                                    decoded_text = stream_content.decode(encoding, errors='ignore')
                                    if len(decoded_text.strip()) > len(text) and len(decoded_text.strip()) > 100:
                                        text = decoded_text
                                        print(f"  추가 스트림 {stream_name}에서 {len(decoded_text)}자 추출")
                                except:
                                    continue
                        except:
                            continue
            
            ole.close()
            return text.strip()
            
        except Exception as e:
            print(f"HWP 추출 오류 ({hwp_path}): {e}")
            return ""
    
    def find_document_files(self):
        """PDF와 HWP 파일 찾기"""
        pdf_files = list(self.input_dir.glob("*.pdf"))
        hwp_files = list(self.input_dir.glob("*.hwp"))
        return pdf_files + hwp_files
    
    def convert_documents(self):
        """문서 변환 실행"""
        files = self.find_document_files()
        print(f"📄 변환할 파일 개수: {len(files)}개")
        
        for file_path in files:
            print(f"🔄 처리 중: {file_path.name}")
            
            try:
                # 텍스트 추출
                if file_path.suffix.lower() == '.pdf':
                    text = self.extract_pdf_text(str(file_path))
                elif file_path.suffix.lower() == '.hwp':
                    # HWP 파일은 개선된 방법 사용
                    text = self.extract_hwp_text_improved(str(file_path))
                else:
                    continue
                
                # 텍스트 정리
                cleaned_text = self.clean_text(text, file_path.name)
                
                if cleaned_text and len(cleaned_text) > 100:  # 최소 100자 이상
                    # 결과 저장
                    output_file = self.output_dir / f"{file_path.stem}.txt"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(cleaned_text)
                    
                    # 성공 로그
                    self.success_log.append({
                        'filename': file_path.name,
                        'output_file': output_file.name,
                        'text_length': len(cleaned_text),
                        'original_length': len(text),
                        'timestamp': datetime.now().isoformat()
                    })
                    self.success_count += 1
                    print(f"✅ 성공: {file_path.name} ({len(cleaned_text)}자)")
                else:
                    raise Exception(f"추출된 텍스트가 너무 짧음 ({len(cleaned_text)}자)")
                    
            except Exception as e:
                # 실패 로그
                self.failure_log.append({
                    'filename': file_path.name,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
                self.failure_count += 1
                print(f"❌ 실패: {file_path.name} - {e}")
    
    def save_results(self):
        """결과 저장"""
        # 성공 로그 저장
        success_df = pd.DataFrame(self.success_log)
        success_df.to_csv(self.logs_dir / 'improved_success_log.csv', index=False, encoding='utf-8-sig')
        
        # 실패 로그 저장
        failure_df = pd.DataFrame(self.failure_log)
        failure_df.to_csv(self.logs_dir / 'improved_failure_log.csv', index=False, encoding='utf-8-sig')
        
        # 전체 결과 JSON 저장
        results = {
            'summary': {
                'total_files': len(self.success_log) + len(self.failure_log),
                'success_count': self.success_count,
                'failure_count': self.failure_count,
                'success_rate': self.success_count / (self.success_count + self.failure_count) * 100 if (self.success_count + self.failure_count) > 0 else 0
            },
            'success_files': self.success_log,
            'failure_files': self.failure_log
        }
        
        with open(self.logs_dir / 'improved_conversion_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 결과 저장 완료: {self.logs_dir}")
    
    def print_summary(self):
        """결과 요약 출력"""
        total = self.success_count + self.failure_count
        success_rate = (self.success_count / total * 100) if total > 0 else 0
        
        print("\n" + "="*50)
        print(" 개선된 변환 결과 요약")
        print("="*50)
        print(f"📄 총 파일 수: {total}개")
        print(f"✅ 성공: {self.success_count}개")
        print(f"❌ 실패: {self.failure_count}개")
        print(f" 성공률: {success_rate:.1f}%")
        
        if self.success_log:
            avg_length = sum(log['text_length'] for log in self.success_log) / len(self.success_log)
            print(f"📝 평균 텍스트 길이: {avg_length:.0f}자")
        print("="*50)
    
    def run_conversion(self):
        """전체 변환 프로세스 실행"""
        print("🚀 개선된 문서 변환 시작...")
        self.convert_documents()
        self.save_results()
        self.print_summary()

if __name__ == "__main__":
    # 경로 설정
    input_path = "data/raw/base_data/extracted_files-20250722T073504Z-1-001/files"
    output_path = "data/processed/improved_processed_data"
    logs_path = "data/logs/improved_conversion_logs"
    
    # 디렉토리 생성
    os.makedirs(output_path, exist_ok=True)
    os.makedirs(logs_path, exist_ok=True)
    
    # 변환기 초기화 및 실행
    converter = ImprovedDocumentConverter(input_path, output_path, logs_path)
    converter.run_conversion() 