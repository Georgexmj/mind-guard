FROM python:3.11-slim

WORKDIR /app

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

# Use official PyPI to avoid mirror hash mismatch issues
RUN pip install --no-cache-dir -r requirements.txt \
    --retries 12 \
    --timeout 300

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
