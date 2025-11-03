# LifeTrace 跨平台支持说明

## 概述

LifeTrace 支持在 Windows、macOS 和 Linux 三个平台上运行，可以自动检测当前活动窗口的应用名称和窗口标题。

## 平台依赖

### Windows
```bash
pip install pywin32>=305
```

**所需模块：**
- `win32gui` - 获取前台窗口
- `win32process` - 获取窗口进程ID
- `psutil` - 获取进程信息（跨平台）

### macOS
```bash
pip install pyobjc-framework-Cocoa>=9.0
pip install pyobjc-framework-Quartz>=9.0
```

**所需模块：**
- `AppKit.NSWorkspace` - 获取活动应用
- `Quartz.CGWindowListCopyWindowInfo` - 获取窗口列表和标题

### Linux
**无需额外 Python 包**，使用系统自带的 `xprop` 工具

**系统要求：**
```bash
# 大多数 Linux 发行版默认已安装
sudo apt-get install x11-utils  # Debian/Ubuntu
sudo yum install xorg-x11-utils  # RHEL/CentOS
```

## 安装方法

### 方法一：使用平台特定的 requirements 文件（推荐）

根据你的操作系统，选择对应的依赖文件：

**Windows 用户：**
```bash
# Recorder 模块
pip install -r requirements_recorder_windows.txt

# 完整版（包含 OCR、向量数据库等）
pip install -r requirements/requirements_windows.txt
```

**macOS 用户：**
```bash
# Recorder 模块
pip install -r requirements_recorder_macos.txt

# 完整版（包含 OCR、向量数据库等）
pip install -r requirements/requirements_macos.txt
```

**Linux 用户：**
```bash
# Recorder 模块
pip install -r requirements_recorder_linux.txt

# 完整版（包含 OCR、向量数据库等）
pip install -r requirements/requirements.txt
# 注意：Linux 使用系统自带的 xprop，请确保已安装 x11-utils
```

### 方法二：手动安装平台特定依赖

如果你已经安装了通用依赖，只需要补充安装平台特定的包：

**Windows:**
```bash
pip install pywin32
```

**macOS:**
```bash
pip install pyobjc-framework-Cocoa pyobjc-framework-Quartz
```

**Linux:**
```bash
# 确保安装了 xprop
which xprop  # 检查是否已安装
sudo apt-get install x11-utils  # 如果未安装
```

## 实现原理

代码位置：`lifetrace_backend/utils.py`

```python
def get_active_window_info() -> Tuple[Optional[str], Optional[str]]:
    """获取当前活跃窗口信息"""
    system = platform.system()

    if system == "Windows":
        return _get_windows_active_window()
    elif system == "Darwin":  # macOS
        return _get_macos_active_window()
    elif system == "Linux":
        return _get_linux_active_window()
    else:
        return None, None
```

### Windows 实现
```python
import win32gui
import win32process
import psutil

hwnd = win32gui.GetForegroundWindow()
window_title = win32gui.GetWindowText(hwnd)
_, pid = win32process.GetWindowThreadProcessId(hwnd)
process = psutil.Process(pid)
app_name = process.name()
```

### macOS 实现
```python
from AppKit import NSWorkspace
from Quartz import CGWindowListCopyWindowInfo

workspace = NSWorkspace.sharedWorkspace()
active_app = workspace.activeApplication()
app_name = active_app.get('NSApplicationName', None)

window_list = CGWindowListCopyWindowInfo(
    kCGWindowListOptionOnScreenOnly,
    kCGNullWindowID
)
```

### Linux 实现
```python
import subprocess

# 获取活动窗口ID
result = subprocess.run(
    ['xprop', '-root', '_NET_ACTIVE_WINDOW'],
    capture_output=True, text=True
)

# 获取窗口标题和应用名
subprocess.run(['xprop', '-id', window_id, 'WM_NAME'], ...)
subprocess.run(['xprop', '-id', window_id, 'WM_CLASS'], ...)
```

## 功能特性

所有平台均支持：
- ✅ 获取当前活动应用名称
- ✅ 获取当前窗口标题
- ✅ 应用黑名单过滤
- ✅ 自动截图记录
- ✅ 事件跟踪

## 测试

你可以运行以下测试来验证跨平台功能：

```python
from lifetrace_backend.utils import get_active_window_info
import platform

print(f"当前系统: {platform.system()}")
app_name, window_title = get_active_window_info()
print(f"应用名称: {app_name}")
print(f"窗口标题: {window_title}")
```

## 常见问题

### Q: 在 macOS 上提示 "macOS依赖未安装"
A: 运行 `pip install pyobjc-framework-Cocoa pyobjc-framework-Quartz`

### Q: 在 Windows 上提示 "Windows依赖未安装"
A: 运行 `pip install pywin32`

### Q: 在 Linux 上无法获取窗口信息
A: 确保安装了 X11 工具：`sudo apt-get install x11-utils`

### Q: macOS 权限问题
A: macOS 可能需要授予应用"辅助功能"权限：
   - 打开"系统偏好设置" → "安全性与隐私" → "隐私" → "辅助功能"
   - 添加终端或你的 Python IDE 到允许列表

### Q: 在 Wayland (Linux) 上是否支持？
A: 当前实现基于 X11，Wayland 支持有限。建议在 X11 模式下运行。

## 开发建议

如果你需要为其他平台添加支持，可以在 `utils.py` 中添加新的函数：

```python
def _get_your_platform_active_window() -> Tuple[Optional[str], Optional[str]]:
    """获取你的平台活跃窗口信息"""
    try:
        # 你的实现
        return app_name, window_title
    except ImportError:
        logging.warning("平台依赖未安装")
    except Exception as e:
        logging.error(f"获取窗口信息失败: {e}")

    return None, None
```

然后在 `get_active_window_info()` 中添加判断逻辑。

## 更新日志

- 2024-XX-XX: 添加 macOS 平台依赖到 requirements 文件
- 2024-XX-XX: 完善跨平台支持文档
