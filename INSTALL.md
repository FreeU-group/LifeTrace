# LifeTrace 安装指南

## 快速开始

根据你的操作系统选择对应的安装命令：

### Windows

```bash
# 1. 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate

# 2. 安装依赖
# 完整版
pip install -r requirements/requirements_windows.txt

# 或者只安装 Recorder 模块
pip install -r requirements_recorder_windows.txt
```

### macOS

```bash
# 1. 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate

# 2. 安装依赖
# 完整版
pip install -r requirements/requirements_macos.txt

# 或者只安装 Recorder 模块
pip install -r requirements_recorder_macos.txt
```

### Linux

```bash
# 1. 确保安装了 X11 工具
sudo apt-get install x11-utils  # Debian/Ubuntu
# 或
sudo yum install xorg-x11-utils  # RHEL/CentOS

# 2. 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate

# 3. 安装依赖
# 完整版
pip install -r requirements/requirements.txt

# 或者只安装 Recorder 模块
pip install -r requirements_recorder_linux.txt
```

## 依赖文件说明

### Recorder 模块（轻量级）

适用于只需要屏幕录制和应用跟踪功能的场景。

- `requirements_recorder_windows.txt` - Windows 版本
- `requirements_recorder_macos.txt` - macOS 版本
- `requirements_recorder_linux.txt` - Linux 版本

### 完整版

包含所有功能：OCR、向量数据库、AI 摘要等。

- `requirements/requirements_windows.txt` - Windows 完整依赖
- `requirements/requirements_macos.txt` - macOS 完整依赖
- `requirements/requirements.txt` - 通用依赖（Linux）

## 平台特定依赖

### Windows
- **pywin32** - 用于获取窗口信息和进程信息

### macOS
- **pyobjc-framework-Cocoa** - Cocoa 框架支持
- **pyobjc-framework-Quartz** - Quartz 框架支持（窗口管理）

### Linux
- **x11-utils** - 系统包，非 Python 包
- 使用 `xprop` 命令获取窗口信息

## 验证安装

安装完成后，可以运行以下命令验证：

```bash
python -c "from lifetrace_backend.utils import get_active_window_info; import platform; print(f'系统: {platform.system()}'); app, title = get_active_window_info(); print(f'当前应用: {app}'); print(f'窗口标题: {title}')"
```

如果看到当前应用名称和窗口标题，说明安装成功！

## macOS 权限设置

macOS 用户可能需要授予应用"辅助功能"权限：

1. 打开 **系统偏好设置** → **安全性与隐私** → **隐私** → **辅助功能**
2. 点击左下角锁图标解锁
3. 添加你的终端或 Python IDE（如 VS Code、PyCharm 等）到允许列表
4. 重启应用

## 常见问题

### Windows: 提示 "无法找到 pywin32"
```bash
pip install pywin32
```

### macOS: 提示 "No module named 'AppKit'"
```bash
pip install pyobjc-framework-Cocoa pyobjc-framework-Quartz
```

### Linux: 提示 "xprop: command not found"
```bash
sudo apt-get install x11-utils
```

### 所有平台: pip 安装速度慢
使用国内镜像源：
```bash
pip install -r requirements_xxx.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 更多信息

详细的跨平台支持说明请参考：[doc/cross_platform_support.md](doc/cross_platform_support.md)
