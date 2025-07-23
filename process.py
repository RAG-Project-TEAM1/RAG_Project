#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Linux 가상환경에서 한글 파일 인코딩 문제 해결 스크립트
Windows에서 생성된 한글 파일을 Linux에서 읽을 때 발생하는 인코딩 문제를 해결합니다.
"""

import os
import sys
import glob
from pathlib import Path

def check_environment():
    """환경 정보 확인"""
    print("=" * 50)
    print("환경 정보 확인")
    print("=" * 50)
    print(f"Python 버전: {sys.version}")
    print(f"기본 인코딩: {sys.getdefaultencoding()}")
    print(f"현재 디렉토리: {os.getcwd()}")
    print("=" * 50)

def detect_encoding(file_path):
    """파일 인코딩 감지"""
    encodings = ['cp949', 'euc-kr', 'utf-8', 'utf-16', 'latin1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                # 한글이 포함되어 있는지 확인
                if any('\u3131' <= char <= '\u318E' or '\uAC00' <= char <= '\uD7A3' for char in content):
                    print(f"  ✅ {encoding}: 한글 감지됨 ({len(content)}자)")
                    return encoding, content
                elif len(content.strip()) > 0:
                    print(f"  ⚠️ {encoding}: 텍스트 있음 ({len(content)}자)")
                    return encoding, content
        except UnicodeDecodeError:
            print(f"  ❌ {encoding}: 실패")
            continue
        except Exception as e:
            print(f"  ❌ {encoding}: 오류 - {e}")
            continue
    
    return None, None

def fix_single_file(file_path, output_path=None):
    """단일 파일 인코딩 수정"""
    print(f"\n🔄 처리 중: {file_path}")
    
    # 인코딩 감지
    encoding, content = detect_encoding(file_path)
    
    if encoding and content:
        # 출력 파일명 설정
        if output_path is None:
            file_stem = Path(file_path).stem
            file_suffix = Path(file_path).suffix
            output_path = f"{file_stem}_fixed{file_suffix}"
        
        # UTF-8로 저장
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 성공: {output_path} ({len(content)}자)")
            return True
        except Exception as e:
            print(f"❌ 저장 실패: {e}")
            return False
    else:
        print(f"❌ 인코딩 감지 실패")
        return False

def fix_all_files(directory='.', pattern='*.txt'):
    """모든 파일 일괄 수정"""
    print(f"\n🚀 일괄 수정 시작: {directory}/{pattern}")
    
    # 파일 목록 찾기
    files = glob.glob(os.path.join(directory, pattern))
    files = [f for f in files if not f.endswith('_fixed.txt')]
    
    if not files:
        print("📁 처리할 파일이 없습니다.")
        return
    
    print(f"📄 발견된 파일: {len(files)}개")
    
    success_count = 0
    failure_count = 0
    
    for file_path in files:
        if fix_single_file(file_path):
            success_count += 1
        else:
            failure_count += 1
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("수정 결과 요약")
    print("=" * 50)
    print(f"📄 총 파일: {len(files)}개")
    print(f"✅ 성공: {success_count}개")
    print(f"❌ 실패: {failure_count}개")
    print(f" 성공률: {success_count/len(files)*100:.1f}%")
    print("=" * 50)

def main():
    """메인 함수"""
    print("🔧 Linux 가상환경 한글 인코딩 수정 도구")
    print("Windows에서 생성된 한글 파일의 인코딩 문제를 해결합니다.")
    
    # 환경 확인
    check_environment()
    
    # 사용자 선택
    print("\n📋 작업 선택:")
    print("1. 모든 txt 파일 일괄 수정")
    print("2. 특정 파일만 수정")
    print("3. 환경 정보만 확인")
    
    choice = input("\n선택하세요 (1-3): ").strip()
    
    if choice == '1':
        fix_all_files()
    elif choice == '2':
        filename = input("파일명을 입력하세요: ").strip()
        if os.path.exists(filename):
            fix_single_file(filename)
        else:
            print(f"❌ 파일을 찾을 수 없습니다: {filename}")
    elif choice == '3':
        print("환경 정보만 확인했습니다.")
    else:
        print("❌ 잘못된 선택입니다.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        print("스크립트를 다시 실행해보세요.") 