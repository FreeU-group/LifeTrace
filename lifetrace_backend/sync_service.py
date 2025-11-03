#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步服务管理器
统一管理文件监控和数据库一致性检查服务
"""

import sys
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# 添加项目根目录到Python路径，以便直接运行此文件
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

from lifetrace_backend.config import config
from lifetrace_backend.consistency_checker import consistency_checker
from lifetrace_backend.file_monitor import file_monitor_service
from lifetrace_backend.logging_config import setup_logging

# 设置日志系统
logger_manager = setup_logging(config)
logger = logger_manager.get_sync_logger()


class SyncServiceManager:
    """同步服务管理器"""

    def __init__(self):
        self.running = False
        self.services = {
            "file_monitor": file_monitor_service,
            "consistency_checker": consistency_checker,
        }
        self.start_time: Optional[datetime] = None
        self.lock = threading.Lock()
        self.stats = {"total_operations": 0, "errors": 0, "service_restarts": 0}

    def start_all(self):
        """启动所有同步服务"""
        with self.lock:
            if self.running:
                logger.warning("同步服务已在运行")
                return

            logger.info("正在启动同步服务...")

            try:
                # 启动文件监控服务
                if (
                    hasattr(config, "enable_file_monitor")
                    and config.enable_file_monitor
                ):
                    try:
                        self.services["file_monitor"].start()
                        logger.info("文件监控服务已启动")
                        self.stats["total_operations"] += 1
                    except Exception as e:
                        logger.error(f"文件监控服务启动失败: {e}")
                        logger.debug(traceback.format_exc())
                        self.stats["errors"] += 1
                else:
                    logger.info("文件监控服务已禁用")

                # 启动一致性检查服务
                if (
                    hasattr(config, "enable_consistency_check")
                    and config.enable_consistency_check
                ):
                    try:
                        check_interval = getattr(
                            config, "consistency_check_interval", 300
                        )
                        self.services[
                            "consistency_checker"
                        ].check_interval = check_interval
                        self.services["consistency_checker"].start()
                        logger.info(
                            f"一致性检查服务已启动，检查间隔: {check_interval}秒"
                        )
                        self.stats["total_operations"] += 1
                    except Exception as e:
                        logger.error(f"一致性检查服务启动失败: {e}")
                        logger.debug(traceback.format_exc())
                        self.stats["errors"] += 1
                else:
                    logger.info("一致性检查服务已禁用")

                self.running = True
                self.start_time = datetime.now()
                logger.info("所有同步服务启动完成")

            except Exception as e:
                logger.error(f"启动同步服务失败: {e}")
                logger.debug(traceback.format_exc())
                self.stats["errors"] += 1
                self.stop_all()
                raise

    def stop_all(self):
        """停止所有同步服务"""
        with self.lock:
            if not self.running:
                return

            logger.info("正在停止同步服务...")

            try:
                # 停止所有服务
                for service_name, service in self.services.items():
                    try:
                        if hasattr(service, "stop") and service.is_running():
                            service.stop()
                            logger.info(f"{service_name} 已停止")
                            self.stats["total_operations"] += 1
                    except Exception as e:
                        logger.error(f"停止 {service_name} 失败: {e}")
                        logger.debug(traceback.format_exc())
                        self.stats["errors"] += 1

                self.running = False
                logger.info("所有同步服务已停止")

            except Exception as e:
                logger.error(f"停止同步服务失败: {e}")
                logger.debug(traceback.format_exc())
                self.stats["errors"] += 1

    def restart_all(self):
        """重启所有同步服务"""
        logger.info("重启同步服务")
        self.stop_all()
        time.sleep(1)  # 等待服务完全停止
        self.start_all()

    def get_status(self) -> Dict[str, Any]:
        """获取所有服务状态"""
        status = {
            "manager_running": self.running,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "stats": self.stats,
            "services": {},
        }

        for service_name, service in self.services.items():
            try:
                if hasattr(service, "get_status"):
                    status["services"][service_name] = service.get_status()
                elif hasattr(service, "is_running"):
                    status["services"][service_name] = {"running": service.is_running()}
                else:
                    status["services"][service_name] = {
                        "running": False,
                        "error": "Service does not support status check",
                    }
            except Exception as e:
                status["services"][service_name] = {"running": False, "error": str(e)}

        return status

    def force_consistency_check(self) -> Dict[str, Any]:
        """强制执行一致性检查"""
        try:
            if not self.services["consistency_checker"].is_running():
                return {"success": False, "error": "一致性检查服务未运行"}

            result = self.services["consistency_checker"].force_check()
            self.stats["total_operations"] += 1
            return {"success": True, "result": result}

        except Exception as e:
            logger.error(f"强制一致性检查失败: {e}")
            logger.debug(traceback.format_exc())
            self.stats["errors"] += 1
            return {"success": False, "error": str(e)}

    def restart_service(self, service_name: str) -> bool:
        """重启指定服务"""
        if service_name not in self.services:
            logger.error(f"未知服务: {service_name}")
            return False

        try:
            service = self.services[service_name]

            # 停止服务
            if hasattr(service, "stop") and service.is_running():
                service.stop()
                time.sleep(1)

            # 启动服务
            if hasattr(service, "start"):
                service.start()
                logger.info(f"服务 {service_name} 重启成功")
                self.stats["service_restarts"] += 1
                self.stats["total_operations"] += 1
                return True

        except Exception as e:
            logger.error(f"重启服务 {service_name} 失败: {e}")
            logger.debug(traceback.format_exc())
            self.stats["errors"] += 1

        return False

    def is_running(self) -> bool:
        """检查管理器是否运行中"""
        return self.running

    def get_service_logs(self, service_name: str, lines: int = 50) -> list:
        """获取服务日志（如果支持）"""
        # 这里可以扩展为从日志文件读取特定服务的日志
        # 目前返回空列表，可以根据需要实现
        return []

    def configure_service(self, service_name: str, **kwargs) -> bool:
        """配置服务参数"""
        if service_name not in self.services:
            return False

        try:
            service = self.services[service_name]

            # 为一致性检查器配置参数
            if service_name == "consistency_checker":
                if "check_interval" in kwargs:
                    service.check_interval = kwargs["check_interval"]
                    logger.info(f"一致性检查间隔已更新为: {kwargs['check_interval']}秒")

                if "vector_sync_interval" in kwargs and hasattr(
                    service, "vector_sync_interval"
                ):
                    service.vector_sync_interval = kwargs["vector_sync_interval"]
                    logger.info(
                        f"向量同步间隔已更新为: {kwargs['vector_sync_interval']}秒"
                    )

            return True

        except Exception as e:
            logger.error(f"配置服务 {service_name} 失败: {e}")
            logger.debug(traceback.format_exc())
            self.stats["errors"] += 1
            return False


class SyncServiceAPI:
    """同步服务API接口"""

    def __init__(self, manager: SyncServiceManager):
        self.manager = manager

    def get_status(self) -> Dict[str, Any]:
        """获取服务状态API"""
        return self.manager.get_status()

    def start_services(self) -> Dict[str, Any]:
        """启动服务API"""
        try:
            self.manager.start_all()
            return {"success": True, "message": "同步服务已启动"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def stop_services(self) -> Dict[str, Any]:
        """停止服务API"""
        try:
            self.manager.stop_all()
            return {"success": True, "message": "同步服务已停止"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def restart_services(self) -> Dict[str, Any]:
        """重启服务API"""
        try:
            self.manager.restart_all()
            return {"success": True, "message": "同步服务已重启"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def force_check(self) -> Dict[str, Any]:
        """强制检查API"""
        return self.manager.force_consistency_check()


# 全局同步服务管理器实例
sync_service_manager = SyncServiceManager()
sync_service_api = SyncServiceAPI(sync_service_manager)
