import os
import pandas as pd
import json
import re
from pathlib import Path
import logging
from datetime import datetime
import fitz  # PyMuPDF
import zipfile
import olefile
import struct

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('document_conversion.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class DocumentConverter:
    def __init__(self, input_path, output_path):
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
        self.logs_path = Path("conversion_logs")
        
        # 디렉토리 생성
        self.output_path.mkdir(exist_ok=True)
        self.logs_path.mkdir(exist_ok=True)
        
        # 결과 저장용 딕셔너리
        self.conversion_results = {
            'total_files': 0,
            'successful_files': [],
            'failed_files': [],
            'short_files': [],
            'statistics': {}
        }
    
    def clean_text(self, text, filename):
        """텍스트 정제 및 전처리"""
        if not text:
            return ""
        
        # 파일명 마킹 추가
        cleaned_text = f"[문서: {filename}]\n\n"
        
        # 기본 정제
        text = re.sub(r'\s+', ' ', text)  # 연속된 공백을 하나로
        text = re.sub(r'\n\s*\n', '\n\n', text)  # 연속된 줄바꿈 정리
        
        # 구조 태그 제거 또는 마킹
        text = re.sub(r'\[이미지\].*?\[/이미지\]', '[이미지 생략됨]', text, flags=re.DOTALL)
        text = re.sub(r'\[표\].*?\[/표\]', '[표 생략됨]', text, flags=re.DOTALL)
        text = re.sub(r'\[그림\].*?\[/그림\]', '[그림 생략됨]', text, flags=re.DOTALL)
        
        # 특수문자 정리 (한글, 영문, 숫자, 기본 문장부호 유지)
        text = re.sub(r'[^\w\s가-힣.,!?;:()\[\]{}"\'-]', '', text)
        
        # 문장 단위로 분리하여 정제
        sentences = re.split(r'[.!?]+', text)
        cleaned_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 5:  # 너무 짧은 문장 제거
                cleaned_sentences.append(sentence)
        
        cleaned_text += '. '.join(cleaned_sentences) + '.'
        
        return cleaned_text.strip()
    
    def extract_pdf_text(self, pdf_path):
        """PDF 파일에서 텍스트 추출"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = page.get_text()
                text += page_text + "\n"
            
            # 문서를 닫기 전에 페이지 수 저장
            page_count = len(doc)
            doc.close()
            
            return {
                'success': True,
                'text': text,
                'pages': page_count,
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'text': '',
                'pages': 0,
                'error': str(e)
            }
    
    def extract_hwp_text_simple(self, hwp_path):
        """HWP 파일에서 간단한 텍스트 추출 (OLE 구조 기반)"""
        try:
            if not olefile.isOleFile(hwp_path):
                return {
                    'success': False,
                    'text': '',
                    'pages': 0,
                    'error': '올바른 HWP 파일이 아닙니다.'
                }
            
            ole = olefile.OleFileIO(hwp_path)
            text = ""
            
            # HWP 파일의 기본 구조에서 텍스트 추출 시도
            try:
                # DocInfo 스트림에서 정보 추출
                if ole.exists('DocInfo'):
                    try:
                        doc_info = ole.openstream('DocInfo').read()
                        # 간단한 텍스트 정보 추출
                        text += "문서 정보: " + str(doc_info[:200]) + "\n"
                    except:
                        pass
                
                # BodyText 스트림에서 텍스트 추출 시도
                if ole.exists('BodyText'):
                    try:
                        body_text = ole.openstream('BodyText').read()
                        # 바이너리 데이터에서 텍스트 추출
                        try:
                            # UTF-16으로 디코딩 시도
                            decoded_text = body_text.decode('utf-16', errors='ignore')
                            # 한글 텍스트만 추출
                            korean_text = re.findall(r'[가-힣\s]+', decoded_text)
                            text += ' '.join(korean_text)
                        except:
                            # 다른 인코딩 시도
                            try:
                                decoded_text = body_text.decode('cp949', errors='ignore')
                                korean_text = re.findall(r'[가-힣\s]+', decoded_text)
                                text += ' '.join(korean_text)
                            except:
                                # 바이너리에서 직접 한글 추출 시도
                                try:
                                    # 바이너리 데이터에서 한글 문자 패턴 찾기
                                    korean_pattern = re.compile(b'[\x80-\xff]+')
                                    matches = korean_pattern.findall(body_text)
                                    for match in matches:
                                        try:
                                            decoded = match.decode('cp949', errors='ignore')
                                            if re.search(r'[가-힣]', decoded):
                                                text += decoded + " "
                                        except:
                                            continue
                                except:
                                    text += "텍스트 추출 실패"
                    except Exception as stream_error:
                        text += f"스트림 읽기 실패: {str(stream_error)}"
                
                ole.close()
                
                if len(text.strip()) > 10:
                    return {
                        'success': True,
                        'text': text,
                        'pages': 1,  # HWP는 페이지 수를 정확히 알기 어려움
                        'error': None
                    }
                else:
                    return {
                        'success': False,
                        'text': '',
                        'pages': 0,
                        'error': '텍스트가 너무 짧거나 추출 실패'
                    }
                    
            except Exception as e:
                try:
                    ole.close()
                except:
                    pass
                return {
                    'success': False,
                    'text': '',
                    'pages': 0,
                    'error': f'HWP 텍스트 추출 오류: {str(e)}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'text': '',
                'pages': 0,
                'error': f'HWP 파일 처리 오류: {str(e)}'
            }
    
    def find_document_files(self):
        """문서 파일 찾기"""
        logging.info("=== 문서 파일 탐색 시작 ===")
        
        pdf_files = list(self.input_path.rglob('*.pdf'))
        hwp_files = list(self.input_path.rglob('*.hwp'))
        
        all_files = pdf_files + hwp_files
        
        logging.info(f"발견된 파일 수:")
        logging.info(f"  PDF: {len(pdf_files)}개")
        logging.info(f"  HWP: {len(hwp_files)}개")
        logging.info(f"  총계: {len(all_files)}개")
        
        return all_files
    
    def convert_documents(self):
        """모든 문서 변환"""
        logging.info("=== 문서 변환 시작 ===")
        
        files = self.find_document_files()
        self.conversion_results['total_files'] = len(files)
        
        if not files:
            logging.info("변환할 문서 파일을 찾을 수 없습니다.")
            return
        
        for i, file_path in enumerate(files, 1):
            logging.info(f"처리 중 ({i}/{len(files)}): {file_path.name}")
            
            # 파일 확장자에 따른 처리
            if file_path.suffix.lower() == '.pdf':
                result = self.extract_pdf_text(file_path)
            elif file_path.suffix.lower() == '.hwp':
                result = self.extract_hwp_text_simple(file_path)
            else:
                result = {
                    'success': False,
                    'text': '',
                    'pages': 0,
                    'error': '지원하지 않는 파일 형식'
                }
            
            # 텍스트 정제
            if result['success']:
                cleaned_text = self.clean_text(result['text'], file_path.name)
                result['cleaned_text'] = cleaned_text
                result['cleaned_length'] = len(cleaned_text)
            
            # 결과 처리
            file_info = {
                'file_name': file_path.name,
                'file_path': str(file_path),
                'file_type': file_path.suffix.lower(),
                'success': result['success'],
                'pages': result['pages'],
                'text_length': result.get('cleaned_length', 0),
                'error': result.get('error', None)
            }
            
            if result['success']:
                # 성공한 경우 텍스트 파일 저장
                output_file = self.output_path / f"{file_path.stem}.txt"
                try:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(result['cleaned_text'])
                    
                    logging.info(f"  성공: {result['pages']}페이지, {result['cleaned_length']}자")
                    
                    # 짧은 파일 체크
                    if result['cleaned_length'] <= 100:
                        self.conversion_results['short_files'].append(file_info)
                        logging.warning(f"  경고: 텍스트가 짧음 ({result['cleaned_length']}자)")
                    
                    self.conversion_results['successful_files'].append(file_info)
                    
                except Exception as e:
                    logging.error(f"  파일 저장 실패: {e}")
                    file_info['error'] = f"파일 저장 실패: {e}"
                    self.conversion_results['failed_files'].append(file_info)
            else:
                logging.error(f"  실패: {result['error']}")
                self.conversion_results['failed_files'].append(file_info)
        
        # 통계 계산
        self._calculate_statistics()
        
        logging.info("=== 문서 변환 완료 ===")
    
    def _calculate_statistics(self):
        """변환 통계 계산"""
        successful_count = len(self.conversion_results['successful_files'])
        failed_count = len(self.conversion_results['failed_files'])
        short_count = len(self.conversion_results['short_files'])
        total_count = self.conversion_results['total_files']
        
        # 성공률 계산
        success_rate = (successful_count / total_count * 100) if total_count > 0 else 0
        
        # 평균 텍스트 길이 계산
        text_lengths = [f['text_length'] for f in self.conversion_results['successful_files']]
        avg_length = sum(text_lengths) / len(text_lengths) if text_lengths else 0
        
        self.conversion_results['statistics'] = {
            'total_files': total_count,
            'successful_files': successful_count,
            'failed_files': failed_count,
            'short_files': short_count,
            'success_rate': success_rate,
            'average_text_length': avg_length,
            'min_text_length': min(text_lengths) if text_lengths else 0,
            'max_text_length': max(text_lengths) if text_lengths else 0
        }
    
    def save_results(self):
        """결과 저장"""
        logging.info("=== 결과 저장 ===")
        
        # 성공한 파일 목록 CSV 저장
        if self.conversion_results['successful_files']:
            successful_df = pd.DataFrame(self.conversion_results['successful_files'])
            successful_file = self.logs_path / 'successful_conversions.csv'
            successful_df.to_csv(successful_file, index=False, encoding='utf-8')
            logging.info(f"성공한 파일 목록 저장: {successful_file}")
        
        # 실패한 파일 목록 CSV 저장
        if self.conversion_results['failed_files']:
            failed_df = pd.DataFrame(self.conversion_results['failed_files'])
            failed_file = self.logs_path / 'failed_files.csv'
            failed_df.to_csv(failed_file, index=False, encoding='utf-8')
            logging.info(f"실패한 파일 목록 저장: {failed_file}")
        
        # 짧은 파일 목록 저장
        if self.conversion_results['short_files']:
            short_df = pd.DataFrame(self.conversion_results['short_files'])
            short_file = self.logs_path / 'short_files.csv'
            short_df.to_csv(short_file, index=False, encoding='utf-8')
            logging.info(f"짧은 파일 목록 저장: {short_file}")
            
            # 짧은 파일 목록 텍스트 파일로도 저장
            short_list_file = self.logs_path / 'short_files.txt'
            with open(short_list_file, 'w', encoding='utf-8') as f:
                f.write("=== 텍스트가 100자 이하인 파일 목록 ===\n\n")
                for file_info in self.conversion_results['short_files']:
                    f.write(f"파일명: {file_info['file_name']}\n")
                    f.write(f"텍스트 길이: {file_info['text_length']}자\n")
                    f.write(f"파일 경로: {file_info['file_path']}\n")
                    f.write("-" * 50 + "\n")
            logging.info(f"짧은 파일 목록 텍스트 저장: {short_list_file}")
        
        # 전체 결과 JSON 저장
        results_file = self.logs_path / 'conversion_results.json'
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.conversion_results, f, ensure_ascii=False, indent=2, default=str)
        
        logging.info(f"전체 결과 저장: {results_file}")
    
    def create_summary_report(self):
        """요약 보고서 생성"""
        logging.info("=== 요약 보고서 생성 ===")
        
        stats = self.conversion_results['statistics']
        
        report = f"""# 문서 변환 결과 보고서

## 📊 변환 통계
- **총 파일 수**: {stats['total_files']}개
- **성공**: {stats['successful_files']}개
- **실패**: {stats['failed_files']}개
- **짧은 파일**: {stats['short_files']}개
- **성공률**: {stats['success_rate']:.1f}%

## 📄 텍스트 통계
- **평균 텍스트 길이**: {stats['average_text_length']:.0f}자
- **최소 텍스트 길이**: {stats['min_text_length']}자
- **최대 텍스트 길이**: {stats['max_text_length']}자

## 📁 생성된 파일
- **텍스트 파일**: {stats['successful_files']}개 (.txt)
- **성공 목록**: successful_conversions.csv
- **실패 목록**: failed_files.csv
- **짧은 파일 목록**: short_files.csv, short_files.txt
- **전체 결과**: conversion_results.json

## 🎯 다음 단계
1. **짧은 파일 검토** - 100자 이하 파일 품질 확인
2. **실패 파일 분석** - 변환 실패 원인 파악
3. **텍스트 청킹** - RAG 시스템을 위한 청킹 수행
4. **FAISS 임베딩** - 벡터 저장소 구축

---
생성 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        report_file = self.logs_path / 'conversion_report.md'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logging.info(f"요약 보고서 저장: {report_file}")
    
    def print_summary(self):
        """변환 요약 출력"""
        stats = self.conversion_results['statistics']
        
        print("\n" + "="*60)
        print("📊 문서 변환 완료 요약")
        print("="*60)
        print(f"총 시도 파일 수: {stats['total_files']}개")
        print(f"성공 파일 수: {stats['successful_files']}개")
        print(f"실패 파일 수: {stats['failed_files']}개")
        print(f"짧은 파일 수: {stats['short_files']}개")
        print(f"성공률: {stats['success_rate']:.1f}%")
        print(f"평균 텍스트 길이: {stats['average_text_length']:.0f}자")
        print("="*60)
        
        if stats['short_files'] > 0:
            print(f"\n⚠️  주의: {stats['short_files']}개 파일이 100자 이하입니다.")
            print("   conversion_logs/short_files.txt 파일을 확인하세요.")
        
        if stats['failed_files'] > 0:
            print(f"\n❌ 실패: {stats['failed_files']}개 파일 변환에 실패했습니다.")
            print("   conversion_logs/failed_files.csv 파일을 확인하세요.")
    
    def run_conversion(self):
        """전체 변환 프로세스 실행"""
        logging.info("=== 문서 변환 프로세스 시작 ===")
        
        # 1. 문서 변환
        self.convert_documents()
        
        # 2. 결과 저장
        self.save_results()
        
        # 3. 요약 보고서 생성
        self.create_summary_report()
        
        # 4. 요약 출력
        self.print_summary()
        
        logging.info("=== 문서 변환 프로세스 완료 ===")

if __name__ == "__main__":
    # 경로 설정
    input_path = r"C:\Users\user\Desktop\코드잇 스프린트1\AI 개발자\미션제출 모음\코드잇 프로젝트 모음\중급 프로젝트\base_data\extracted_files-20250722T073504Z-1-001\files"
    output_path = r"C:\Users\user\Desktop\코드잇 스프린트1\AI 개발자\미션제출 모음\코드잇 프로젝트 모음\중급 프로젝트\processed_data"
    
    # 변환기 생성 및 실행
    converter = DocumentConverter(input_path, output_path)
    converter.run_conversion() 