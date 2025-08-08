# 📄 RAG_Project

## 📃보고서 PDF 파일
https://drive.google.com/file/d/1N4MwpW_2BsCFiBZBrCDfmwM3lv83P9kx/view?usp=sharing

## ✏️ 협업일지 링크
박지수 - https://www.notion.so/23803752e5f9802fa345e748a399a184

박창훈 - https://www.notion.so/Daily-PCH-238ac8e1b95280adaa6fc701ef407b7e

이우진 - https://www.notion.so/2-238816c91f3a80c880ffc05feccf53e8

정민영 - https://www.notion.so/Daily-2382d05d9c468081a528f698cf580863

주대성 - https://www.notion.so/23832d889f8880ba8a1ac7835ce76f4d

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

	•	Python 3.10+
	•	FAISS: 벡터 검색 인덱스
	•	OpenAI GPT API: LLM 응답 생성
	•	PyMuPDF, PDFPlumber, Unstructured: PDF 파싱
	•	MinerU: PDF → Markdown 변환
	•	Pandas, NumPy: 데이터 처리

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

이 프로젝트는 실행 전에 **`.env` 파일**에 필수 환경 변수를 정의해야 합니다.  
아래와 같이 프로젝트 루트에 `.env` 파일을 생성하세요.

```
touch .env
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

```
python pdf_to_md_pipeline.py -i ./pdfs -o ./data --vram-size 16
-i : PDF 파일들이 있는 디렉토리
-o : 출력 디렉토리
--vram-size : MinerU 가상 RAM 크기 (기본값: 16GB)
```

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
## 📦 환경 변수 (.env)
```.env``` 파일에는 다음과 같은 환경 변수를 포함해야 합니다
```
# OpenAI API 키
OPENAI_API_KEY=your-openai-api-key

# 선택적으로 사용할 수 있는 모델 이름 (gpt-4 or gpt-3.5-turbo)
LLM_MODEL=gpt-4

# 벡터 DB 저장 경로
VECTOR_DB_PATH=./vector_store/faiss_index

# 데이터 경로 설정
DATA_DIR=./data

# 기타 환경 설정
LOG_LEVEL=INFO
```
## 📈 예시 워크플로우
```
A[PDF 문서 업로드] --> B[PDF → Markdown 변환]
B --> C[Markdown 청킹 및 전처리]
C --> D[임베딩 및 벡터 저장]
D --> E[유사도 검색 + LLM 응답 생성]
E --> F[최종 응답 사용자에게 반환]
```

## 🧩 주요 기능 요약
| 기능 영역         | 설명 |
|------------------|------|
|    PDF 파싱       | 다양한 PDF 파서(Fitz, PDFPlumber, Unstructured 등)를 활용한 문서 레이아웃 분석 |
|    Markdown 변환  | MinerU 기반의 레이아웃 정제 및 Markdown 후처리 수행 |
|    청킹 및 전처리  | 헤더 기반 청킹, Null 블록 제거 등 Markdown 정제 및 구조화 |
|    벡터 인덱싱     | FAISS를 사용한 임베딩 기반 유사도 검색 수행 |
|    LLM 응답 생성   | 사용자 쿼리에 기반한 프롬프트 구성 및 OpenAI API 응답 생성 |
|    요약 및 강화    | 중요도 기반 필터링 및 요약 등 응답 품질 향상을 위한 후처리 기능 포함 |

## 📄 라이선스

본 프로젝트는 코드잇 하에 제공됩니다.
https://www.codeit.kr/
