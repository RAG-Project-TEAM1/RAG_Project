# RAG_Project

## 프로젝트 개요
배경: 매일 수백 건의 기업 및 정부 제안요청서(RFP)가 게시되는데, 각 요청서 당 수십 페이지가 넘는 문건을 모두 검토하는 것은 불가능. 이러한 과정은 비효율적이며, 중요한 정보를 빠르게 파악하기 어려움.

목표: 사용자의 요청에 따라 RFP 문서의 내용을 효과적으로 추출하고 요약하여 필요한 정보를 제공할 수 있는 사내 RAG 시스템을 구현

기대 효과: RAG 시스템을 통해 중요한 정보를 신속하게 제공함으로써, 제안서 검토 시간을 단축하고 컨설팅 업무에 보다 집중할 수 있는 환경을 조성

## 🖥️ 실습 환경
	•	개발 환경: VS Code + Remote SSH (GCP VM 연결)
	•	운영체제: Ubuntu 20.04 LTS (GCP VM)
	•	Python 버전: 3.10+
	•	가상환경: venv (또는 Conda 가능)
	•	Git: GitHub 원격 저장소 연동
	•	LLM API: OpenAI API (GPT-4/3.5), 필요 시 Hugging Face Transformers
	•	GPU: NVIDIA L4 / CUDA 12.x (GCP AI 가속기 환경)
