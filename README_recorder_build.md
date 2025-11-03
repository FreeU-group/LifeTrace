# LifeTrace Recorder 独立可执行文件构建指南

## 概述

本指南将帮助您将 LifeTrace 的 recorder 模块打包成独立的 Windows 可执行文件。

## 文件说明

- `recorder_standalone.py` - 独立启动脚本
- `requirements_recorder.txt` - 最小依赖列表
- `build_recorder.spec` - PyInstaller 配置文件
- `build_recorder.bat` - 自动化构建脚本

## 构建步骤

### 方法一：使用自动化脚本（推荐）

1. 双击运行 `build_recorder.bat`
2. 脚本会自动完成所有构建步骤
3. 构建完成后，可执行文件位于 `dist/LifeTrace_Recorder.exe`

### 方法二：手动构建

1. **安装依赖**
   ```bash
   pip install -r requirements_recorder.txt
   ```

2. **清理旧文件**
   ```bash
   rmdir /s /q dist build
   ```

3. **构建可执行文件**
   ```bash
   pyinstaller build_recorder.spec
   ```

## 使用说明

构建完成后，您可以：

1. **直接运行**
   ```bash
   dist\LifeTrace_Recorder.exe
   ```

2. **带参数运行**
   ```bash
   dist\LifeTrace_Recorder.exe --interval 2 --screens all
   ```

3. **查看帮助**
   ```bash
   dist\LifeTrace_Recorder.exe --help
   ```

## 配置文件

可执行文件会使用以下配置文件（按优先级）：
1. 当前目录下的 `config.yaml`
2. 内置的默认配置

## 注意事项

1. **首次运行**：首次运行时会自动创建必要的目录和数据库文件
2. **权限要求**：需要屏幕截图权限
3. **防病毒软件**：某些防病毒软件可能会误报，需要添加信任
4. **依赖项**：可执行文件已包含所有必要依赖，无需额外安装

## 故障排除

### 构建失败
- 确保 Python 版本 >= 3.8
- 确保所有依赖都已正确安装
- 检查是否有权限问题

### 运行失败
- 检查是否有屏幕截图权限
- 确保配置文件格式正确
- 查看错误日志信息

### 文件大小过大
- 可以在 `build_recorder.spec` 中添加更多排除项
- 使用 UPX 压缩（已启用）

## 自定义配置

如需修改构建配置，请编辑 `build_recorder.spec` 文件：

- `excludes` - 排除不需要的模块
- `hiddenimports` - 添加隐式导入
- `datas` - 包含额外的数据文件
- `icon` - 设置可执行文件图标

## 技术细节

- **打包工具**：PyInstaller
- **打包模式**：单文件模式
- **压缩**：启用 UPX 压缩
- **控制台**：保留控制台窗口（便于调试）

## 版本信息

- 支持的操作系统：Windows 10/11
- Python 版本要求：>= 3.8
- 构建工具：PyInstaller >= 5.0.0
