# syntax=docker/dockerfile:1
FROM node:20-alpine AS febuild
WORKDIR /fe
COPY demo_yelp/frontend/package.json demo_yelp/frontend/package-lock.json* ./
RUN npm install
COPY demo_yelp/frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
# Preinstall path dep; pyproject still lists file:../zeus_client_python which
# does not exist in the image layout — install app with --no-deps (see demo_travel_sample).
COPY zeus_client_python /tmp/zeus_client_python
COPY demo_yelp/pyproject.toml ./
COPY demo_yelp/src ./src
COPY demo_yelp/data ./data
COPY demo_yelp/config.example.json ./
RUN pip install --no-cache-dir /tmp/zeus_client_python \
    && pip install --no-cache-dir \
        "fastapi==0.115.6" \
        "uvicorn[standard]==0.34.0" \
        "httpx==0.28.1" \
        "python-multipart==0.0.20" \
    && pip install --no-cache-dir --no-deps -e .
COPY --from=febuild /fe/dist /app/frontend/dist
ENV PORT=5000
ENV ZEUS_CLIENT_CONFIG_DIR=/app
ENV ZEUS_CHAT_REQUESTS_DIR=/app/data/chat_requests
ENV CHAT_LOG_PATH=/app/data/chats.jsonl
EXPOSE 5000
CMD ["python", "-m", "local_guide"]
