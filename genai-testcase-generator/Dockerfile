# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system deps needed for pdf/docx handling and faiss build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential poppler-utils libxml2 libxslt1.1 libmagic1 curl \
 && rm -rf /var/lib/apt/lists/*

# Copy everything into container
COPY . .

# Upgrade pip and install dependencies
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Make start.sh executable
RUN chmod +x start.sh

# Cloud Run requires listening on $PORT (default: 8080)
EXPOSE 8080

# Set environment variables
ENV PORT=8080

# ✅ Important: run start.sh with bash
CMD ["bash", "start.sh"]