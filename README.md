# 📄 RAG_Project

## 📌 프로젝트 개요
**배경**  
매일 수백 건의 기업 및 정부 제안요청서(RFP)가 게시되지만, 각 요청서는 수십 페이지에 달하여 전부 검토하는 것이 어렵습니다.  
이로 인해 중요한 정보를 빠르게 파악하기 힘들고, 검토 과정이 비효율적으로 진행됩니다.

**목표**  
사용자 요청에 따라 RFP 문서의 내용을 효과적으로 추출·요약하여, 필요한 정보를 즉시 제공하는 **사내 RAG 시스템**을 구현합니다.

**기대 효과**  
- RAG 시스템을 통해 중요한 정보를 신속하게 제공  
- 제안서 검토 시간을 단축  
- 컨설팅 및 분석 업무에 보다 집중할 수 있는 환경 조성

---

## 🖥️ 실습 환경
- **개발 환경**: VS Code + Remote SSH (GCP VM 연결)
- **운영체제**: Ubuntu 20.04 LTS (GCP VM)
- **Python 버전**: 3.10+
- **가상환경**: venv (또는 Conda 가능)
- **Git**: GitHub 원격 저장소 연동
- **LLM API**: OpenAI API (GPT-4/3.5), 필요 시 Hugging Face Transformers
- **GPU**: NVIDIA L4 / CUDA 12.x (GCP AI 가속기 환경)

---
## 🛠️ 기술 스택








## 📂 리포지토리 구조

```plaintext
.
├─ src/                               # RAG 핵심 로직
│  ├─ loader.py                       # 문서 로드 및 전처리
│  ├─ vector_search.py                # 임베딩·인덱스·검색
│  ├─ answer_generation.py            # 프롬프트 작성 및 응답 생성
│  ├─ prompt.py                       # 프롬프트 템플릿 정의
│  ├─ filename_utils.py               # 파일명 정규화·유사도 매칭
│  ├─ enrich.py                       # 요약·후처리 모듈
│  ├─ utils.py                        # 공용 유틸 함수
│  ├─ config.py                       # 환경변수·경로 설정
│  └─ pipeline.py                     # 전체 파이프라인 실행 엔트리
│
├─ pdf_parser/                        # PDF 파싱 계층
│  ├─ converter.py                    # PDF 변환 로직
│  ├─ cli.py                          # 커맨드라인 실행
│  ├─ parsers/                        # 파서 구현체 모음
│  │  ├─ fitz_parser.py
│  │  ├─ plumber_parser.py
│  │  └─ unstructured_parser.py
│  └─ utils/                          # PDF 파서 유틸리티
│     ├─ logging_config.py
│     ├─ page_mapping.py
│     ├─ text_cleaning.py
│     └─ merging.py
│
├─ layout_parser/                     # PDF → Markdown 레이아웃 파서
│  └─ pdf_to_markdown_mineru.py
│
├─ md_processor/                      # Markdown 후처리·청킹
│  ├─ pipeline.py
│  ├─ header_converter.py
│  ├─ null_cleaner.py
│  └─ cli.py
│
├─ notebooks/                         # 실험·데모 노트북
│  └─ demo_rag_workflow.ipynb
│
├─ process.py                         # 전체 파이프라인 실행 스크립트
├─ pdf_to_md_pipeline.py              # PDF → MD 변환 파이프라인 스크립트
├─ parser_documents.py                 # 문서 파싱 실행 스크립트
├─ requirements.txt                    # 프로젝트 의존성 목록
├─ README.md
└─ .gitignore
```
# 시작 가이드
## ⚙️ 설치 방법

### 1. 리포지토리 클론
```
git clone https://github.com/RAG-Project-TEAM1/RAG_Project.git
cd RAG_Project
```

### 2. 가상환경 생성 및 활성화
```
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 의존성 설치
```
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. 환경 변수 설정
```
OPENAI_API_KEY=sk-xxxx
```
## 🚀 실행 방법

### 1. PDF → Markdown 변환
```
python pdf_to_md_pipeline.py --input ./data/input.pdf --output ./data/output.md
```

### 2. 전체 RAG 파이프라인 실행
```
python process.py --query "예)사업 예산이 2억 이상인 사업들 알려줘"
```
### 3. 노트북 환경 실행
```
jupyter notebook notebooks/demo_rag_workflow.ipynb
```



## PDF to Markdown 파이프라인 사용방법
### input_dir -> output_dir
기본 pdfs -> data

### 설치 방법
출처: [MinerU github](https://github.com/opendatalab/MinerU?utm_source=pytorchkr&ref=pytorchkr)
``` 
pip install --upgrade pip
pip install uv
uv pip install -U "mineru[core]"
```
### 사용방법
python pdf_to_md_pipeline.py -i ./pdfs -o ./data --vram-size 16
-i : PDF 파일들이 있는 디렉토리
-o : 출력 디렉토리
--vram-size : MinerU 가상 RAM 크기 (기본값: 16GB)

### 최종 출력
```
/data/
├── file1/
│   └── auto/
│       ├── file1.md                       # 정제된 결과 문서 (Markdown)
│       ├── file1_content_list.json  # 문서 콘텐츠 목록 (text, table, 메타데이터 정보 등)
│       ├── file1_layout.pdf            # 문서 레이아웃 분석 결과 PDF (영역/구조 시각화)
│       ├── file1_middle.json         # 원본 기반 상세 블록 (실제 텍스트·표 위치 및 내용)
│       ├── file1_model.json          # 레이아웃 블록 (본문, 표, 그림 등) 위치와 유형, 신뢰도 분석
│       ├── file1_origin.pdf            # 입력 원본 PDF(가공 전)
│       └── file1_span.pdf              # OCR PDF (핵심 스팬 시각화)
├── file2/
│   └── auto/
│       ├── file2.md                    
│       ├── file2_content_list.json     
...
├── _original_mineru/             # 원본 백업 폴더 (MinerU 정제 전 Markdown 파일)
├── file1.md                            # 폴더 밖의 원본/추가 마크다운 파일
├── file2.md                            # 폴더 밖의 원본/추가 마크다운 파일    
```   
