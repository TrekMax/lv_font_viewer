#!/bin/bash
# LVGL Font Viewer 启动脚本

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3"
    exit 1
fi

# 检查依赖
echo "检查依赖..."
python3 -c "import PyQt6" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "未安装 PyQt6，正在安装依赖..."
    pip3 install -r requirements.txt
fi

# 启动程序
echo "启动 LVGL Font Viewer..."
python3 lv_font_viewer.py "$@"
