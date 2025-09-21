# backend/generator.py
import os
import json
import pandas as pd
import logging
from vertex_ai_client import generate_with_gemini, get_embedding_model, init_vertex_with_credentials
from rag_loader import get_relevant_docs_local, ensure_rag_files_local
from utils import ensure_folder
from reviewer import ai_review_testcases

LOG = logging.getLogger("generator")
LOG.setLevel(logging.INFO)

BASE_DIR = os.path.dirname(__file__)
EXAMPLES_DIR = os.path.join(BASE_DIR, "examples")
ensure_folder(EXAMPLES_DIR)

def create_sample_few_shots():
    examples = {
        "jira_testcase_eg.xlsx": pd.DataFrame([{"TestCaseID":"TC-JIRA-001","Description":"View appointment slots","Requirement":"Patients can view slots","ExpectedResult":"Slots list shown","Priority":"High","Notes":"Jira example"}]),
        "azure_testcase_eg.xlsx": pd.DataFrame([{"TestCaseID":"TC-AZ-001","Description":"Email reminder","Requirement":"Send reminder 24h","ExpectedResult":"Reminder sent","Priority":"Medium","Notes":"Azure example"}]),
        "polarion_testcase_eg.xlsx": pd.DataFrame([{"TestCaseID":"TC-POL-001","Description":"Cancel appointment","Requirement":"Doctor can cancel","ExpectedResult":"Appointment removed","Priority":"Medium","Notes":"Polarion example"}]),
        "etl_testcase_eg.xlsx": pd.DataFrame([{"TestCaseID":"TC-ETL-001","Description":"ETL load completes","Requirement":"ETL must load daily","ExpectedResult":"Data loaded","Priority":"Medium","Notes":"ETL example"}])
    }
    for fname, df in examples.items():
        path = os.path.join(EXAMPLES_DIR, fname)
        if not os.path.exists(path):
            df.to_excel(path, index=False)
            LOG.info("Created sample few-shot example: %s", path)

create_sample_few_shots()
ensure_rag_files_local()

class GeneratorService:
    def __init__(self):
        self.columns = ["TestCaseID", "Description", "Requirement", "ExpectedResult", "Priority", "Notes"]
        try:
            init_vertex_with_credentials()
        except Exception as e:
            LOG.warning("Vertex AI init warning: %s", e)

    def load_few_shot(self, alm_tool):
        mapping = {"jira": "jira_testcase_eg.xlsx","azure": "azure_testcase_eg.xlsx","polarion": "polarion_testcase_eg.xlsx","etl": "etl_testcase_eg.xlsx"}
        fname = mapping.get(alm_tool, mapping["jira"])
        path = os.path.join(EXAMPLES_DIR, fname)
        try:
            return pd.read_excel(path)
        except Exception as e:
            LOG.warning("Failed to load few-shot: %s", e)
            return None

    def build_prompt(self, prompt_text, alm_format_columns, few_shot_text, relevant_docs_text):
        column_list_str = ", ".join([f'"{c}"' for c in alm_format_columns])
        return f"""
You are an expert QA engineer specializing in healthcare software.
Based on the following user request, generate 10-15 unique test cases.
Include Positive, Negative, Security, Performance, and Usability scenarios.

Relevant docs:
{relevant_docs_text}

Few-shot examples:
{few_shot_text}

User Request: '{prompt_text}'

Return strictly valid JSON array where each object has keys: {column_list_str}.
Do not include explanations or markdown.
"""

    def generate_with_gemini_safe(self, prompt_text, alm_format_columns, relevant_docs_text, few_shot_text, max_retries=2):
        meta_prompt = self.build_prompt(prompt_text, alm_format_columns, few_shot_text, relevant_docs_text)
        for attempt in range(max_retries):
            raw = generate_with_gemini(meta_prompt)
            if raw and raw.strip():
                return raw
            LOG.warning("Empty response from Gemini, retrying (%d/%d)...", attempt+1, max_retries)
        raise RuntimeError("Vertex AI Gemini returned empty output after retries.")

    def parse_generator_output_safe(self, raw_text):
        text = raw_text.strip()
        # remove code fences
        if text.startswith("```"):
            text = "".join(text.split("```")[1:]).strip()
        # try to extract JSON array
        import re
        m = re.search(r'(\[.*\])', text, flags=re.DOTALL)
        js = m.group(1) if m else text
        try:
            parsed = json.loads(js)
            if not isinstance(parsed, list):
                raise ValueError("Parsed JSON is not a list")
            return parsed, text
        except Exception:
            LOG.error("Raw output could not be parsed as JSON:\n%s", text)
            raise RuntimeError(f"Failed to parse JSON from generator output. Check logs for raw output.")

    def generate_full_pipeline(self, typed_requirements=None, uploaded_files=None, alm_inputs=None, alm_tool="jira", external_prompt=None):
        typed_requirements = typed_requirements or []
        uploaded_files = uploaded_files or []
        alm_inputs = alm_inputs or {}

        prompt_for_rag = " ".join(typed_requirements) or external_prompt or "healthcare requirements"
        try:
            docs = get_relevant_docs_local(prompt_for_rag, k=3)
            relevant_docs_text = "\n\n".join(docs)
        except Exception as e:
            LOG.warning("RAG retrieval failed: %s", e)
            relevant_docs_text = ""

        df_few = self.load_few_shot(alm_tool)
        few_shot_text = df_few.to_string(index=False) if df_few is not None else ""
        alm_format_columns = df_few.columns.tolist() if df_few is not None else self.columns

        user_prompt = external_prompt or "\n".join([
            "Typed Requirements:\n" + "\n".join(typed_requirements) if typed_requirements else "",
            "Uploaded Files Content:\n" + "\n".join([f"{f.get('file_name','file')}\n{f.get('content','')}" for f in uploaded_files]) if uploaded_files else "",
            "ALM Inputs:\n" + json.dumps(alm_inputs) if alm_inputs else ""
        ]).strip() or prompt_for_rag

        raw_text = self.generate_with_gemini_safe(user_prompt, alm_format_columns, relevant_docs_text, few_shot_text)
        parsed_cases, used_text = self.parse_generator_output_safe(raw_text)

        # normalize
        normalized = [{c: obj.get(c,"") if isinstance(obj, dict) else "" for c in alm_format_columns} for obj in parsed_cases]
        reviewed_list = ai_review_testcases(normalized, alm_format_columns, relevant_docs_text, few_shot_text)
        df_reviewed = pd.DataFrame(reviewed_list, columns=alm_format_columns)

        return normalized, df_reviewed, alm_format_columns, used_text
