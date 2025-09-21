# frontend/components.py
import streamlit as st
import os
from datetime import datetime
import re

def is_valid_username(name):
    return bool(re.match(r'^\w+$', name))

def create_session_folder(username):
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    folder = os.path.join("uploads", f"{username}_session_{session_id}")
    os.makedirs(folder, exist_ok=True)
    return folder

def tabs_ui():
    tab1, tab2, tab3 = st.tabs(["📝 Typed Requirements", "📂 Upload Files", "🎫 ALM Inputs"])

    with tab1:
        typed_text = st.text_area("Enter requirement(s) here", key="typed_input")
        if typed_text.strip() and typed_text.strip() not in st.session_state.typed_requirements:
            st.session_state.typed_requirements.append(typed_text.strip())
        if st.session_state.typed_requirements:
            st.text_area("Requirements Added", value="\n".join(st.session_state.typed_requirements), height=150, disabled=True)

    with tab2:
        uploaded_files = st.file_uploader("Upload requirement document(s)", type=["pdf", "docx", "txt"], accept_multiple_files=True)
        if uploaded_files:
            batch_folder = os.path.join(st.session_state.session_folder, f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            os.makedirs(batch_folder, exist_ok=True)
            st.session_state.uploaded_files = []
            for file in uploaded_files:
                file_path = os.path.join(batch_folder, file.name)
                with open(file_path, "wb") as f:
                    f.write(file.getbuffer())
                st.session_state.uploaded_files.append(file)
            st.success(f"✅ {len(uploaded_files)} file(s) uploaded and stored.")

    with tab3:
        selected_alms = st.multiselect("Select ALM(s) to fetch requirements from", ["Jira", "Polarion", "Azure DevOps"])
        for alm in selected_alms:
            st.markdown(f"#### {alm} Input")
            if alm == "Jira":
                jira_url = st.text_input("Enter Jira ticket URL", key="jira_input")
                if jira_url.strip() and jira_url.strip() not in st.session_state.alm_inputs["Jira"]["tickets"]:
                    st.session_state.alm_inputs["Jira"]["tickets"].append(jira_url.strip())
            elif alm == "Polarion":
                polarion_id = st.text_input("Enter Polarion Work Item URL or ID", key="polarion_input")
                if polarion_id.strip() and polarion_id.strip() not in st.session_state.alm_inputs["Polarion"]["items"]:
                    st.session_state.alm_inputs["Polarion"]["items"].append(polarion_id.strip())
            elif alm == "Azure DevOps":
                ado_id = st.text_input("Enter Azure DevOps Work Item ID", key="ado_input")
                if ado_id.strip() and ado_id.strip() not in st.session_state.alm_inputs["Azure DevOps"]["items"]:
                    st.session_state.alm_inputs["Azure DevOps"]["items"].append(ado_id.strip())

        for alm, data in st.session_state.alm_inputs.items():
            if data.get("tickets") or data.get("items"):
                st.markdown(f"**{alm} Requirements Added**")
                combined = data.get("tickets", []) + data.get("items", [])
                st.text_area(f"{alm} Inputs", value="\n".join(combined), height=100, disabled=True)
