import faiss
import numpy as np
import openai

def embed_query(query, model="text-embedding-3-small"):
    resp = openai.embeddings.create(input=[query], model=model)
    return np.array(resp.data[0].embedding).astype("float32")

def search_index(index, query_embedding, k=5):
    D, I = index.search(query_embedding.reshape(1, -1), k)
    return D, I
