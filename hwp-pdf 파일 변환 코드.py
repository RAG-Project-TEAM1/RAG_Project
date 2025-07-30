# HWP 파일 일괄 PDF 변환 프로그램
# 필요: pywin32, 한글(HWP) 프로그램 설치
# 사용법: src_folder, dst_folder 경로를 수정 후 실행
import win32com.client
import os
import glob
import shutil
import uuid

# HWP 파일을 PDF로 안전하게 변환 (임시 파일 및 예외 처리 포함)
def hwp_to_pdf_safe(hwp_path, pdf_path):
    temp_hwp = f"temp_{uuid.uuid4().hex}.hwp"
    temp_pdf = f"temp_{uuid.uuid4().hex}.pdf"
    shutil.copy2(hwp_path, temp_hwp)
    hwp = None
    try:
        hwp = win32com.client.Dispatch("HWPFrame.HwpObject")
        hwp.RegisterModule("FilePathCheckDLL", "SecurityModule")
        hwp.Open(os.path.abspath(temp_hwp), "", "")
        hwp.SaveAs(os.path.abspath(temp_pdf), "PDF", "")
        hwp.Quit()
        shutil.move(temp_pdf, pdf_path)
        print(f"[완료] {pdf_path}")
    except Exception as e:
        print(f"[실패] {hwp_path} / 오류: {e}")
    finally:
        # 임시 파일 정리
        if hwp is not None:
            try:
                hwp.Quit()
            except Exception:
                pass
        if os.path.exists(temp_hwp):
            try:
                os.remove(temp_hwp)
            except Exception:
                pass
        if os.path.exists(temp_pdf):
            try:
                os.remove(temp_pdf)
            except Exception:
                pass

# 폴더 내 모든 HWP 파일을 PDF로 변환
def batch_hwp_to_pdf(src_folder, dst_folder):
    os.makedirs(dst_folder, exist_ok=True)
    hwp_files = glob.glob(os.path.join(src_folder, "*.hwp"))
    if not hwp_files:
        print("변환할 HWP 파일이 없습니다.")
        return
    for hwp_file in hwp_files:
        filename = os.path.splitext(os.path.basename(hwp_file))[0]
        pdf_path = os.path.join(dst_folder, filename + ".pdf")
        hwp_to_pdf_safe(hwp_file, pdf_path)

if __name__ == "__main__":
    # 아래 경로를 본인 환경에 맞게 수정하세요
    src_folder = r"C:\files"         # HWP 파일 폴더 경로
    dst_folder = r"C:\pdf_output"        # PDF 저장 폴더
    batch_hwp_to_pdf(src_folder, dst_folder) 