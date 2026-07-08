#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "[1/4] 安装系统依赖..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv libgl1 libglib2.0-0 v4l-utils unzip

echo "[2/4] 创建 Python 虚拟环境..."
python3 -m venv yolo_env
source yolo_env/bin/activate

echo "[3/4] 安装 Python 依赖..."
pip install --upgrade pip
pip install -r requirements.txt

echo "[4/4] 完成。"
echo "下一步：把训练好的 best.pt 放到 weights/best.pt，然后运行 ./run.sh"
