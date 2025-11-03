#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件系统监控服务
监控截图目录的文件变化，自动同步数据库
"""

import logging
import os
import sys
import threading
import traceback
from pathlib import Path
from typing import Optional, Set

# 添加项目根目录到Python路径，以便直接运行此文件
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from lifetrace_backend.config import config
from lifetrace_backend.models import OCRResult, ProcessingQueue, Screenshot, SearchIndex
from lifetrace_backend.storage import db_manager


class ScreenshotFileHandler(FileSystemEventHandler):
    """截图文件事件处理器"""

    def __init__(self, sync_service):
        super().__init__()
        self.sync_service = sync_service
        self.logger = logging.getLogger(__name__)
        self.deleted_files: Set[str] = set()
        self.lock = threading.Lock()

        # 配置日志格式
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(
                getattr(
                    logging,
                    getattr(config, "sync_service_log_level", "INFO"),
                    logging.INFO,
                )
            )

    def on_deleted(self, event):
        """文件删除事件处理"""
        try:
            if event.is_directory:
                return

            file_path = event.src_path
            if self._is_screenshot_file(file_path):
                with self.lock:
                    self.deleted_files.add(file_path)
                # self.logger.info(f"检测到截图文件删除: {file_path}")
                # 延迟处理，避免频繁的数据库操作
                threading.Timer(
                    2.0, self._process_deleted_file, args=[file_path]
                ).start()
        except Exception as e:
            self.logger.error(f"处理文件删除事件失败: {e}")
            self.logger.debug(traceback.format_exc())

    def on_moved(self, event):
        """文件移动事件处理（视为删除）"""
        try:
            if event.is_directory:
                return

            src_path = event.src_path
            if self._is_screenshot_file(src_path):
                with self.lock:
                    self.deleted_files.add(src_path)
                # self.logger.info(f"检测到截图文件移动: {src_path} -> {event.dest_path}")
                threading.Timer(
                    2.0, self._process_deleted_file, args=[src_path]
                ).start()
        except Exception as e:
            self.logger.error(f"处理文件移动事件失败: {e}")
            self.logger.debug(traceback.format_exc())

    def _is_screenshot_file(self, file_path: str) -> bool:
        """检查是否为截图文件"""
        return file_path.lower().endswith((".png", ".jpg", ".jpeg"))

    def _process_deleted_file(self, file_path: str):
        """处理删除的文件"""
        try:
            with self.lock:
                if file_path not in self.deleted_files:
                    return
                self.deleted_files.discard(file_path)

            # 再次检查文件是否真的被删除
            if os.path.exists(file_path):
                self.logger.info(f"文件仍存在，跳过删除处理: {file_path}")
                return

            # 查找并删除对应的数据库记录
            self.sync_service.cleanup_deleted_file(file_path)

        except Exception as e:
            self.logger.error(f"处理删除文件失败 {file_path}: {e}")
            self.logger.debug(traceback.format_exc())


class FileMonitorService:
    """文件监控服务"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.observer: Optional[Observer] = None
        self.handler: Optional[ScreenshotFileHandler] = None
        self.running = False
        self.screenshots_dir = Path(config.screenshots_dir)

    def start(self):
        """启动文件监控"""
        if self.running:
            self.logger.warning("文件监控服务已在运行")
            return

        try:
            # 确保截图目录存在
            self.screenshots_dir.mkdir(parents=True, exist_ok=True)

            # 创建观察者和处理器
            self.observer = Observer()
            self.handler = ScreenshotFileHandler(self)

            # 监控截图目录
            self.observer.schedule(
                self.handler, str(self.screenshots_dir), recursive=False
            )

            self.observer.start()
            self.running = True
            self.logger.info(f"文件监控服务已启动，监控目录: {self.screenshots_dir}")

        except Exception as e:
            self.logger.error(f"启动文件监控服务失败: {e}")
            self.stop()

    def stop(self):
        """停止文件监控"""
        if not self.running:
            return

        try:
            if self.observer:
                self.observer.stop()
                self.observer.join(timeout=5)

            self.running = False
            self.logger.info("文件监控服务已停止")

        except Exception as e:
            self.logger.error(f"停止文件监控服务失败: {e}")

    def cleanup_deleted_file(self, file_path: str):
        """清理删除文件对应的数据库记录"""
        try:
            with db_manager.get_session() as session:
                # 查找对应的截图记录
                screenshot = (
                    session.query(Screenshot)
                    .filter(Screenshot.file_path == file_path)
                    .first()
                )

                if not screenshot:
                    self.logger.debug(f"未找到文件对应的数据库记录: {file_path}")
                    return

                screenshot_id = screenshot.id

                # 删除相关的OCR结果
                ocr_count = (
                    session.query(OCRResult)
                    .filter_by(screenshot_id=screenshot_id)
                    .delete()
                )

                # 删除相关的搜索索引
                index_count = (
                    session.query(SearchIndex)
                    .filter_by(screenshot_id=screenshot_id)
                    .delete()
                )

                # 删除相关的处理队列
                queue_count = (
                    session.query(ProcessingQueue)
                    .filter_by(screenshot_id=screenshot_id)
                    .delete()
                )

                # 删除截图记录
                session.delete(screenshot)

                total_deleted = ocr_count + index_count + queue_count + 1
                self.logger.info(
                    f"已清理删除文件的数据库记录: {file_path}, "
                    f"OCR记录: {ocr_count}, 索引记录: {index_count}, 队列记录: {queue_count}, 总计: {total_deleted}"
                )

        except Exception as e:
            self.logger.error(f"清理删除文件的数据库记录失败 {file_path}: {e}")
            self.logger.debug(traceback.format_exc())

            # 记录详细的错误信息用于调试
            try:
                with db_manager.get_session() as session:
                    screenshot_count = session.query(Screenshot).count()
                    self.logger.debug(f"当前数据库中有 {screenshot_count} 条截图记录")
            except Exception as db_error:
                self.logger.error(f"获取数据库状态失败: {db_error}")

    def is_running(self) -> bool:
        """检查服务是否运行中"""
        return self.running


# 全局文件监控服务实例
file_monitor_service = FileMonitorService()
