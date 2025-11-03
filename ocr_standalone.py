#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LifeTrace OCR 独立启动脚本
用于打包成Windows可执行文件
"""

import os
import sys
from pathlib import Path

def _get_application_path() -> str:
    """获取应用程序路径，兼容PyInstaller打包"""
    if getattr(sys, 'frozen', False):
        # 如果是PyInstaller打包的应用，使用可执行文件所在目录
        return os.path.dirname(sys.executable)
    else:
        # 开发环境，使用项目根目录
        return str(Path(__file__).parent)

# 确保项目根目录在Python路径中
project_root = _get_application_path()
sys.path.insert(0, project_root)

def main():
    """主入口函数"""
    try:
        # 导入simple_ocr模块并运行
        from lifetrace_backend.simple_ocr import main as ocr_main
        ocr_main()
    except KeyboardInterrupt:
        print("\nOCR服务已停止")
        sys.exit(0)
    except Exception as e:
        print(f"启动OCR服务时发生错误: {e}")
        input("按回车键退出...")
        sys.exit(1)

if __name__ == '__main__':
    main()
