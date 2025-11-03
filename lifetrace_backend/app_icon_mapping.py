#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用图标映射表
将应用名称映射到图标文件
"""

# 应用名称(小写) -> 图标文件名
# 支持 .exe 文件名、应用显示名、中文名等多种形式
APP_ICON_MAPPING = {
    # 浏览器
    "chrome.exe": "chrome.png",
    "chrome": "chrome.png",
    "google chrome": "chrome.png",
    "msedge.exe": "edge.png",
    "edge": "edge.png",
    "edge.exe": "edge.png",
    "microsoft edge": "edge.png",
    "firefox.exe": "firefox.png",
    "firefox": "firefox.png",
    "mozilla firefox": "firefox.png",
    # 开发工具
    "code.exe": "vscode.png",
    "code": "vscode.png",
    "vscode": "vscode.png",
    "visual studio code": "vscode.png",
    "pycharm64.exe": "pycharm.png",
    "pycharm.exe": "pycharm.png",
    "pycharm": "pycharm.png",
    "idea64.exe": "intellij.png",
    "intellij": "intellij.png",
    "intellij idea": "intellij.png",
    "webstorm64.exe": "webstorm.png",
    "webstorm.exe": "webstorm.png",
    "webstorm": "webstorm.png",
    "githubdesktop.exe": "github.png",
    "github desktop": "github.png",
    "github": "github.png",
    # 通讯工具
    "wechat.exe": "wechat.png",
    "weixin.exe": "wechat.png",
    "wechat": "wechat.png",
    "weixin": "wechat.png",
    "微信": "wechat.png",
    "qq.exe": "qq.png",
    "qq": "qq.png",
    "telegram.exe": "telegram.png",
    "telegram": "telegram.png",
    "discord.exe": "discord.png",
    "discord": "discord.png",
    # Office 套件
    "winword.exe": "word.png",
    "word": "word.png",
    "microsoft word": "word.png",
    "excel.exe": "excel.png",
    "excel": "excel.png",
    "microsoft excel": "excel.png",
    "powerpnt.exe": "powerpoint.png",
    "powerpoint.exe": "powerpoint.png",
    "powerpoint": "powerpoint.png",
    "microsoft powerpoint": "powerpoint.png",
    "wps.exe": "wps.png",
    "wps": "wps.png",
    "wpp.exe": "powerpoint.png",  # WPS演示
    "et.exe": "excel.png",  # WPS表格
    # 设计工具
    "photoshop.exe": "photoshop.png",
    "photoshop": "photoshop.png",
    "xmind.exe": "xmind.png",
    "xmind": "xmind.png",
    "snipaste.exe": "snipaste.png",
    "snipaste": "snipaste.png",
    # 媒体工具
    "spotify.exe": "spotify.png",
    "spotify": "spotify.png",
    "vlc.exe": "vlc.png",
    "vlc": "vlc.png",
    # 系统工具
    "explorer.exe": "explorer.png",
    "explorer": "explorer.png",
    "file explorer": "explorer.png",
    "文件资源管理器": "explorer.png",
    "notepad.exe": "notepad.png",
    "notepad": "notepad.png",
    "记事本": "notepad.png",
    "calc.exe": "calculator.png",
    "calculator.exe": "calculator.png",
    "calculator": "calculator.png",
    "计算器": "calculator.png",
}


def get_icon_filename(app_name):
    """
    根据应用名称获取图标文件名

    Args:
        app_name: 应用名称（支持exe文件名、显示名等）

    Returns:
        图标文件名，如果未找到返回None
    """
    if not app_name:
        return None

    # 转为小写进行匹配
    app_name_lower = app_name.lower().strip()

    # 精确匹配
    if app_name_lower in APP_ICON_MAPPING:
        return APP_ICON_MAPPING[app_name_lower]

    # 模糊匹配（部分包含）
    for key, icon_file in APP_ICON_MAPPING.items():
        if key in app_name_lower or app_name_lower in key:
            return icon_file

    return None


def get_all_supported_apps():
    """获取所有支持的应用列表"""
    return sorted(set(APP_ICON_MAPPING.values()))
