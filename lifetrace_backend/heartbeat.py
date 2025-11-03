#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
心跳系统模块

提供服务心跳监控、日志管理和自动重启功能
"""

import json
import logging
import os
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# 添加项目根目录到Python路径，以便直接运行此文件
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

from lifetrace_backend.config import config


class HeartbeatLogger:
    """心跳日志记录器"""

    def __init__(self, service_name: str, log_dir: str = None):
        self.service_name = service_name

        # 从配置文件读取参数
        self.log_dir = Path(log_dir or config.heartbeat_log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 心跳日志文件路径
        self.heartbeat_file = self.log_dir / f"{service_name}_heartbeat.log"

        # 从配置读取心跳参数
        self.heartbeat_interval = config.heartbeat_interval
        self.max_log_size = config.heartbeat_log_max_size_mb * 1024 * 1024  # 转换为字节
        self.max_log_files = config.heartbeat_log_max_files
        self.auto_cleanup = config.heartbeat_log_auto_cleanup

        # 心跳线程控制
        self._heartbeat_thread = None
        self._stop_event = threading.Event()
        self._running = False

        # 设置日志格式
        self.logger = logging.getLogger(f"heartbeat_{service_name}")
        self.logger.setLevel(logging.INFO)

        # 创建文件处理器
        handler = logging.FileHandler(self.heartbeat_file, encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def start_heartbeat(self):
        """启动心跳记录"""
        if self._running:
            return

        self._running = True
        self._stop_event.clear()
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop, daemon=True
        )
        self._heartbeat_thread.start()

        self.logger.info(f"心跳记录启动 - 服务: {self.service_name}")

    def stop_heartbeat(self):
        """停止心跳记录"""
        if not self._running:
            return

        self._running = False
        self._stop_event.set()

        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._heartbeat_thread.join(timeout=2)

        self.logger.info(f"心跳记录停止 - 服务: {self.service_name}")

    def _heartbeat_loop(self):
        """心跳循环"""
        while not self._stop_event.is_set():
            try:
                # 记录心跳
                heartbeat_data = {
                    "service": self.service_name,
                    "timestamp": datetime.now().isoformat(),
                    "pid": os.getpid(),
                    "status": "alive",
                }

                self.logger.info(
                    f"HEARTBEAT: {json.dumps(heartbeat_data, ensure_ascii=False)}"
                )

                # 检查日志文件大小并轮转
                self._rotate_log_if_needed()

            except Exception as e:
                # 心跳记录失败也要继续
                print(f"心跳记录失败: {e}")

            # 等待下一次心跳
            self._stop_event.wait(self.heartbeat_interval)

    def _rotate_log_if_needed(self):
        """检查并轮转日志文件"""
        try:
            if (
                self.heartbeat_file.exists()
                and self.heartbeat_file.stat().st_size > self.max_log_size
            ):
                self._rotate_logs()
        except Exception as e:
            print(f"日志轮转检查失败: {e}")

    def _rotate_logs(self):
        """轮转日志文件"""
        try:
            # 关闭当前日志处理器
            for handler in self.logger.handlers[:]:
                if isinstance(handler, logging.FileHandler):
                    handler.close()
                    self.logger.removeHandler(handler)

            # 重命名现有日志文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = (
                self.log_dir / f"{self.service_name}_heartbeat_{timestamp}.log"
            )

            if self.heartbeat_file.exists():
                self.heartbeat_file.rename(backup_file)

            # 清理旧的日志文件
            self._cleanup_old_logs()

            # 创建新的日志处理器
            handler = logging.FileHandler(self.heartbeat_file, encoding="utf-8")
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

            self.logger.info(f"日志轮转完成 - 备份文件: {backup_file.name}")

        except Exception as e:
            print(f"日志轮转失败: {e}")

    def _cleanup_old_logs(self):
        """清理旧的日志文件"""
        try:
            # 获取所有心跳日志文件
            pattern = f"{self.service_name}_heartbeat_*.log"
            log_files = list(self.log_dir.glob(pattern))

            # 按修改时间排序
            log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # 删除超过限制的文件
            for old_file in log_files[self.max_log_files :]:
                try:
                    old_file.unlink()
                    print(f"删除旧日志文件: {old_file.name}")
                except Exception as e:
                    print(f"删除日志文件失败 {old_file.name}: {e}")

        except Exception as e:
            print(f"清理旧日志失败: {e}")

    def record_heartbeat(self, custom_data: Dict = None):
        """手动记录心跳

        Args:
            custom_data: 自定义心跳数据
        """
        try:
            # 基础心跳数据
            heartbeat_data = {
                "service": self.service_name,
                "timestamp": datetime.now().isoformat(),
                "pid": os.getpid(),
                "status": "alive",
            }

            # 合并自定义数据
            if custom_data:
                heartbeat_data.update(custom_data)

            # 写入心跳文件（JSON格式，每行一个记录）
            with open(self.heartbeat_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(heartbeat_data, ensure_ascii=False) + "\n")

            # 检查日志文件大小并轮转
            self._rotate_log_if_needed()

        except Exception as e:
            print(f"记录心跳失败: {e}")

    def reset_log(self):
        """重置心跳日志文件"""
        try:
            if self.heartbeat_file.exists():
                # 备份当前日志
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = (
                    self.log_dir
                    / f"{self.service_name}_heartbeat_reset_{timestamp}.log"
                )
                self.heartbeat_file.rename(backup_file)
                print(f"心跳日志已重置，备份文件: {backup_file.name}")

            # 清理旧的日志文件
            self._cleanup_old_logs()

        except Exception as e:
            print(f"重置心跳日志失败: {e}")

    def get_log_size(self) -> int:
        """获取当前日志文件大小（字节）"""
        try:
            if self.heartbeat_file.exists():
                return self.heartbeat_file.stat().st_size
            return 0
        except Exception:
            return 0

    def get_log_info(self) -> Dict:
        """获取日志文件信息"""
        try:
            info = {
                "file_path": str(self.heartbeat_file),
                "exists": self.heartbeat_file.exists(),
                "size_bytes": 0,
                "size_mb": 0.0,
                "max_size_mb": self.max_log_size / (1024 * 1024),
                "backup_files": [],
            }

            if self.heartbeat_file.exists():
                size_bytes = self.heartbeat_file.stat().st_size
                info["size_bytes"] = size_bytes
                info["size_mb"] = size_bytes / (1024 * 1024)

            # 获取备份文件列表
            pattern = f"{self.service_name}_heartbeat_*.log"
            backup_files = list(self.log_dir.glob(pattern))
            info["backup_files"] = [f.name for f in backup_files]

            return info

        except Exception as e:
            return {"error": str(e)}


class HeartbeatMonitor:
    """心跳监控器"""

    def __init__(self, log_dir: str = None):
        self.log_dir = Path(log_dir or config.heartbeat_log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 从配置文件读取监控参数
        self.heartbeat_timeout = config.heartbeat_timeout
        self.check_interval = config.heartbeat_check_interval

        # 服务状态
        self.service_status: Dict[str, Dict] = {}

        # 监控线程控制
        self._monitor_thread = None
        self._stop_event = threading.Event()
        self._running = False

        # 回调函数
        self.on_service_timeout = None  # 服务超时回调
        self.on_service_recovered = None  # 服务恢复回调

    def start_monitoring(self):
        """启动心跳监控"""
        if self._running:
            return

        self._running = True
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

        print("心跳监控启动")

    def stop_monitoring(self):
        """停止心跳监控"""
        if not self._running:
            return

        self._running = False
        self._stop_event.set()

        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2)

        print("心跳监控停止")

    def _monitor_loop(self):
        """监控循环"""
        while not self._stop_event.is_set():
            try:
                self._check_all_services()
            except Exception as e:
                print(f"心跳监控检查失败: {e}")

            # 等待下一次检查
            self._stop_event.wait(self.check_interval)

    def _check_all_services(self):
        """检查所有服务的心跳状态"""
        # 获取所有心跳日志文件
        heartbeat_files = list(self.log_dir.glob("*_heartbeat.log"))

        current_time = datetime.now()

        for log_file in heartbeat_files:
            service_name = log_file.stem.replace("_heartbeat", "")

            try:
                last_heartbeat = self._get_last_heartbeat(log_file)

                if last_heartbeat:
                    # 计算心跳间隔
                    time_diff = (current_time - last_heartbeat).total_seconds()

                    # 更新服务状态
                    previous_status = self.service_status.get(service_name, {}).get(
                        "status"
                    )

                    if time_diff > self.heartbeat_timeout:
                        # 服务超时
                        self.service_status[service_name] = {
                            "status": "timeout",
                            "last_heartbeat": last_heartbeat,
                            "timeout_duration": time_diff,
                        }

                        # 触发超时回调
                        if previous_status != "timeout" and self.on_service_timeout:
                            self.on_service_timeout(service_name, time_diff)

                    else:
                        # 服务正常
                        self.service_status[service_name] = {
                            "status": "alive",
                            "last_heartbeat": last_heartbeat,
                            "timeout_duration": 0,
                        }

                        # 触发恢复回调
                        if previous_status == "timeout" and self.on_service_recovered:
                            self.on_service_recovered(service_name)

                else:
                    # 没有找到心跳记录
                    self.service_status[service_name] = {
                        "status": "no_heartbeat",
                        "last_heartbeat": None,
                        "timeout_duration": float("inf"),
                    }

            except Exception as e:
                print(f"检查服务 {service_name} 心跳失败: {e}")

    def _get_last_heartbeat(self, log_file: Path) -> Optional[datetime]:
        """获取最后一次心跳时间"""
        try:
            # 读取日志文件的最后几行
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # 从后往前查找最新的心跳记录
            for line in reversed(lines[-50:]):  # 只检查最后50行
                line = line.strip()
                if line:  # 跳过空行
                    try:
                        # 直接解析JSON格式的心跳数据
                        heartbeat_data = json.loads(line)

                        # 解析时间戳
                        timestamp_str = heartbeat_data.get("timestamp")
                        if timestamp_str:
                            return datetime.fromisoformat(timestamp_str)

                    except (json.JSONDecodeError, ValueError, KeyError):
                        continue

            return None

        except Exception as e:
            print(f"读取心跳日志失败 {log_file}: {e}")
            return None

    def get_service_status(self, service_name: str) -> Optional[Dict]:
        """获取指定服务的状态"""
        return self.service_status.get(service_name)

    def get_all_status(self) -> Dict[str, Dict]:
        """获取所有服务的状态"""
        return self.service_status.copy()

    def is_service_alive(self, service_name: str) -> bool:
        """检查服务是否存活"""
        status = self.get_service_status(service_name)
        return status and status.get("status") == "alive"
