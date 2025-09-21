# backend/backend_api.py
import os
import json
import logging
import uuid
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS   # <-- add this
from generator import GeneratorService
from utils import ensure_folder
from datetime import datetime
import threading

LOG = logging.getLogger("backend")
LOG.setLevel(logging.INFO)

app = Flask(__name__)

CORS(app)  # <-- allow all origins for now

BASE_UPLOADS = os.environ.get("TEMP_FOLDER", os.path.join(os.path.dirname(__file__), "..", "uploads"))
ensure_folder(BASE_UPLOADS)




# In-memory sessions store
SESSIONS = {}
GENERATOR = GeneratorService()

@app.route("/generate_testcases", methods=["POST"])
def generate_testcases():
    try:
        payload = request.get_json(force=True)
        if not payload:
            return jsonify({"error": "No JSON payload"}), 400

        username = payload.get("username", "user")
        inputs = payload.get("inputs", {})
        typed = inputs.get("typed_requirements", [])
        uploaded_files = inputs.get("uploaded_files", [])
        alm_inputs = inputs.get("alm_inputs", {})
        alm_tool = (payload.get("alm_tool") or "jira").lower()

        LOG.info("Generating test cases for user=%s alm_tool=%s", username, alm_tool)

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

        raw_path = os.path.join(out_dir, f"{safe_user}_raw_{alm_tool}_{ts}.json")
        reviewed_path = os.path.join(out_dir, f"{safe_user}_reviewed_{alm_tool}_{ts}.xlsx")

        with open(raw_path, "w", encoding="utf-8") as f:
            json.dump(raw_cases, f, indent=2, ensure_ascii=False)

        reviewed_cases.to_excel(reviewed_path, index=False)

        SESSIONS[session_id] = {
            "username": username,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "raw_path": raw_path,
            "reviewed_path": reviewed_path,
            "columns": columns,
            "prompt": prompt_used,
            "alm_tool": alm_tool
        }

        preview_html = reviewed_cases.head(10).to_html(index=False, escape=False)

        resp = {
            "message": "Test cases generated and AI-reviewed",
            "session_id": session_id,
            "count": len(reviewed_cases),
            "preview_html": preview_html,
            "columns": columns,
            "download_reviewed": f"/download_reviewed/{session_id}/{os.path.basename(reviewed_path)}",
            "download_raw": f"/download_raw/{session_id}/{os.path.basename(raw_path)}"
        }
        return jsonify(resp), 200

    except Exception as e:
        LOG.exception("generate_testcases failed")
        return jsonify({"error": str(e)}), 500

@app.route("/download_reviewed/<session_id>/<filename>", methods=["GET"])
def download_reviewed(session_id, filename):
    s = SESSIONS.get(session_id)
    if not s:
        return "Session not found", 404
    path = s.get("reviewed_path")
    if not path or os.path.basename(path) != filename:
        return "File not found", 404
    return send_file(path, as_attachment=True)

@app.route("/download_raw/<session_id>/<filename>", methods=["GET"])
def download_raw(session_id, filename):
    s = SESSIONS.get(session_id)
    if not s:
        return "Session not found", 404
    path = s.get("raw_path")
    if not path or os.path.basename(path) != filename:
        return "File not found", 404
    return send_file(path, as_attachment=True)

@app.route("/status", methods=["GET"])
def status():
    return jsonify({"ok": True, "sessions": len(SESSIONS)})

def run_backend():
    port = int(os.environ.get("PORT", 8080))  # same as Streamlit
    threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
    ).start()
