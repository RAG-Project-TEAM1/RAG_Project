from src.config import *
from src.utils import sanitize_filename
from src.loader import load_vector_metadata, load_data_list
from src.vector_search import embed_query, search_index
from src.answer_generation import generate_answer

# 1. 데이터 로드
vector_metadata = load_vector_metadata(VECTOR_METADATA)
data_list = load_data_list(DATA_LIST)

# 2. 사용자 입력/검색
query = input("질문: ")
q_emb = embed_query(query)
# ...이후 chunks/context 생성

# 3. 답변 생성
answer = generate_answer(query, context="(검색된 문서 내용)")
print(answer)