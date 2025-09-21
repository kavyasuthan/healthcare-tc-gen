#!/bin/bash
set -e

STREAMLIT_PORT=${PORT:-8080}

echo "Starting Streamlit (which will also launch Flask backend) on port ${STREAMLIT_PORT}..."
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_SERVER_PORT=${STREAMLIT_PORT}
export STREAMLIT_SERVER_ENABLE_CORS=false
# Backend will run on same PORT internally
export BACKEND_URL=http://127.0.0.1:${STREAMLIT_PORT}

streamlit run backend/main_ui.py --server.port ${STREAMLIT_PORT} --server.address 0.0.0.0
