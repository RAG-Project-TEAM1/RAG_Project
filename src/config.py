import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHUNKS_DIR = "../output_jsonl_chunks"
VECTOR_INDEX = "../vector.index"
VECTOR_METADATA = "../vector_metadata.json"
DATA_LIST = "../data_list.csv"
