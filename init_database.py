#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动重置LifeTrace数据库
直接操作，不依赖lifetrace命令
"""

import os
import sys
import shutil
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from lifetrace_backend.config import config


def manual_reset():
    """手动重置所有数据库"""
    print("🔄 手动重置LifeTrace数据库")
    print("=" * 40)

    # 1. 显示当前配置
    print(f"配置信息:")
    print(f"  基础目录: {config.base_dir}")
    print(f"  数据库路径: {config.database_path}")
    print(f"  截图目录: {config.screenshots_dir}")
    print(f"  向量数据库目录: {config.vector_db_persist_directory}")

    # 2. 删除SQLite数据库
    print(f"\n1. 删除SQLite数据库...")
    db_path = config.database_path
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"✅ 已删除 {db_path}")
    else:
        print(f"ℹ️  数据库文件不存在: {db_path}")

    # 3. 清理向量数据库目录
    print(f"\n2. 清理向量数据库...")
    vector_db_path = Path(config.vector_db_persist_directory)
    if vector_db_path.exists():
        try:
            shutil.rmtree(vector_db_path)
            print(f"✅ 已删除向量数据库目录: {vector_db_path}")
        except Exception as e:
            print(f"❌ 删除向量数据库目录失败: {e}")
    else:
        print(f"ℹ️  向量数据库目录不存在: {vector_db_path}")

    # 4. 清理截图目录（可选）
    print(f"\n3. 清理截图目录...")
    screenshots_dir = Path(config.screenshots_dir)
    if screenshots_dir.exists():
        files = list(screenshots_dir.glob("*"))
        if files:
            confirm = input(f"发现 {len(files)} 个文件，是否删除? (y/N): ").strip().lower()
            if confirm == 'y':
                for file_path in files:
                    if file_path.is_file():
                        file_path.unlink()
                print(f"✅ 已清理截图目录")
            else:
                print("ℹ️  跳过截图目录清理")
        else:
            print("ℹ️  截图目录为空")
    else:
        print(f"ℹ️  截图目录不存在: {screenshots_dir}")

    # 5. 重新创建目录结构
    print(f"\n4. 重新创建目录结构...")
    # 确保只创建~/目录下的结构，不在项目根目录创建文件
    # base_dir已经在config中处理为正确的路径，不需要单独创建
    directories = [
        # 不需要单独创建base_dir，它应该已经存在
        config.screenshots_dir,
        os.path.join(config.base_dir, 'logs'),
        config.vector_db_persist_directory
    ]

    for dir_path in directories:
        os.makedirs(dir_path, exist_ok=True)
        print(f"✅ 目录已创建: {dir_path}")

    # 6. 重新初始化数据库
    print(f"\n5. 重新初始化数据库...")
    try:
        from lifetrace_backend.storage import db_manager
        db_manager._init_database()
        print("✅ SQLite数据库已重新初始化")

        # 初始化向量数据库
        try:
            from lifetrace_backend.vector_service import create_vector_service
            vector_service = create_vector_service(config, db_manager)
            if vector_service.is_enabled():
                print("✅ 向量数据库已重新初始化")
            else:
                print("ℹ️  向量数据库未启用")
        except Exception as ve:
            print(f"⚠️  向量数据库初始化失败: {ve}")

    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")

    print(f"\n✅ 数据库初始化完成!")


if __name__ == "__main__":
    manual_reset()
