import logging
import os
import sys
import threading
import time
from pathlib import Path
from queue import Empty, Queue
from typing import Set

# 添加项目根目录到Python路径，以便直接运行此文件
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

import imagehash
from PIL import Image
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from lifetrace_backend.config import config
from lifetrace_backend.consistency_checker import ConsistencyChecker
from lifetrace_backend.logging_config import setup_logging
from lifetrace_backend.simple_heartbeat import SimpleHeartbeatSender
from lifetrace_backend.storage import db_manager
from lifetrace_backend.utils import get_active_window_info

# 设置日志系统
logger_manager = setup_logging(config)
logger = logger_manager.get_processor_logger()


class ScreenshotHandler(FileSystemEventHandler):
    """截图文件事件处理器"""

    def __init__(self, processor):
        self.processor = processor

    def on_created(self, event):
        """文件创建事件"""
        if not event.is_directory and self._is_screenshot_file(event.src_path):
            logger.debug(f"检测到新截图: {event.src_path}")
            self.processor.add_file_to_queue(event.src_path)

    def on_modified(self, event):
        """文件修改事件"""
        if not event.is_directory and self._is_screenshot_file(event.src_path):
            logger.debug(f"检测到截图修改: {event.src_path}")
            self.processor.add_file_to_queue(event.src_path)

    def _is_screenshot_file(self, file_path: str) -> bool:
        """检查是否为截图文件"""
        return file_path.lower().endswith((".png", ".jpg", ".jpeg"))


class FileProcessor:
    """文件处理器"""

    def __init__(self):
        self.config = config
        self.screenshots_dir = self.config.screenshots_dir
        self.batch_size = self.config.get("processing.batch_size", 10)
        self.queue_size = self.config.get("processing.queue_size", 100)
        self.max_workers = self.config.get("processing.max_workers", 2)

        # 文件处理队列
        self.file_queue = Queue(maxsize=self.queue_size)
        self.processed_files: Set[str] = set()

        # 线程控制
        self.running = False
        self.worker_threads = []

        # 文件监听
        self.observer = Observer()
        self.event_handler = ScreenshotHandler(self)

        # 一致性检查器
        self.consistency_checker = ConsistencyChecker(
            check_interval=self.config.get("consistency_check.interval", 300)
        )

        # 初始化UDP心跳发送器
        self.heartbeat_sender = SimpleHeartbeatSender("processor")

        logging.info("文件处理器初始化完成")

    def add_file_to_queue(self, file_path: str):
        """将文件添加到处理队列"""
        if file_path in self.processed_files:
            logging.debug(f"文件已处理过，跳过: {file_path}")
            return

        try:
            # 等待文件写入完成
            time.sleep(0.5)

            if not os.path.exists(file_path):
                logging.warning(f"文件不存在: {file_path}")
                return

            self.file_queue.put(file_path, block=False)
            logging.debug(f"文件加入处理队列: {file_path}")

        except Exception as e:
            logging.warning(f"无法添加文件到队列 {file_path}: {e}")

    def process_file(self, file_path: str) -> bool:
        """处理单个文件"""
        try:
            if not os.path.exists(file_path):
                logging.warning(f"文件不存在: {file_path}")
                return False

            # 获取文件信息
            file_stats = os.stat(file_path)
            file_size = file_stats.st_size

            if file_size == 0:
                logging.warning(f"文件为空: {file_path}")
                return False

            # 获取图像尺寸和哈希
            try:
                with Image.open(file_path) as img:
                    width, height = img.size
                    image_hash = str(imagehash.phash(img))
            except Exception as e:
                logging.error(f"无法处理图像文件 {file_path}: {e}")
                return False

            # 获取屏幕ID（从文件名解析）
            screen_id = self._extract_screen_id(file_path)

            # 获取窗口信息（这里可能不准确，因为是事后处理）
            app_name, window_title = get_active_window_info()

            # 添加到数据库
            screenshot_id = db_manager.add_screenshot(
                file_path=file_path,
                file_hash=image_hash,
                width=width,
                height=height,
                screen_id=screen_id,
                app_name=app_name,
                window_title=window_title,
            )

            if screenshot_id:
                logging.info(f"文件处理完成: {file_path} (ID: {screenshot_id})")

                # 标记为已处理
                self.processed_files.add(file_path)
                return True
            else:
                logging.warning(f"添加截图记录失败: {file_path}")
                return False

        except Exception as e:
            logging.error(f"处理文件失败 {file_path}: {e}")
            return False

    def _extract_screen_id(self, file_path: str) -> int:
        """从文件名提取屏幕ID"""
        try:
            filename = os.path.basename(file_path)
            if filename.startswith("screen_"):
                parts = filename.split("_")
                if len(parts) >= 2:
                    return int(parts[1])
        except (ValueError, IndexError):
            pass
        return 0

    def _worker_thread(self):
        """工作线程"""
        while self.running:
            try:
                # 从队列获取文件
                file_path = self.file_queue.get(timeout=1.0)

                # 处理文件
                self.process_file(file_path)

                # 标记任务完成
                self.file_queue.task_done()

            except Empty:
                continue
            except Exception as e:
                logging.error(f"工作线程异常: {e}")

    def scan_existing_files(self):
        """扫描现有文件"""
        if not os.path.exists(self.screenshots_dir):
            logging.info("截图目录不存在，跳过扫描")
            return

        logging.info(f"扫描现有截图文件: {self.screenshots_dir}")

        screenshot_files = []
        for file_path in Path(self.screenshots_dir).glob("*.png"):
            if file_path.is_file():
                screenshot_files.append(str(file_path))

        # 检查哪些文件未处理
        unprocessed_files = []
        for file_path in screenshot_files:
            # 简单检查：如果数据库中没有相同路径的记录，则认为未处理
            screenshot = db_manager.get_screenshot_by_path(file_path)
            if not screenshot:
                unprocessed_files.append(file_path)

        logging.info(f"发现 {len(unprocessed_files)} 个未处理文件")

        # 批量添加到队列
        for file_path in unprocessed_files:
            self.add_file_to_queue(file_path)

    def start(self):
        """启动文件处理器"""
        self.running = True

        # 启动工作线程
        for i in range(self.max_workers):
            thread = threading.Thread(
                target=self._worker_thread, name=f"FileWorker-{i}"
            )
            thread.daemon = True
            thread.start()
            self.worker_threads.append(thread)

        # 扫描现有文件
        self.scan_existing_files()

        # 启动文件监听
        self.observer.schedule(
            self.event_handler, self.screenshots_dir, recursive=False
        )
        self.observer.start()

        # 启动一致性检查器
        self.consistency_checker.start()

        logging.info("文件处理器启动完成（包含一致性检查功能）")

        # 启动UDP心跳发送
        self.heartbeat_sender.start(interval=1.0)

        try:
            while self.running:
                # 发送心跳（包含队列状态信息）
                queue_status = self.get_queue_status()
                self.heartbeat_sender.send_heartbeat(
                    {
                        "status": "running",
                        "queue_size": queue_status["queue_size"],
                        "processed_count": queue_status["processed_count"],
                        "worker_count": queue_status["worker_count"],
                    }
                )

                time.sleep(1)

                # 定期清理已处理文件集合（防止内存泄漏）
                if len(self.processed_files) > 10000:
                    self.processed_files.clear()
                    logging.info("清理已处理文件记录")

        except KeyboardInterrupt:
            logging.info("收到停止信号")
            self.heartbeat_sender.send_heartbeat(
                {"status": "stopped", "reason": "keyboard_interrupt"}
            )
        except Exception as e:
            logging.error(f"处理器运行异常: {e}")
            self.heartbeat_sender.send_heartbeat({"status": "error", "error": str(e)})
        finally:
            self.stop()

    def stop(self):
        """停止文件处理器"""
        logging.info("正在停止文件处理器...")

        self.running = False

        # 停止UDP心跳发送
        self.heartbeat_sender.stop()

        # 停止一致性检查器
        self.consistency_checker.stop()

        # 停止文件监听
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()

        # 等待队列处理完成
        self.file_queue.join()

        # 等待工作线程结束
        for thread in self.worker_threads:
            if thread.is_alive():
                thread.join(timeout=5.0)

        logging.info("文件处理器已停止")

    def get_queue_status(self) -> dict:
        """获取队列状态"""
        return {
            "queue_size": self.file_queue.qsize(),
            "processed_count": len(self.processed_files),
            "worker_count": len([t for t in self.worker_threads if t.is_alive()]),
            "running": self.running,
        }


# 扩展数据库管理器，添加根据路径查询截图的方法
def get_screenshot_by_path(self, file_path: str):
    """根据文件路径获取截图"""
    try:
        with self.get_session() as session:
            from lifetrace_backend.models import Screenshot

            return session.query(Screenshot).filter_by(file_path=file_path).first()
    except Exception as e:
        logging.error(f"根据路径获取截图失败: {e}")
        return None


# 动态添加方法到数据库管理器
db_manager.get_screenshot_by_path = get_screenshot_by_path.__get__(
    db_manager, type(db_manager)
)


def main():
    """主函数 - 命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="LifeTrace File Processor")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--workers", type=int, help="工作线程数")
    parser.add_argument("--batch-size", type=int, help="批处理大小")
    parser.add_argument("--debug", action="store_true", help="启用调试日志")

    args = parser.parse_args()

    # 日志已在模块顶部通过logging_config配置

    # 更新配置
    if args.workers:
        config.set("processing.max_workers", args.workers)

    if args.batch_size:
        config.set("processing.batch_size", args.batch_size)

    # 创建并启动文件处理器
    processor = FileProcessor()
    processor.start()


if __name__ == "__main__":
    main()
