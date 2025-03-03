FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=manage.py \
    FLASK_CONFIG=production

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libmagic1 \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建上传目录
RUN mkdir -p app/static/uploads/image \
    && mkdir -p app/static/uploads/audio \
    && chmod -R 777 app/static/uploads

# 设置启动命令
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "manage:app"]
