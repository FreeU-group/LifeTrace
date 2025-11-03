#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跨平台应用名称映射模块
提供友好的应用名称到实际进程名的映射功能
"""

import platform
from typing import Dict, List, Set

# 跨平台应用名称映射字典
# key: 友好的应用名称（用户配置时使用）
# value: 字典，包含各平台的进程名列表
APP_MAPPING: Dict[str, Dict[str, List[str]]] = {
    # 即时通讯软件
    "微信": {
        "Windows": ["WeChat.exe", "Weixin.exe"],
        "Darwin": ["WeChat"],  # macOS
        "Linux": ["wechat", "electronic-wechat"],
    },
    "WeChat": {
        "Windows": ["WeChat.exe", "Weixin.exe"],
        "Darwin": ["WeChat"],  # macOS
        "Linux": ["wechat", "electronic-wechat"],
    },
    "QQ": {
        "Windows": ["QQ.exe", "QQScLauncher.exe"],
        "Darwin": ["QQ"],
        "Linux": ["qq", "linuxqq"],
    },
    "钉钉": {
        "Windows": ["DingTalk.exe"],
        "Darwin": ["DingTalk"],
        "Linux": ["dingtalk"],
    },
    "企业微信": {
        "Windows": ["WXWork.exe"],
        "Darwin": ["企业微信"],
        "Linux": ["wxwork"],
    },
    "飞书": {
        "Windows": ["Feishu.exe", "Lark.exe"],
        "Darwin": ["Feishu", "Lark"],
        "Linux": ["feishu", "lark"],
    },
    "Telegram": {
        "Windows": ["Telegram.exe"],
        "Darwin": ["Telegram"],
        "Linux": ["telegram-desktop", "telegram"],
    },
    "Discord": {
        "Windows": ["Discord.exe"],
        "Darwin": ["Discord"],
        "Linux": ["discord", "Discord"],
    },
    # 办公软件
    "记事本": {
        "Windows": ["notepad.exe"],
        "Darwin": ["TextEdit"],
        "Linux": ["gedit", "kate", "nano", "vim"],
    },
    "计算器": {
        "Windows": ["calc.exe", "calculator.exe"],
        "Darwin": ["Calculator"],
        "Linux": ["gnome-calculator", "kcalc", "galculator"],
    },
    "Word": {
        "Windows": ["WINWORD.EXE", "winword.exe"],
        "Darwin": ["Microsoft Word"],
        "Linux": ["libreoffice-writer", "writer"],
    },
    "Excel": {
        "Windows": ["EXCEL.EXE", "excel.exe"],
        "Darwin": ["Microsoft Excel"],
        "Linux": ["libreoffice-calc", "calc"],
    },
    "PowerPoint": {
        "Windows": ["POWERPNT.EXE", "powerpnt.exe"],
        "Darwin": ["Microsoft PowerPoint"],
        "Linux": ["libreoffice-impress", "impress"],
    },
    "WPS": {
        "Windows": ["wps.exe", "et.exe", "wpp.exe"],
        "Darwin": ["WPS Office"],
        "Linux": ["wps", "et", "wpp"],
    },
    # 浏览器
    "Chrome": {
        "Windows": ["chrome.exe"],
        "Darwin": ["Google Chrome"],
        "Linux": ["google-chrome", "chrome"],
    },
    "Firefox": {
        "Windows": ["firefox.exe"],
        "Darwin": ["Firefox"],
        "Linux": ["firefox"],
    },
    "Edge": {
        "Windows": ["msedge.exe"],
        "Darwin": ["Microsoft Edge"],
        "Linux": ["microsoft-edge"],
    },
    "Safari": {"Windows": ["Safari.exe"], "Darwin": ["Safari"], "Linux": []},
    # 开发工具
    "VS Code": {
        "Windows": ["Code.exe"],
        "Darwin": ["Visual Studio Code"],
        "Linux": ["code"],
    },
    "VSCode": {
        "Windows": ["Code.exe"],
        "Darwin": ["Visual Studio Code"],
        "Linux": ["code"],
    },
    "PyCharm": {
        "Windows": ["pycharm64.exe", "pycharm.exe"],
        "Darwin": ["PyCharm"],
        "Linux": ["pycharm"],
    },
    "IntelliJ IDEA": {
        "Windows": ["idea64.exe", "idea.exe"],
        "Darwin": ["IntelliJ IDEA"],
        "Linux": ["idea"],
    },
    # 媒体软件
    "网易云音乐": {
        "Windows": ["cloudmusic.exe"],
        "Darwin": ["NeteaseMusic"],
        "Linux": ["netease-cloud-music"],
    },
    "QQ音乐": {"Windows": ["QQMusic.exe"], "Darwin": ["QQMusic"], "Linux": ["qqmusic"]},
    "VLC": {"Windows": ["vlc.exe"], "Darwin": ["VLC"], "Linux": ["vlc"]},
    # 游戏平台
    "Steam": {"Windows": ["steam.exe"], "Darwin": ["Steam"], "Linux": ["steam"]},
    "Epic Games": {
        "Windows": ["EpicGamesLauncher.exe"],
        "Darwin": ["Epic Games Launcher"],
        "Linux": ["epic-games-launcher"],
    },
    # 系统工具
    "任务管理器": {
        "Windows": ["Taskmgr.exe"],
        "Darwin": ["Activity Monitor"],
        "Linux": ["gnome-system-monitor", "htop", "top"],
    },
    "命令提示符": {
        "Windows": ["cmd.exe"],
        "Darwin": ["Terminal"],
        "Linux": ["gnome-terminal", "konsole", "xterm"],
    },
    "PowerShell": {
        "Windows": ["powershell.exe", "pwsh.exe"],
        "Darwin": ["pwsh"],
        "Linux": ["pwsh"],
    },
    # 安全软件
    "360安全卫士": {"Windows": ["360Safe.exe", "360sd.exe"], "Darwin": [], "Linux": []},
    "腾讯电脑管家": {
        "Windows": ["QQPCMgr.exe", "QQPCRTP.exe"],
        "Darwin": [],
        "Linux": [],
    },
    # 下载工具
    "迅雷": {
        "Windows": ["Thunder.exe", "ThunderVIP.exe"],
        "Darwin": ["Thunder"],
        "Linux": [],
    },
    "百度网盘": {
        "Windows": ["BaiduNetdisk.exe"],
        "Darwin": ["BaiduNetdisk"],
        "Linux": ["baidunetdisk"],
    },
}


class AppMapper:
    """应用名称映射器"""

    def __init__(self):
        self._process_cache: Dict[str, Set[str]] = {}

    def get_process_names(self, app_name: str) -> List[str]:
        """
        根据应用名称获取所有平台的进程名列表（合并去重）

        Args:
            app_name: 友好的应用名称

        Returns:
            所有平台进程名的合并列表，如果应用不存在则返回空列表
        """
        if app_name not in APP_MAPPING:
            return []

        # 使用缓存提高性能
        if app_name in self._process_cache:
            return list(self._process_cache[app_name])

        # 合并所有平台的进程名
        all_processes = set()
        platform_mapping = APP_MAPPING[app_name]
        for platform_processes in platform_mapping.values():
            all_processes.update(platform_processes)

        # 缓存结果
        self._process_cache[app_name] = all_processes
        return list(all_processes)

    def expand_app_names(self, app_names: List[str]) -> List[str]:
        """
        将友好的应用名称列表扩展为实际的进程名列表

        Args:
            app_names: 友好的应用名称列表

        Returns:
            扩展后的进程名列表（去重）
        """
        expanded_names = set()

        for app_name in app_names:
            # 如果是友好名称，获取对应的进程名
            process_names = self.get_process_names(app_name)
            if process_names:
                expanded_names.update(process_names)
            else:
                # 如果不是友好名称，直接添加（可能是用户直接配置的进程名）
                expanded_names.add(app_name)

        return list(expanded_names)

    def get_supported_apps(self) -> List[str]:
        """
        获取支持的应用名称列表

        Returns:
            支持的友好应用名称列表
        """
        return list(APP_MAPPING.keys())

    def get_app_info(self, app_name: str) -> Dict[str, List[str]]:
        """
        获取应用在所有平台的进程名信息

        Args:
            app_name: 友好的应用名称

        Returns:
            包含所有平台进程名的字典
        """
        return APP_MAPPING.get(app_name, {})

    def is_supported_app(self, app_name: str) -> bool:
        """
        检查是否为支持的应用名称

        Args:
            app_name: 应用名称

        Returns:
            是否为支持的应用名称
        """
        return app_name in APP_MAPPING


# 全局应用映射器实例
app_mapper = AppMapper()


def get_process_names_for_app(app_name: str) -> List[str]:
    """
    便捷函数：获取应用对应的进程名列表

    Args:
        app_name: 友好的应用名称

    Returns:
        当前平台对应的进程名列表
    """
    return app_mapper.get_process_names(app_name)


def expand_blacklist_apps(app_names: List[str]) -> List[str]:
    """
    便捷函数：扩展黑名单应用列表

    Args:
        app_names: 友好的应用名称列表

    Returns:
        扩展后的进程名列表
    """
    return app_mapper.expand_app_names(app_names)


if __name__ == "__main__":
    # 测试代码
    print(f"当前平台: {platform.system()}")
    print(f"支持的应用数量: {len(APP_MAPPING)}")

    # 测试几个应用
    test_apps = ["微信", "QQ", "Chrome", "VS Code", "记事本"]

    for app in test_apps:
        processes = get_process_names_for_app(app)
        print(f"{app}: {processes}")

    # 测试扩展功能
    print("\n扩展测试:")
    expanded = expand_blacklist_apps(["微信", "Chrome", "unknown_app.exe"])
    print(f"扩展结果: {expanded}")
