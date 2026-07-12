# CAUala web app — runs anywhere that runs a container.
# Local:      docker build -t cauala . && docker run -p 8000:7860 cauala
# HF Spaces:  uses this file automatically (Docker Space), serves on 7860.
# Render/Railway/Cloud Run/Fly: they inject $PORT and it is honoured below.
FROM python:3.11-slim

WORKDIR /app

# Install dependencies first for better layer caching.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the repo. We run from /app (not `pip install .`) so the
# registry/ and scoring/ YAML files resolve via their repo-relative paths.
COPY . .

# Hugging Face Spaces expects 7860; other hosts override $PORT.
ENV PORT=7860 HOST=0.0.0.0
EXPOSE 7860

CMD ["sh", "-c", "uvicorn src.webapp:app --host 0.0.0.0 --port ${PORT:-7860}"]
