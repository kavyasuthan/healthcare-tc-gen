# backend/rag_loader.py
import os
import json
import pandas as pd
from pathlib import Path
from vertex_ai_client import get_embedding_model
import numpy as np
import faiss
import logging

LOG = logging.getLogger("rag_loader")
LOG.setLevel(logging.INFO)

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAG_DIR = os.path.join(BASE, "rag")
Path(RAG_DIR).mkdir(parents=True, exist_ok=True)

def ensure_rag_files_local():
    txt_path = os.path.join(RAG_DIR, "healthcare_compliance.txt")
    json_path = os.path.join(RAG_DIR, "req_example.json")
    xlsx_path = os.path.join(RAG_DIR, "traceability_matrix_eg.xlsx")

    if not os.path.exists(txt_path):
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("Healthcare compliance notes: PHI must be protected. Role-based access, audit trails, encryption at rest and in transit. Data retention guidelines.\n")

    if not os.path.exists(json_path):
        sample = [
            {"requirement": "Authenticate users", "testcases": ["Valid login", "Invalid login"]},
            {"requirement": "Encrypt PHI", "testcases": ["Encrypt in transit", "Encrypt at rest"]}
        ]
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(sample, f, indent=2)

    if not os.path.exists(xlsx_path):
        df = pd.DataFrame([{"ReqID":"R1","Requirement":"Authenticate users","Trace":"TC001"}])
        df.to_excel(xlsx_path, index=False)

def load_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def load_json(path):
    import json
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_xlsx(path):
    return pd.read_excel(path).to_string(index=False)

def get_relevant_docs_local(query, k=1):
    # load files
    txt = load_text(os.path.join(RAG_DIR, "healthcare_compliance.txt"))
    j = load_json(os.path.join(RAG_DIR, "req_example.json"))
    json_text = " ".join([r.get("requirement","") + " " + " ".join(r.get("testcases",[])) for r in j])
    xls = load_xlsx(os.path.join(RAG_DIR, "traceability_matrix_eg.xlsx"))
    all_texts = [json_text, xls, txt]

    # embeddings via vertex embedding model
    model = get_embedding_model()
    embeds = model.get_embeddings(all_texts)
    vecs = np.array([e.values for e in embeds]).astype("float32")
    dim = vecs.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(vecs)
    qemb = model.get_embeddings([query])[0].values
    qvec = np.array([qemb]).astype("float32")
    distances, indices = index.search(qvec, k)
    results = [all_texts[i] for i in indices[0] if 0 <= i < len(all_texts)]
    return results
