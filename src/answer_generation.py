import openai

def generate_answer(query, context, model="gpt-4o"):
    prompt = f"""[질문]\n{query}\n\n[문서]\n{context}\n\n위 문서 내용을 바탕으로 질문에 답하세요."""
    resp = openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    return resp.choices[0].message.content.strip()
    
