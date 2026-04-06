FROM python:3.11-slim

WORKDIR /app

# 切换 apt 为阿里云镜像并安装系统依赖
RUN sed -i 's|http://deb.debian.org|http://mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's|http://deb.debian.org|http://mirrors.aliyun.com|g' /etc/apt/sources.list 2>/dev/null || true \
    && apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# 使用清华 PyPI 镜像加速安装
RUN pip install --no-cache-dir -r requirements.txt \
    -i https://pypi.org/simple \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
