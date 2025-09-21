# frontend/main_ui.py
import streamlit as st
import shutil
from components import create_session_folder, tabs_ui
from input_handler import InputHandler
import requests
import os
from urllib.parse import urljoin

st.set_page_config(page_title="Healthcare Testcase Generator", page_icon="🧪", layout="centered")

st.markdown("""
<div style="text-align:center; font-size:36px; font-weight:bold; line-height:1.2;">
🧪 Healthcare Testcase Generator
</div>
<div style="text-align:center; font-size:18px; color:gray; margin-top:15px; margin-bottom:20px;">
AI-powered system to convert healthcare requirements into compliant, traceable test cases
</div>
""", unsafe_allow_html=True)

st.markdown("<hr style='margin:15px 0 20px 0;'>", unsafe_allow_html=True)

st.session_state.setdefault('username', "")
st.session_state.setdefault('username_set', False)
st.session_state.setdefault('session_folder', None)
st.session_state.setdefault('typed_requirements', [])
st.session_state.setdefault('uploaded_files', [])
st.session_state.setdefault('alm_inputs', {
    "Jira": {"tickets": []},
    "Polarion": {"items": []},
    "Azure DevOps": {"items": []}
})
st.session_state.setdefault('last_session_id', None)
st.session_state.setdefault('last_preview_html', None)
st.session_state.setdefault('last_columns', None)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000")

if not st.session_state.username_set:
    username_input = st.text_input("Enter your username")
    if username_input:
        st.session_state.username = username_input.strip()
        st.session_state.username_set = True
        st.session_state.session_folder = create_session_folder(username_input.strip())
        st.rerun()
    st.stop()

st.success(f"Welcome, **{st.session_state.username}**!")
st.text_input("Username", value=st.session_state.username, disabled=True)
tabs_ui()

col1, col2 = st.columns([1,1])
with col1:
    if st.button("🚀 Send All Inputs"):
        handler = InputHandler()
        request_json = handler.build_request_json(
            st.session_state.typed_requirements,
            st.session_state.uploaded_files,
            st.session_state.alm_inputs
        )
        payload = {"username": st.session_state.username, "inputs": request_json}
        try:
            resp = requests.post(f"{BACKEND_URL}/generate_testcases", json=payload, timeout=300)
            if resp.status_code == 200:
                data = resp.json()
                st.success("✅ Test cases generated and AI-reviewed.")
                sid = data.get("session_id")
                st.session_state.last_session_id = sid
                st.session_state.last_preview_html = data.get("preview_html")
                st.session_state.last_columns = data.get("columns")
                if st.session_state.last_preview_html:
                    st.subheader("Preview (first 10 rows)")
                    st.markdown(st.session_state.last_preview_html, unsafe_allow_html=True)
                dl = data.get("download_reviewed")
                if dl:
                    link = urljoin(BACKEND_URL, dl.lstrip("/"))
                    st.markdown(f"**Download Excel:** [Click Here]({link})")
            else:
                st.error(f"Error: {resp.status_code} - {resp.text}")
        except Exception as e:
            st.error(f"Backend call failed: {e}")

with col2:
    if st.button("🗑️ End Session"):
        if st.session_state.session_folder:
            shutil.rmtree(st.session_state.session_folder, ignore_errors=True)
        keys = ['session_folder','username','typed_requirements','uploaded_files','alm_inputs','username_set','last_session_id','last_preview_html','last_columns']
        for k in keys:
            if k in st.session_state:
                del st.session_state[k]
        st.success("✅ Session ended. Refresh the page to start a new session.")
        st.rerun()

st.markdown("---")
st.header("Admin Review (internal) — not exposed to end user")
st.info("AI review is performed in backend automatically. Admin portal coming later.")
