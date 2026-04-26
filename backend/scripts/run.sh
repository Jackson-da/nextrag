#!/bin/bash
# 启动脚本 for Linux/macOS

set -e

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "错误: 需要 Python 3.10 或更高版本"
    echo "当前版本: $python_version"
    exit 1
fi

# 创建虚拟环境 (如果不存在)
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "安装依赖..."
pip install -r requirements.txt

# 复制环境变量文件
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "警告: 请编辑 .env 文件填入你的 API Key"
fi

# 启动服务
echo "启动服务..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
