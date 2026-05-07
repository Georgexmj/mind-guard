FROM python:3.11-slim

WORKDIR /app

ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ARG PIP_EXTRA_INDEX_URL=
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=600 \
    PIP_NO_CACHE_DIR=1

# Switch apt mirrors and install system dependencies
RUN sed -i 's|http://deb.debian.org|http://mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's|http://deb.debian.org|http://mirrors.aliyun.com|g' /etc/apt/sources.list 2>/dev/null || true \
    && apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Use configurable mirror with higher timeout/retries to reduce network flakiness.
RUN if [ -n "$PIP_EXTRA_INDEX_URL" ]; then \
      pip install -r requirements.txt \
      --retries 30 \
      --timeout 600 \
      --prefer-binary \
      -i "$PIP_INDEX_URL" \
      --extra-index-url "$PIP_EXTRA_INDEX_URL"; \
    else \
      pip install -r requirements.txt \
      --retries 30 \
      --timeout 600 \
      --prefer-binary \
      -i "$PIP_INDEX_URL"; \
    fi

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
