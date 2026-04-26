@echo off
REM Windows 启动脚本

echo ========================================
echo 智能文档问答系统 - 后端服务启动
echo ========================================

REM 检查 Python 版本
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未安装 Python
    pause
    exit /b 1
)

REM 创建虚拟环境 (如果不存在)
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo 安装依赖...
pip install -r requirements.txt

REM 复制环境变量文件
if not exist ".env" (
    echo 复制环境变量文件...
    copy .env.example .env
    echo 警告: 请编辑 .env 文件填入你的 API Key
)

REM 启动服务
echo 启动服务...
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause
