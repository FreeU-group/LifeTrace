#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库一致性检查服务
定期检查文件系统与数据库的一致性，自动修复不一致的数据
"""

import sys
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Set

# 添加项目根目录到Python路径，以便直接运行此文件
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

from lifetrace_backend.config import config
from lifetrace_backend.logging_config import setup_logging
from lifetrace_backend.models import OCRResult, ProcessingQueue, Screenshot, SearchIndex
from lifetrace_backend.storage import db_manager

# 初始化日志系统
logger_manager = setup_logging()
logger = logger_manager.get_logger("consistency_checker", "sync")


class ConsistencyChecker:
    """数据库一致性检查器"""

    def __init__(self, check_interval: int = 300):  # 默认5分钟检查一次
        self.check_interval = check_interval
        self.running = False
        self.check_thread: Optional[threading.Thread] = None
        self.screenshots_dir = Path(config.screenshots_dir)
        self.last_check_time = None
        self.stats = {
            "total_checks": 0,
            "orphaned_records_found": 0,
            "orphaned_files_found": 0,
            "cleanup_operations": 0,
            "errors": 0,
        }

    def start(self):
        """启动一致性检查服务"""
        if self.running:
            logger.warning("一致性检查服务已在运行")
            return

        self.running = True
        self.check_thread = threading.Thread(target=self._check_loop, daemon=True)
        self.check_thread.start()
        logger.info(f"一致性检查服务已启动，检查间隔: {self.check_interval}秒")

    def stop(self):
        """停止一致性检查服务"""
        if not self.running:
            return

        self.running = False
        if self.check_thread and self.check_thread.is_alive():
            self.check_thread.join(timeout=5)

        logger.info("一致性检查服务已停止")

    def _check_loop(self):
        """检查循环"""
        while self.running:
            try:
                result = self.perform_consistency_check()
                self.stats["total_checks"] += 1
                self.last_check_time = datetime.now()

                logger.info(
                    f"一致性检查完成: 孤立记录 {result.get('orphaned_db_records', 0)}, "
                    f"孤立文件 {result.get('orphaned_files', 0)}, "
                    f"清理操作 {result.get('cleaned_records', 0)}"
                )

            except Exception as e:
                self.stats["errors"] += 1
                logger.error(f"一致性检查失败: {e}")
                logger.debug(traceback.format_exc())

            # 等待下次检查
            for _ in range(self.check_interval):
                if not self.running:
                    break
                time.sleep(1)

    def perform_consistency_check(self) -> dict:
        """执行一致性检查"""
        logger.debug("开始执行一致性检查")

        try:
            # 获取文件系统中的截图文件
            fs_files = self._get_filesystem_files()
            logger.debug(f"文件系统中找到 {len(fs_files)} 个截图文件")

            # 获取数据库中的截图记录
            db_files = self._get_database_files()
            logger.debug(f"数据库中找到 {len(db_files)} 个截图记录")

            # 找出不一致的数据
            orphaned_db_records = db_files - fs_files  # 数据库中有但文件系统中没有
            orphaned_files = fs_files - db_files  # 文件系统中有但数据库中没有

            result = {
                "check_time": datetime.now().isoformat(),
                "total_fs_files": len(fs_files),
                "total_db_records": len(db_files),
                "orphaned_db_records": len(orphaned_db_records),
                "orphaned_files": len(orphaned_files),
                "cleaned_records": 0,
                "errors": [],
            }

            # 记录统计信息
            self.stats["orphaned_records_found"] += len(orphaned_db_records)
            self.stats["orphaned_files_found"] += len(orphaned_files)

            # 清理孤立的数据库记录
            if orphaned_db_records:
                cleaned_count = self._cleanup_orphaned_records(orphaned_db_records)
                result["cleaned_records"] = cleaned_count
                self.stats["cleanup_operations"] += cleaned_count
                logger.info(f"清理了 {cleaned_count} 条孤立的数据库记录")

            # 记录孤立的文件（不自动处理，可能是新文件）
            if orphaned_files:
                if len(orphaned_files) <= 5:
                    logger.info(
                        f"发现 {len(orphaned_files)} 个孤立文件（可能是新文件）: {list(orphaned_files)}"
                    )
                else:
                    logger.info(
                        f"发现 {len(orphaned_files)} 个孤立文件（可能是新文件）"
                    )
                    for file_path in list(orphaned_files)[:5]:  # 只记录前5个
                        logger.debug(f"孤立文件: {file_path}")

            if orphaned_db_records or orphaned_files:
                logger.info(
                    f"一致性检查完成 - 文件系统: {len(fs_files)}, "
                    f"数据库: {len(db_files)}, 清理: {result['cleaned_records']}"
                )
            else:
                logger.debug("一致性检查完成 - 数据一致")

            return result

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"一致性检查执行失败: {e}")
            logger.debug(traceback.format_exc())
            return {"check_time": datetime.now().isoformat(), "error": str(e)}

    def _get_filesystem_files(self) -> Set[str]:
        """获取文件系统中的截图文件路径"""
        files = set()

        if not self.screenshots_dir.exists():
            return files

        try:
            for file_path in self.screenshots_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in [
                    ".png",
                    ".jpg",
                    ".jpeg",
                ]:
                    files.add(str(file_path))
        except Exception as e:
            logger.error(f"读取文件系统失败: {e}")

        return files

    def _get_database_files(self) -> Set[str]:
        """获取数据库中的截图文件路径"""
        files = set()

        try:
            with db_manager.get_session() as session:
                screenshots = session.query(Screenshot.file_path).all()
                files = {screenshot.file_path for screenshot in screenshots}
        except Exception as e:
            logger.error(f"读取数据库失败: {e}")

        return files

    def _cleanup_orphaned_records(self, orphaned_files: Set[str]) -> int:
        """清理孤立的数据库记录"""
        cleaned_count = 0

        try:
            with db_manager.get_session() as session:
                for file_path in orphaned_files:
                    try:
                        # 查找对应的截图记录
                        screenshot = (
                            session.query(Screenshot)
                            .filter(Screenshot.file_path == file_path)
                            .first()
                        )

                        if not screenshot:
                            continue

                        screenshot_id = screenshot.id

                        # 统计要删除的关联记录数
                        ocr_count = (
                            session.query(OCRResult)
                            .filter_by(screenshot_id=screenshot_id)
                            .count()
                        )
                        index_count = (
                            session.query(SearchIndex)
                            .filter_by(screenshot_id=screenshot_id)
                            .count()
                        )
                        queue_count = (
                            session.query(ProcessingQueue)
                            .filter_by(screenshot_id=screenshot_id)
                            .count()
                        )
                        total_related = ocr_count + index_count + queue_count

                        # 删除相关的OCR结果
                        session.query(OCRResult).filter_by(
                            screenshot_id=screenshot_id
                        ).delete()

                        # 删除相关的搜索索引
                        session.query(SearchIndex).filter_by(
                            screenshot_id=screenshot_id
                        ).delete()

                        # 删除相关的处理队列
                        session.query(ProcessingQueue).filter_by(
                            screenshot_id=screenshot_id
                        ).delete()

                        # 删除截图记录
                        session.delete(screenshot)
                        cleaned_count += 1

                        logger.debug(
                            f"清理孤立记录: {file_path} (ID: {screenshot_id}), 关联记录: {total_related}"
                        )

                    except Exception as e:
                        logger.error(f"清理记录失败 {file_path}: {e}")
                        logger.debug(traceback.format_exc())
                        continue

        except Exception as e:
            logger.error(f"批量清理失败: {e}")
            logger.debug(traceback.format_exc())

        return cleaned_count

    def force_check(self) -> dict:
        """强制执行一次检查"""
        logger.info("执行强制一致性检查")
        return self.perform_consistency_check()

    def get_status(self) -> dict:
        """获取检查器状态"""
        return {
            "running": self.running,
            "check_interval": self.check_interval,
            "last_check_time": (
                self.last_check_time.isoformat() if self.last_check_time else None
            ),
            "stats": self.stats.copy(),
        }

    def is_running(self) -> bool:
        """检查服务是否运行中"""
        return self.running


class AdvancedConsistencyChecker(ConsistencyChecker):
    """高级一致性检查器，包含向量数据库同步"""

    def __init__(
        self, check_interval: int = 300, vector_sync_interval: int = 1800
    ):  # 向量同步30分钟一次
        super().__init__(check_interval)
        self.vector_sync_interval = vector_sync_interval
        self.last_vector_sync = None

    def perform_consistency_check(self) -> dict:
        """执行高级一致性检查，包含向量数据库同步"""
        result = super().perform_consistency_check()

        # 检查是否需要同步向量数据库
        now = datetime.now()
        if (
            self.last_vector_sync is None
            or (now - self.last_vector_sync).total_seconds()
            >= self.vector_sync_interval
        ):
            try:
                vector_result = self._sync_vector_database()
                result.update(vector_result)
                self.last_vector_sync = now
            except Exception as e:
                logger.error(f"向量数据库同步失败: {e}")
                result["vector_sync_error"] = str(e)

        return result

    def _sync_vector_database(self) -> dict:
        """同步向量数据库"""
        try:
            from lifetrace_backend.vector_service import create_vector_service

            vector_service = create_vector_service(config, db_manager)
            if not vector_service.is_enabled():
                return {"vector_sync": "disabled"}

            # 获取统计信息
            with db_manager.get_session() as session:
                sqlite_count = session.query(OCRResult).count()

            vector_stats = vector_service.get_stats()
            vector_count = vector_stats.get("document_count", 0)

            # 如果数量不一致，执行智能同步
            if sqlite_count != vector_count:
                logger.info(
                    f"向量数据库不一致 (SQLite: {sqlite_count}, Vector: {vector_count})，执行同步"
                )
                synced_count = vector_service.sync_from_database()
                return {
                    "vector_sync": "completed",
                    "sqlite_count": sqlite_count,
                    "vector_count_before": vector_count,
                    "synced_count": synced_count,
                }
            else:
                return {
                    "vector_sync": "consistent",
                    "sqlite_count": sqlite_count,
                    "vector_count": vector_count,
                }

        except Exception as e:
            logger.error(f"向量数据库同步检查失败: {e}")
            raise


# 全局一致性检查器实例
consistency_checker = AdvancedConsistencyChecker()
