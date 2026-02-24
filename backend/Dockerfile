# Build context must be the roundtable/ root (one level above backend/).
# docker build -f backend/Dockerfile .
# This is handled automatically by docker-compose and build-and-push.sh.

FROM python:3.12-slim

WORKDIR /app

# Copy dependency manifest and install first (better layer caching)
COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir .

# Copy application code
COPY backend/ ./

# Copy protocol templates (referenced at runtime via ../protocol relative to this file's location)
# In the image: /app/routes/protocol.py resolves PROTOCOL_DIR as /protocol
COPY protocol/ /protocol/

ENV PROTOCOL_DIR=/protocol

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
