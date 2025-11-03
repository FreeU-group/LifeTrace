#!/usr/bin/env python3
"""
初始化LifeTrace配置文件

如果配置文件不存在，则创建默认配置文件
配置文件保存在config目录下，而不是~目录
"""

import os
import sys
import shutil
import yaml
from pathlib import Path

# 设置项目路径
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path))

from lifetrace_backend.config import config

def init_config(force=False):
    """初始化配置文件

    Args:
        force: 是否强制初始化，如果为True，则会覆盖已存在的配置文件
    """
    # 获取默认配置文件路径
    default_config_path = os.path.join(project_path, 'config', 'default_config.yaml')

    # 创建配置文件目录
    config_dir = os.path.join(project_path, 'config')
    os.makedirs(config_dir, exist_ok=True)

    # 目标配置文件路径
    target_config_path = os.path.join(config_dir, 'config.yaml')

    # 检查默认配置文件是否存在
    if os.path.exists(default_config_path):
        # 如果目标配置文件已存在且不强制覆盖，则提示
        if os.path.exists(target_config_path) and not force:
            print(f"配置文件已存在: {target_config_path}")
            print("如果要重新初始化，请使用 --force 参数")
            return

        # 复制默认配置文件
        shutil.copy2(default_config_path, target_config_path)
        print(f"配置文件已创建: {target_config_path}")

        # 修改配置文件中的路径设置
        with open(target_config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        # 更新路径设置
        config_data['base_dir'] = 'data'
        config_data['database_path'] = 'data/lifetrace.db'
        config_data['screenshots_dir'] = 'screenshots'

        # 保存修改后的配置
        with open(target_config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, allow_unicode=True, sort_keys=False)
    else:
        print(f"默认配置文件不存在: {default_config_path}")
        print("将使用内置默认配置创建配置文件")

        # 使用配置对象的 save_config 方法创建配置文件
        config.config_path = target_config_path
        config.save_config()
        print(f"配置文件已创建: {target_config_path}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="初始化LifeTrace配置文件")
    parser.add_argument("--force", action="store_true", help="强制覆盖已存在的配置文件")
    args = parser.parse_args()

    init_config(force=args.force)
