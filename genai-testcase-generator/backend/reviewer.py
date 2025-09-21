# backend/reviewer.py
import json
import logging
from vertex_ai_client import generate_with_gemini

LOG = logging.getLogger("reviewer")
LOG.setLevel(logging.INFO)

def build_review_prompt(test_cases_list, columns, rag_text="", few_shot_text=""):
    cases_json = json.dumps(test_cases_list, indent=2, ensure_ascii=False)
    cols = ", ".join([f'"{c}"' for c in columns])
    prompt = f"""
You are an expert QA reviewer for healthcare systems. You will receive a JSON array of test cases.
Each test case has keys: {cols}.

Tasks (perform all):
1. Remove exact duplicates.
2. Identify missing negative or security scenarios and add up to 3 suggested test cases (if applicable).
3. Ensure fields are non-empty where possible (fill brief suggestions if empty).
4. Check alignment to compliance items in the following context (if provided): {rag_text[:1000]}
5. Produce a cleaned JSON array of objects using the same keys. For any added test case, generate a TestCaseID (prefix REV-XXXX).

Input test cases:
{cases_json}

Few-shot examples for format:
{few_shot_text}

Return only valid JSON array (no commentary).
"""
    return prompt

def ai_review_testcases(test_cases_list, columns, rag_text="", few_shot_text=""):
    prompt = build_review_prompt(test_cases_list, columns, rag_text, few_shot_text)
    LOG.info("Sending review prompt to Vertex AI (length=%d)", len(prompt))
    try:
        raw = generate_with_gemini(prompt)
        text = raw.strip()
        if text.startswith("```"):
            parts = text.split("```")
            if len(parts) >= 3:
                text = parts[2].strip()
            else:
                text = parts[1].strip()
        # extract JSON array
        import re
        m = re.search(r'(\[.*\])', text, flags=re.DOTALL)
        js = m.group(1) if m else text
        result = json.loads(js)
        if not isinstance(result, list):
            raise RuntimeError("Reviewer returned non-list")
        return result
    except Exception as e:
        LOG.exception("AI reviewer failed, returning original cases")
        # fallback: ensure minimal normalization
        return test_cases_list
