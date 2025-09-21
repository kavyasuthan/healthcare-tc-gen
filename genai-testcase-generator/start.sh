#!/bin/bash
set -e

BACKEND_PORT=${BACKEND_PORT:-5000}
STREAMLIT_PORT=${PORT:-8080}

echo "Starting backend (gunicorn) on port ${BACKEND_PORT}..."
gunicorn -w 2 -b 0.0.0.0:${BACKEND_PORT} backend.backend_api:app &

sleep 2

echo "Starting Streamlit on port ${STREAMLIT_PORT}..."
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_SERVER_PORT=${STREAMLIT_PORT}
export STREAMLIT_SERVER_ENABLE_CORS=false
export BACKEND_URL=${BACKEND_URL:-http://localhost:${BACKEND_PORT}}
streamlit run frontend/main_ui.py --server.port ${STREAMLIT_PORT} --server.address 0.0.0.0
