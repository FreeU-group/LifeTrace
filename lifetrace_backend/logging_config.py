#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LifeTrace 统一日志配置模块
提供集中的日志管理和配置功能
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class LifeTraceLogger:
    """LifeTrace 日志管理器"""

    def __init__(self, config=None):
        self.config = config
        self.loggers: Dict[str, logging.Logger] = {}
        self._setup_log_directories()

    def _setup_log_directories(self):
        """创建日志目录结构"""
        if self.config:
            base_dir = getattr(self.config, "base_dir")
        else:
            # 如果没有配置，使用项目根目录下的data目录
            base_dir = os.path.join(Path(__file__).parent.parent, "data")

        self.log_dir = os.path.join(base_dir, "logs")
        os.makedirs(self.log_dir, exist_ok=True)

        # 创建各模块的日志子目录
        for subdir in ["core", "sync", "debug"]:
            os.makedirs(os.path.join(self.log_dir, subdir), exist_ok=True)

    def get_logger(
        self,
        name: str,
        module_type: str = "core",
        log_level: str = "INFO",
        enable_file_logging: bool = True,
        enable_console_logging: bool = True,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
    ) -> logging.Logger:
        """获取或创建指定名称的日志器

        Args:
            name: 日志器名称
            module_type: 模块类型 ('core', 'sync', 'debug')
            log_level: 日志级别
            enable_file_logging: 是否启用文件日志
            enable_console_logging: 是否启用控制台日志
            max_bytes: 日志文件最大大小
            backup_count: 备份文件数量
        """
        if name in self.loggers:
            return self.loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

        # 清除现有的处理器
        logger.handlers.clear()

        # 创建格式化器
        detailed_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        )
        simple_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # 文件日志处理器
        if enable_file_logging:
            log_file = os.path.join(self.log_dir, module_type, f"{name}.log")
            file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
            )
            file_handler.setFormatter(detailed_formatter)
            logger.addHandler(file_handler)

        # 控制台日志处理器
        if enable_console_logging:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(simple_formatter)
            logger.addHandler(console_handler)

        # 防止日志传播到根日志器
        logger.propagate = False

        self.loggers[name] = logger
        return logger

    def get_main_logger(self) -> logging.Logger:
        """获取主日志器，记录所有重要事件"""
        return self.get_logger(
            "lifetrace_main",
            module_type="core",
            log_level=self._get_config_value("logging.main_log_level", "INFO"),
        )

    def get_server_logger(self) -> logging.Logger:
        """获取服务器日志器"""
        return self.get_logger(
            "lifetrace_server",
            module_type="core",
            log_level=self._get_config_value("logging.server_log_level", "INFO"),
        )

    def get_recorder_logger(self) -> logging.Logger:
        """获取录制器日志器"""
        return self.get_logger(
            "lifetrace_recorder",
            module_type="core",
            log_level=self._get_config_value("logging.recorder_log_level", "INFO"),
        )

    def get_processor_logger(self) -> logging.Logger:
        """获取处理器日志器"""
        return self.get_logger(
            "lifetrace_processor",
            module_type="core",
            log_level=self._get_config_value("logging.processor_log_level", "INFO"),
        )

    def get_ocr_logger(self) -> logging.Logger:
        """获取OCR日志器"""
        return self.get_logger(
            "lifetrace_ocr",
            module_type="core",
            log_level=self._get_config_value("logging.ocr_log_level", "INFO"),
        )

    def get_vector_logger(self) -> logging.Logger:
        """获取向量数据库日志器"""
        return self.get_logger(
            "lifetrace_vector",
            module_type="core",
            log_level=self._get_config_value("logging.vector_log_level", "INFO"),
        )

    def get_sync_logger(self) -> logging.Logger:
        """获取同步服务日志器"""
        return self.get_logger(
            "lifetrace_sync",
            module_type="sync",
            log_level=self._get_config_value("logging.sync_log_level", "INFO"),
        )

    def get_consistency_logger(self) -> logging.Logger:
        """获取一致性检查日志器"""
        return self.get_logger(
            "lifetrace_consistency",
            module_type="sync",
            log_level=self._get_config_value("logging.consistency_log_level", "INFO"),
        )

    def get_file_monitor_logger(self) -> logging.Logger:
        """获取文件监控日志器"""
        return self.get_logger(
            "lifetrace_file_monitor",
            module_type="sync",
            log_level=self._get_config_value("logging.file_monitor_log_level", "INFO"),
        )

    def get_debug_logger(self, name: str) -> logging.Logger:
        """获取调试日志器"""
        return self.get_logger(
            f"debug_{name}",
            module_type="debug",
            log_level="DEBUG",
            enable_console_logging=True,
        )

    def _get_config_value(self, key: str, default):
        """从配置中获取值"""
        if not self.config:
            return default

        keys = key.split(".")
        value = self.config._config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set_global_log_level(self, level: str):
        """设置全局日志级别"""
        log_level = getattr(logging, level.upper(), logging.INFO)
        for logger in self.loggers.values():
            logger.setLevel(log_level)

    def cleanup_old_logs(self, days: int = 30):
        """清理旧日志文件"""
        import time

        cutoff_time = time.time() - (days * 24 * 60 * 60)

        for root, dirs, files in os.walk(self.log_dir):
            for file in files:
                if file.endswith(".log"):
                    file_path = os.path.join(root, file)
                    if os.path.getmtime(file_path) < cutoff_time:
                        try:
                            os.remove(file_path)
                            print(f"已删除旧日志文件: {file_path}")
                        except Exception as e:
                            print(f"删除日志文件失败 {file_path}: {e}")

    def get_log_status(self) -> Dict:
        """获取日志系统状态"""
        status = {
            "log_directory": self.log_dir,
            "active_loggers": len(self.loggers),
            "logger_names": list(self.loggers.keys()),
            "log_files": [],
        }

        # 统计日志文件
        for root, dirs, files in os.walk(self.log_dir):
            for file in files:
                if file.endswith(".log"):
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    status["log_files"].append(
                        {
                            "path": file_path,
                            "size_mb": round(file_size / (1024 * 1024), 2),
                            "modified": datetime.fromtimestamp(
                                os.path.getmtime(file_path)
                            ).isoformat(),
                        }
                    )

        return status


# 全局日志管理器实例
_logger_manager: Optional[LifeTraceLogger] = None


def setup_logging(config=None) -> LifeTraceLogger:
    """设置日志系统"""
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = LifeTraceLogger(config)
    return _logger_manager


def get_logger_manager() -> Optional[LifeTraceLogger]:
    """获取日志管理器实例"""
    return _logger_manager


def get_logger(name: str, module_type: str = "core", **kwargs) -> logging.Logger:
    """便捷函数：获取日志器"""
    if _logger_manager is None:
        setup_logging()
    return _logger_manager.get_logger(name, module_type, **kwargs)
