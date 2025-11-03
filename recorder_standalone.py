#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LifeTrace Recorder 独立启动脚本
用于打包成Windows可执行文件
"""

import os
import sys
from pathlib import Path

# 确保项目根目录在Python路径中
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """主入口函数"""
    try:
        # 导入recorder模块并运行
        from lifetrace_backend.recorder import main as recorder_main
        recorder_main()
    except KeyboardInterrupt:
        print("\n录制已停止")
        sys.exit(0)
    except Exception as e:
        print(f"启动录制器时发生错误: {e}")
        input("按回车键退出...")
        sys.exit(1)

if __name__ == '__main__':
    main()
