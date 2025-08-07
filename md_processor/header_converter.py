import re
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class LineInfo:
    """라인 정보를 담는 데이터 클래스"""
    original: str
    type: str
    level: int
    content: str
    line_index: int
    is_consecutive: bool = False
    should_remove: bool = False

class OptimizedMarkdownConverter:
    """
    Markdown 문서의 구조를 자동으로 분석하고 의미 있는 제목 헤더로 변환하는 도구입니다.
    목차(TOC) 감지 및 제거 기능
    
    주요 기능:
        - 로마 숫자, 계층형 숫자(1.1, 1.2.3 등) 기반의 섹션 인식
        - 목차 섹션 자동 감지 및 일반 텍스트로 유지
        - 점 없는 숫자 패턴 (1 추진목표) 지원
        - 심볼(□, ○, • 등)은 헤더로 변환하지 않음
        - # (H1)과 ## (H2) 레벨로만 구성
    """    
    def __init__(self):
        self.max_header_length = 60 
        self.min_header_length = 2
        self.enable_consecutive_header_removal = True
        
        # 정규식 패턴들을 카테고리별로 정리
        self.patterns = self._compile_patterns()
        
        # 로마 숫자 추적을 단순화
        self.has_roman_numerals = False
        
    def _compile_patterns(self) -> Dict[str, Dict[str, re.Pattern]]:
        """패턴들을 카테고리별로 정리하여 컴파일"""
        return {
            'roman': {
                'unicode': re.compile(r'^(Ⅰ|Ⅱ|Ⅲ|Ⅳ|Ⅴ|Ⅵ|Ⅶ|Ⅷ|Ⅸ|Ⅹ)\.?\s*(.+)'),
                'ascii': re.compile(r'^([IVX]+)\.?\s*(.+)', re.IGNORECASE)
            },
            'numbered': {
                'hierarchical': re.compile(r'^(\d+(?:\.\d+)*)\.\s*(.+)'),
                'simple': re.compile(r'^(\d+)\s+(.+)')  # 점 없는 숫자 패턴 추가
            },
            'symbols': {
                'square': re.compile(r'^□\s*(.+)'),
                'note': re.compile(r'^※\s*(.+)'),
                'circle': re.compile(r'^○\s*(.+)'),
                'bullet': re.compile(r'^•\s*(.+)'),
                'dash': re.compile(r'^-\s*(.+)')
            },
            'exclude': {
                'parentheses': re.compile(r'^\d+\)\s*(.+)'),
                'korean_paren': re.compile(r'^[가-힣]\)\s*(.+)'),
                'alpha_paren': re.compile(r'^[a-zA-Z]\)\s*(.+)')
            },
            'cleanup': {
                'markdown_header': re.compile(r'^#+\s*(.*)'),
                'meaningless': re.compile(r'^[#\s]*$|^[#\s·•\-_=]*$|^[#\s]*\.\s*$')
            },
            'toc': {
                # 목차 패턴: 로마숫자 + 텍스트 + 점선 + 페이지번호
                'roman_toc': re.compile(r'^(Ⅰ|Ⅱ|Ⅲ|Ⅳ|Ⅴ|Ⅵ|Ⅶ|Ⅷ|Ⅸ|Ⅹ)\.?\s*(.+?)[\s·]{2,}\s*\d+$'),
                # 숫자 목차: 1. 제목 ··· 페이지
                'numbered_toc': re.compile(r'^(\d+(?:\.\d+)*)\.\s*(.+?)[\s·]{2,}\s*\d+$'),
                # 일반 목차: 텍스트 ··· 페이지
                'general_toc': re.compile(r'^(.+?)[\s·]{3,}\s*\d+$'),
                # 점선만 있는 라인
                'dotted_line': re.compile(r'^[·\s]{3,}$')
            }
        }

    def _is_toc_line(self, line: str) -> bool:
        """목차 라인인지 판단"""
        line = line.strip()
        
        # 빈 라인이거나 점선만 있는 라인
        if not line or self.patterns['toc']['dotted_line'].match(line):
            return True
            
        # 로마숫자 목차 패턴
        if self.patterns['toc']['roman_toc'].match(line):
            return True
            
        # 숫자 목차 패턴
        if self.patterns['toc']['numbered_toc'].match(line):
            return True
            
        # 일반 목차 패턴 (제목··페이지)
        if self.patterns['toc']['general_toc'].match(line):
            return True
            
        return False

    def _detect_toc_section(self, lines: List[str]) -> Tuple[int, int]:
        """
        목차 섹션의 시작과 끝을 감지
        Returns: (start_index, end_index) - 목차가 없으면 (-1, -1)
        """
        toc_start = -1
        toc_end = -1
        consecutive_toc_count = 0
        
        for i, line in enumerate(lines):
            if self._is_toc_line(line):
                if toc_start == -1:
                    toc_start = i
                consecutive_toc_count += 1
                toc_end = i
            else:
                # 목차가 아닌 라인이 나왔을 때
                if consecutive_toc_count >= 3:  # 최소 3줄 이상의 목차 패턴이 있어야 목차로 인정
                    break
                else:
                    # 목차 패턴이 충분하지 않으면 리셋
                    toc_start = -1
                    toc_end = -1
                    consecutive_toc_count = 0
        
        # 목차 패턴이 충분하지 않으면 목차 없음으로 처리
        if consecutive_toc_count < 3:
            return -1, -1
            
        return toc_start, toc_end

    def _is_valid_text(self, text: str) -> bool:
        """텍스트가 유효한 헤더 텍스트인지 통합 검증"""
        if not text or len(text.strip()) < self.min_header_length:
            return False
        
        clean_text = text.strip()
        if len(clean_text) > self.max_header_length:
            return False
        
        # 의미없는 패턴들을 통합
        meaningless_patterns = [
            r'^[·•\-_=]{1,5}$',
            r'^\d+\.?$',
            r'^\[.*\].*···\s*\d+$',
            r'^<.*>$',
            r'^ㅇ\s',
            r'.*\(\d{4}\.\d{1,2}\.\d{1,2}\.?기준\)',
            r'.*···\s*\d+$',
            r'.*[\s·]{3,}\s*\d+$'  # 목차 패턴 추가
        ]
        
        return not any(re.match(pattern, clean_text) for pattern in meaningless_patterns)

    def _extract_roman_numeral(self, line: str) -> Optional[Tuple[str, str]]:
        """로마 숫자 추출 통합 메서드 (목차 제외)"""
        # 목차 패턴인지 먼저 확인
        if self._is_toc_line(line):
            return None
            
        # 유니코드 로마 숫자 먼저 확인
        match = self.patterns['roman']['unicode'].match(line)
        if match:
            return match.group(1), match.group(2).strip()
        
        # ASCII 로마 숫자 확인
        match = self.patterns['roman']['ascii'].match(line)
        if match and self._is_valid_roman_numeral(match.group(1)):
            return match.group(1), match.group(2).strip()
        
        return None

    def _is_valid_roman_numeral(self, text: str) -> bool:
        """로마 숫자 유효성 검사"""
        valid_romans = {
            'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X',
            'XI', 'XII', 'XIII', 'XIV', 'XV', 'XVI', 'XVII', 'XVIII', 'XIX', 'XX'
        }
        return text.upper() in valid_romans

    def _classify_line_type(self, line: str, line_index: int, in_toc_section: bool = False) -> LineInfo:
        """라인 분류 로직을 단순화 (목차 처리 추가)"""
        line = line.strip()
        
        if not line:
            return LineInfo('', 'empty', 0, '', line_index)
        
        # 목차 섹션 내의 라인은 모두 텍스트로 처리
        if in_toc_section:
            return LineInfo(line, 'toc_content', 0, line, line_index)
        
        # 제외 패턴 먼저 확인
        for pattern in self.patterns['exclude'].values():
            if pattern.match(line):
                return LineInfo(line, 'excluded', 0, line, line_index)
        
        # 로마 숫자 확인
        roman_result = self._extract_roman_numeral(line)
        if roman_result:
            roman_num, header_text = roman_result
            if self._is_valid_text(header_text):
                self.has_roman_numerals = True
                return LineInfo(line, 'roman', 1, line, line_index)  # 원본 line 유지
        
        # 계층형 숫자 확인 (점 있는 버전)
        match = self.patterns['numbered']['hierarchical'].match(line)
        if match:
            number_part, header_text = match.groups()
            if self._is_valid_text(header_text):
                # 로마 숫자가 있으면: 1.x는 H2, 로마 숫자가 없으면: 1은 H1, 1.x는 H2
                if self.has_roman_numerals:
                    level = 2  # 로마 숫자 다음은 모두 H2
                else:
                    level = 1 if number_part.count('.') == 0 else 2
                return LineInfo(line, 'numbered', level, line, line_index)  # 원본 line 유지
        
        # 점 없는 숫자 패턴 (1 추진목표)
        match = self.patterns['numbered']['simple'].match(line)
        if match:
            number_part, header_text = match.groups()
            if self._is_valid_text(header_text):
                # 로마 숫자가 있으면 H2, 없으면 H1
                level = 2 if self.has_roman_numerals else 1
                return LineInfo(line, 'numbered_simple', level, line, line_index)  # 원본 line 유지
        
        # 심볼 패턴들은 헤더로 처리하지 않음 (일반 텍스트로 유지)
        # for symbol_type, pattern in self.patterns['symbols'].items():
        #     match = pattern.match(line)
        #     if match and self._is_valid_text(match.group(1)):
        #         return LineInfo(line, symbol_type, 2, line, line_index)
        
        # 제목 형태 확인 (로마 숫자가 없는 경우만)
        if not self.has_roman_numerals and self._looks_like_title(line):
            return LineInfo(line, 'title', 1, line, line_index)  # 원본 line 유지
        
        return LineInfo(line, 'text', 0, line, line_index)

    def _looks_like_title(self, line: str) -> bool:
        """제목 판별 로직 단순화"""
        if len(line) > 50:
            return False
        
        # 제목 키워드가 있는 경우만
        title_keywords = ['목적', '개요', '요약', '결론', '배경']
        return any(keyword in line for keyword in title_keywords)

    def _mark_consecutive_headers(self, lines: List[LineInfo]) -> List[LineInfo]:
        """연속되는 헤더 라인을 제거하거나 텍스트로 변환하는 전처리 함수"""
        if not self.enable_consecutive_header_removal:
            return lines
        
        result = []
        consecutive_count = 0
        
        for i, line_info in enumerate(lines):
            is_header = line_info.level > 0
            next_is_header = (i + 1 < len(lines) and lines[i + 1].level > 0)
            
            if is_header:
                consecutive_count += 1
                
                # 제거 조건들을 명확히 분리
                should_remove = (
                    consecutive_count >= 2 or
                    line_info.content.strip().endswith(':') or 
                    next_is_header  
                )
                
                if should_remove:
                    # 헤더를 텍스트로 변환
                    clean_content = re.sub(r'^#+\s*', '', line_info.content).strip()
                    line_info = LineInfo(
                        original=clean_content,
                        type='converted_text',
                        level=0,
                        content=clean_content,
                        line_index=line_info.line_index,
                        should_remove=True
                    )
                    consecutive_count = 0 
            else:
                consecutive_count = 0
            
            result.append(line_info)
        
        return result

    def convert_document(self, text: str) -> str:
        """메인 변환 로직 (목차 처리 추가)"""
        # 기존 헤더 정리
        cleaned_text = self._clean_existing_headers(text)
        lines = cleaned_text.split('\n')
        
        # 목차 섹션 감지
        toc_start, toc_end = self._detect_toc_section(lines)
        
        if toc_start != -1:
            print(f"목차 섹션 감지됨: {toc_start+1}줄 ~ {toc_end+1}줄 (총 {toc_end-toc_start+1}줄)")
        
        self.has_roman_numerals = False
        
        # 라인별 분류 (목차 섹션 정보 전달)
        analyzed_lines = []
        for i, line in enumerate(lines):
            in_toc = toc_start <= i <= toc_end if toc_start != -1 else False
            line_info = self._classify_line_type(line, i, in_toc)
            analyzed_lines.append(line_info)
        
        # 연속 헤더 처리
        processed_lines = self._mark_consecutive_headers(analyzed_lines)
        
        # 마크다운 변환
        return self._lines_to_markdown(processed_lines)

    def _clean_existing_headers(self, text: str) -> str:
        """기존 마크다운 헤더 정리"""
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            match = self.patterns['cleanup']['markdown_header'].match(line.strip())
            if match:
                cleaned_lines.append(match.group(1).strip())
            else:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)

    def _lines_to_markdown(self, lines: List[LineInfo]) -> str:
        """LineInfo 리스트를 마크다운으로 변환"""
        converted_lines = []
        removed_count = 0
        toc_lines_removed = 0
        
        for line_info in lines:
            if line_info.type == 'toc_content':
                # 목차 내용은 그대로 유지하되 별도 카운트
                converted_lines.append(line_info.original)
                toc_lines_removed += 1
            elif line_info.level > 0:
                header = '#' * line_info.level
                converted_lines.append(f"{header} {line_info.content}")
            elif line_info.should_remove:
                converted_lines.append(line_info.original)
                removed_count += 1
            else:
                converted_lines.append(line_info.original)
        
        # 연속 빈 줄 정리
        final_lines = self._clean_empty_lines(converted_lines)
        
        if toc_lines_removed > 0:
            print(f"목차 처리: {toc_lines_removed}개 라인을 일반 텍스트로 유지")
        
        if removed_count > 0:
            print(f"연속 헤더 제거: {removed_count}개 헤더를 본문으로 변환")
        
        return '\n'.join(final_lines)

    def _clean_empty_lines(self, lines: List[str]) -> List[str]:
        """연속된 빈 줄 정리"""
        result = []
        prev_empty = False
        
        for line in lines:
            is_empty = line.strip() == ''
            if not (is_empty and prev_empty):
                result.append(line)
            prev_empty = is_empty
        
        return result

    def process_file(self, input_path: str, output_path: Optional[str] = None) -> bool:
        """파일 처리"""
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            converted_content = self.convert_document(content)
            
            if output_path is None:
                input_file = Path(input_path)
                output_path = input_file.parent / f"{input_file.stem}_cleaned.md"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(converted_content)
            
            print(f"변환 완료: {input_path} → {output_path}")
            print(f"   로마 숫자 사용: {'예' if self.has_roman_numerals else '아니오'}")
            
            return True
            
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            return False

    def set_consecutive_header_removal_enabled(self, enabled: bool):
        """연속 헤더 제거 기능 설정"""
        self.enable_consecutive_header_removal = enabled
        print(f"🔧 연속 헤더 제거 기능: {'활성화' if enabled else '비활성화'}")

    def process_directory_recursive(self, root_directory: str):
        """디렉토리 내부 모든 하위 디렉토리를 재귀적으로 탐색하여 각 파일을 개별적으로 _cleaned_2.md 생성"""
        root_dir = Path(root_directory)
        
        if not root_dir.exists():
            print(f"❌ 디렉토리를 찾을 수 없습니다: {root_directory}")
            return
        
        # 모든 하위 디렉토리의 .md 파일 탐색
        all_md_files = list(root_dir.rglob("*.md"))
        if not all_md_files:
            print(f"❌ '{root_directory}' 디렉토리에서 .md 파일을 찾을 수 없습니다.")
            return
        
        # 이미 변환된 파일은 제외
        md_files_to_process = []
        for md_file in all_md_files:
            if any(suffix in md_file.stem for suffix in ['_clean', '_cleaned']):
                continue
            md_files_to_process.append(md_file)
        
        if not md_files_to_process:
            print("처리할 .md 파일이 없습니다 (이미 변환된 파일들은 제외됨)")
            return
        
        print(f"'{root_directory}' 내 모든 .md 파일을 탐색합니다 (총 {len(md_files_to_process)}개 파일 발견)")
        print(f"\n각 파일을 개별적으로 변환합니다...")
        
        successful_files = 0
        
        # 각 파일을 개별적으로 처리
        for i, md_file in enumerate(md_files_to_process, 1):
            try:
                # 파일의 상대 경로 계산
                try:
                    relative_path = md_file.relative_to(root_dir)
                except ValueError:
                    relative_path = md_file.name
                
                print(f"\n{i}/{len(md_files_to_process)}. {relative_path} 처리 중...")
                
                # 파일 읽기
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 개별 파일 변환
                converted_content = self.convert_document(content)
                
                # 출력 파일 경로
                original_filename = md_file.stem
                output_filename = f"{original_filename}_cleaned_2.md"
                output_file_path = md_file.parent / output_filename
                
                # 변환된 내용 저장
                with open(output_file_path, 'w', encoding='utf-8') as f:
                    f.write(converted_content)
                
                print(f"   {output_filename} 생성 완료 (위치: {output_file_path.parent})")
                successful_files += 1
                
            except Exception as e:
                print(f"   파일 처리 중 오류 발생: {md_file.name} → {e}")
                continue
        
        print(f"\n총 {successful_files}개 파일의 _cleaned_2.md 생성 완료!")
        print(f"모든 _cleaned_2.md 파일은 원본 파일과 같은 디렉토리에 저장되었습니다.")
        print(f"각 파일에서 의미없는 헤더들이 제거되었습니다.")
        print(f"연속 헤더 제거 기능이 {'적용' if self.enable_consecutive_header_removal else '비활성화'}되었습니다.")
