#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

if [ ! -d "yolo_env" ]; then
  echo "未找到 yolo_env，请先运行：./install_orangepi.sh"
  exit 1
fi

source yolo_env/bin/activate
python app.py
