import os
import json
import logging
import uuid
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from generator import GeneratorService
from utils import ensure_folder
from datetime import datetime
import threading

LOG = logging.getLogger("backend")
LOG.setLevel(logging.INFO)

app = Flask(__name__)
CORS(app)

# 🔹 Base folder to store uploads and generated files
BASE_UPLOADS = os.environ.get("TEMP_FOLDER", os.path.join(os.path.dirname(__file__), "..", "uploads"))
ensure_folder(BASE_UPLOADS)

# 🔹 Session storage
SESSIONS = {}

# 🔹 Testcase generator instance
GENERATOR = GeneratorService()


# =========================
# Flask Routes
# =========================

@app.route("/generate_testcases", methods=["POST"])
def generate_testcases():
    """Flask route: returns JSON for frontend requests."""
    try:
        payload = request.get_json(force=True)
        return jsonify(generate_testcases_handler(payload)), 200
    except Exception as e:
        LOG.exception("generate_testcases failed")
        return jsonify({"error": str(e)}), 500


@app.route("/download_reviewed/<session_id>/<filename>", methods=["GET"])
def download_reviewed(session_id, filename):
    """Serve reviewed Excel file via browser."""
    s = SESSIONS.get(session_id)
    if not s:
        return "Session not found", 404
    path = s.get("reviewed_path")
    if not path or os.path.basename(path) != filename:
        return "File not found", 404
    return send_file(path, as_attachment=True)


@app.route("/download_raw/<session_id>/<filename>", methods=["GET"])
def download_raw(session_id, filename):
    """Serve raw JSON file via browser."""
    s = SESSIONS.get(session_id)
    if not s:
        return "Session not found", 404
    path = s.get("raw_path")
    if not path or os.path.basename(path) != filename:
        return "File not found", 404
    return send_file(path, as_attachment=True)


@app.route("/status", methods=["GET"])
def status():
    """Simple health check."""
    return jsonify({"ok": True, "sessions": len(SESSIONS)})


# =========================
# Direct-call handler (for Streamlit)
# =========================

def generate_testcases_handler(payload: dict):
    """
    Direct-call version for Streamlit.
    Returns dict including preview_html and absolute file paths.
    """
    username = payload.get("username", "user")
    inputs = payload.get("inputs", {})
    typed = inputs.get("typed_requirements", [])
    uploaded_files = inputs.get("uploaded_files", [])
    alm_inputs = inputs.get("alm_inputs", {})
    alm_tool = (payload.get("alm_tool") or "jira").lower()

    LOG.info("Generating test cases for user=%s alm_tool=%s", username, alm_tool)

    # 🔹 Generate test cases using GeneratorService
    raw_cases, reviewed_cases, columns, prompt_used = GENERATOR.generate_full_pipeline(
        typed_requirements=typed,
        uploaded_files=uploaded_files,
        alm_inputs=alm_inputs,
        alm_tool=alm_tool
    )

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_user = "".join([c if c.isalnum() else "_" for c in username]) or "user"
    session_id = str(uuid.uuid4())
    out_dir = os.path.join(BASE_UPLOADS, f"{safe_user}_{ts}_{session_id}")
    ensure_folder(out_dir)

    # 🔹 File paths
    raw_path = os.path.join(out_dir, f"{safe_user}_raw_{alm_tool}_{ts}.json")
    reviewed_path = os.path.join(out_dir, f"{safe_user}_reviewed_{alm_tool}_{ts}.xlsx")

    # 🔹 Save files
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(raw_cases, f, indent=2, ensure_ascii=False)
    reviewed_cases.to_excel(reviewed_path, index=False)

    # 🔹 Store session info
    SESSIONS[session_id] = {
        "username": username,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "raw_path": raw_path,
        "reviewed_path": reviewed_path,
        "columns": columns,
        "prompt": prompt_used,
        "alm_tool": alm_tool
    }

    # 🔹 Prepare preview HTML (first 10 rows)
    preview_html = reviewed_cases.head(10).to_html(index=False, escape=False)

    # 🔹 Return dict including absolute file paths for Streamlit
    return {
        "message": "Test cases generated and AI-reviewed",
        "session_id": session_id,
        "count": len(reviewed_cases),
        "preview_html": preview_html,
        "columns": columns,
        "download_reviewed": f"/download_reviewed/{session_id}/{os.path.basename(reviewed_path)}",
        "download_raw": f"/download_raw/{session_id}/{os.path.basename(raw_path)}",
        "file_path_reviewed": reviewed_path,  # ✅ absolute path for Streamlit download
        "file_path_raw": raw_path
    }


# =========================
# Run backend in background (for Streamlit)
# =========================

def run_backend():
    port = int(os.environ.get("PORT", 8080))
    threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
    ).start()
