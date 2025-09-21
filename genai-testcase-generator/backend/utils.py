# backend/utils.py
import os
from pathlib import Path

def ensure_folder(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def read_local_file_safe(path):
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()
