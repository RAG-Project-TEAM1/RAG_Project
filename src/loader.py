import json
import pandas as pd

def load_vector_metadata(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_data_list(csv_path):
    return pd.read_csv(csv_path)