FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libffi8 \
    libssl3 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install --no-cache-dir ".[dev]"

EXPOSE 8000

ENV HTTP_PROXY=""
ENV HTTPS_PROXY=""

ENTRYPOINT ["python", "-m", "youvedio"]
CMD ["mcp", "--transport", "sse"]
