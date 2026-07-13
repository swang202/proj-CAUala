# CAUala web app — runs anywhere that runs a container.
# Local:  docker build -t cauala . && docker run -p 8000:8000 cauala
# Render / Railway / Cloud Run / Fly inject $PORT, which is honoured below.
FROM python:3.11-slim

WORKDIR /app

# Install dependencies first for better layer caching.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the repo. We run from /app (not `pip install .`) so the
# registry/ and scoring/ YAML files resolve via their repo-relative paths.
COPY . .

ENV PORT=8000 HOST=0.0.0.0
EXPOSE 8000

CMD ["sh", "-c", "uvicorn src.webapp:app --host 0.0.0.0 --port ${PORT:-8000}"]
