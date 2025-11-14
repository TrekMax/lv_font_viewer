#!/usr/bin/env python3
"""
LVGL Font Viewer

LVGL 字体文件查看器主程序
"""
import sys
import os

# 禁用 Qt 字体数据库警告
os.environ['QT_LOGGING_RULES'] = 'qt.text.font.db=false'

from PyQt6.QtWidgets import QApplication
from src.ui import MainWindow


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName("LVGL Font Viewer")
    app.setOrganizationName("LVGL Tools")
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 如果有命令行参数，自动加载文件
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        window.load_font(file_path)
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
