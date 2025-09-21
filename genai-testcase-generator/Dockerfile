# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system deps needed for pdf/docx handling and faiss build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential poppler-utils libxml2 libxslt1.1 libmagic1 \
 && rm -rf /var/lib/apt/lists/*

COPY . .

RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

RUN chmod +x start.sh

EXPOSE 8080

ENV PORT=8080
ENV BACKEND_PORT=5000
# NOTE: don't hardcode BACKEND_URL here so the app derives it from BACKEND_PORT/PORT at runtime.

CMD ["bash", "start.sh"]

