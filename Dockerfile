# ================================
# 构建阶段 - 用于编译和安装依赖
# ================================
FROM python:3.13-slim as builder

# 设置工作目录
WORKDIR /app

# 安装构建时需要的系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖到用户目录（避免全局安装）
RUN pip install --no-cache-dir --user -r requirements.txt

# ================================
# 运行阶段 - 最终的精简镜像
# ================================
FROM python:3.13-slim

# 创建非root用户提高安全性
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 只安装运行时必需的库
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && apt-get autoremove -y

# 从构建阶段复制已安装的Python包
COPY --from=builder /root/.local /home/appuser/.local

# 设置工作目录
WORKDIR /app

# 复制应用代码
COPY *.py .

# 更改文件所有权
RUN chown -R appuser:appuser /app

# 切换到非root用户
USER appuser

# 确保Python能找到用户安装的包
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/home/appuser/.local/lib/python3.13/site-packages:$PYTHONPATH

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["python", "-m", "robyn", "app.py", "--fast", "--log-level", "INFO"]