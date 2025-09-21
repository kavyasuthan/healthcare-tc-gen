# GenAI Testcase Generator — Complete (plug & play)

This repo contains:
- Streamlit frontend (frontend/)
- Flask backend (backend/)
- RAG data (rag/) and few-shot examples (backend/examples/)
- Vertex AI Gemini-based generator (mandatory)
- AI Review step done backend-side (no HITL in frontend)

## Quick start (local dev)

1. Clone repo and create virtualenv:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
