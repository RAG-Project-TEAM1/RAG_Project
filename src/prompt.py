def generate_answer(query, chunks):
    context = ""
    for c in chunks:
        m = c["metadata"]
        context += f"""
📄 [문서 정보]
제목: {m.get('title', '')}
소제목: {m.get('subtitle', '')}
공고번호: {m.get('공고 번호', '')}
발주기관: {m.get('발주 기관', '')}
사업명: {m.get('사업명', '')}
예산: {m.get('사업 금액', '')}
마감일: {m.get('입찰 참여 마감일', '')}

📑 [본문]
{c['text']}

""".strip() + "\n\n"

    prompt = f"""다음은 사용자의 질문과 관련된 문서 내용입니다.

[질문]
{query}

[문서]
{context}

위 문서들을 참고하여 질문에 대해 명확하고 간결하게 답변하세요."""

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    return response.choices[0].message.content.strip()
﻿
