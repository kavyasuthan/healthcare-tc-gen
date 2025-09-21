# frontend/input_handler.py
import io
import docx
import PyPDF2

class InputHandler:
    def __init__(self):
        pass

    def extract_from_text(self, typed_requirements):
        return {"typed_requirements": typed_requirements}

    def extract_from_files(self, uploaded_files):
        file_results = []
        for file in uploaded_files:
            try:
                name = file.name
                if name.lower().endswith(".txt"):
                    content = file.getvalue().decode("utf-8", errors="ignore")
                elif name.lower().endswith(".docx"):
                    bio = io.BytesIO(file.getvalue())
                    doc = docx.Document(bio)
                    content = "\n".join([p.text for p in doc.paragraphs])
                elif name.lower().endswith(".pdf"):
                    bio = io.BytesIO(file.getvalue())
                    reader = PyPDF2.PdfReader(bio)
                    pages = []
                    for page in reader.pages:
                        try:
                            t = page.extract_text()
                            if t:
                                pages.append(t)
                        except Exception:
                            continue
                    content = "\n".join(pages)
                else:
                    content = ""
            except Exception as e:
                content = f"[Error reading file: {e}]"
            file_results.append({"file_name": name, "content": content})
        return {"uploaded_files": file_results}

    def extract_from_alm(self, alm_inputs):
        return {"alm_inputs": alm_inputs}

    def build_request_json(self, typed_requirements, uploaded_files, alm_inputs):
        request_json = {}
        if typed_requirements:
            request_json.update(self.extract_from_text(typed_requirements))
        if uploaded_files:
            request_json.update(self.extract_from_files(uploaded_files))
        if alm_inputs:
            request_json.update(self.extract_from_alm(alm_inputs))
        return request_json
