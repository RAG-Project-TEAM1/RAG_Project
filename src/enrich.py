def enrich_metadata(meta: dict, data_df: pd.DataFrame) -> dict:
    fname = meta["filename"].strip()
    row = data_df[data_df["파일명"].str.strip() == fname]
    if not row.empty:
        row = row.iloc[0]
        for col in ["공고 번호", "사업명", "사업 금액", "발주 기관", "입찰 참여 마감일"]:
            meta[col] = row.get(col, "")
    return meta