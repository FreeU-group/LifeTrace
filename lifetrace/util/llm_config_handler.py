#!/usr/bin/env python3
"""
LLM 配置变更处理器
负责处理 LLM 配置变更时的相关操作
"""

from lifetrace.util.config_watcher import ConfigChangeType
from lifetrace.util.logging_config import get_logger

logger = get_logger()


class LLMConfigHandler:
    """LLM 配置变更处理器 - 实现 ConfigChangeHandler 协议"""

    def __init__(self, deps_module, config_module):
        """初始化处理器

        Args:
            deps_module: dependencies 模块引用
            config_module: config 模块引用
        """
        self.deps = deps_module
        self.config = config_module
        logger.info("LLM 配置处理器已初始化")

    def handle_config_change(self, change_type: ConfigChangeType, old_value: dict, new_value: dict):
        """处理配置变更 - 实现 ConfigChangeHandler 协议

        Args:
            change_type: 配置变更类型
            old_value: 旧配置值
            new_value: 新配置值
        """
        try:
            if change_type == ConfigChangeType.LLM:
                logger.info("LLMConfigHandler 处理 LLM 配置变更")
                self._handle_llm_config_change(old_value, new_value)

        except Exception as e:
            logger.error(f"LLMConfigHandler 处理配置变更失败: {e}", exc_info=True)

    def _handle_llm_config_change(self, old_value: dict, new_value: dict):
        """处理 LLM 配置变更

        Args:
            old_value: 旧的 LLM 配置
            new_value: 新的 LLM 配置
        """
        logger.info("检测到 LLM 配置变更")

        # 更新配置状态
        self.deps.is_llm_configured = self.config.is_configured()
        status = "已配置" if self.deps.is_llm_configured else "未配置"
        logger.info(f"LLM 配置状态已更新: {status}")

        # 记录配置变更详情
        if old_value.get("api_key") != new_value.get("api_key"):
            logger.info("API Key 已变更")
        if old_value.get("base_url") != new_value.get("base_url"):
            logger.info(f"Base URL 已变更: {new_value.get('base_url')}")
        if old_value.get("model") != new_value.get("model"):
            logger.info(f"模型已变更: {new_value.get('model')}")

        # 注意：根据设计，不重新初始化 RAG 服务
        # RAG 服务会在下次调用时自动使用新配置
        logger.info("LLM 配置已更新，服务将在下次调用时使用新配置")


# 全局单例
_llm_config_handler_instance = None


def get_llm_config_handler(deps_module, config_module) -> LLMConfigHandler:
    """获取 LLM 配置处理器单例

    Args:
        deps_module: dependencies 模块引用
        config_module: config 模块引用

    Returns:
        LLMConfigHandler 实例
    """
    global _llm_config_handler_instance
    if _llm_config_handler_instance is None:
        _llm_config_handler_instance = LLMConfigHandler(deps_module, config_module)
    return _llm_config_handler_instance
