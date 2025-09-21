# backend/vertex_ai_client.py
import os
import logging
import vertexai
from vertexai.generative_models import GenerativeModel
from vertexai.language_models import TextEmbeddingModel

LOG = logging.getLogger("vertex_ai_client")
LOG.setLevel(logging.INFO)

PROJECT_ID = os.environ.get("PROJECT_ID", None)
LOCATION = os.environ.get("LOCATION", "us-central1")

def init_vertex_with_credentials():
    """
    Initialize vertexai SDK. If GOOGLE_APPLICATION_CREDENTIALS is set or ADC available,
    vertexai.init will use them. PROJECT_ID can be provided via env.
    """
    try:
        if PROJECT_ID:
            vertexai.init(project=PROJECT_ID, location=LOCATION)
            LOG.info("Vertex AI initialized with project=%s location=%s", PROJECT_ID, LOCATION)
        else:
            vertexai.init(location=LOCATION)
            LOG.info("Vertex AI initialized with location=%s (project autodetect)", LOCATION)
    except Exception as e:
        LOG.exception("vertexai.init failed: %s", e)
        raise

def generate_with_gemini(prompt, model_name="gemini-2.5-flash"):
    try:
        model = GenerativeModel(model_name)
        response = model.generate_content(prompt)
        text = response.text
        return text
    except Exception as e:
        LOG.exception("Vertex AI generate failed: %s", e)
        raise RuntimeError(f"Vertex AI generation failed: {e}")

def get_embedding_model():
    try:
        return TextEmbeddingModel.from_pretrained("gemini-embedding-001")
    except Exception as e:
        LOG.exception("Failed to load embedding model: %s", e)
        raise
