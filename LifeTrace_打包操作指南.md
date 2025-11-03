# LifeTrace 项目打包操作指南

## 项目概述

LifeTrace 是一个生活轨迹记录和分析系统，包含三个核心模块：
- **LifeTrace_Server**: Web服务器模块，提供API和Web界面
- **LifeTrace_Recorder**: 屏幕录制模块，负责截图和数据收集
- **LifeTrace_OCR**: OCR处理模块，负责图像文字识别

## 打包环境要求

### 系统环境
- Windows 10/11
- Python 3.8+
- Anaconda/Miniconda (推荐使用虚拟环境)

### 依赖工具
- PyInstaller (用于打包Python应用为可执行文件)
- 相关Python包依赖 (见各模块requirements文件)

## 打包配置文件说明

### 1. LifeTrace_OCR 打包配置 (`build_ocr.spec`)

**主要特点:**
- 入口文件: `ocr_standalone.py`
- 包含完整的RapidOCR运行时环境
- 解决了RapidOCR配置文件和模型文件依赖问题
- **性能优化**: 使用外部ONNX模型文件避免嵌入式解压缩开销

**关键配置 (性能优化版本):**
```python
datas=[
    ('config', 'config'),  # 项目配置文件
    ('models', 'models'),  # 外部ONNX模型文件（避免嵌入到exe中）
    # 包含RapidOCR的代码部分（不包含models目录）
    (r'C:/Users/25048/anaconda3/envs/sword/lib/site-packages/rapidocr_onnxruntime/*.py', 'rapidocr_onnxruntime'),
    (r'C:/Users/25048/anaconda3/envs/sword/lib/site-packages/rapidocr_onnxruntime/utils', 'rapidocr_onnxruntime/utils'),
    (r'C:/Users/25048/anaconda3/envs/sword/lib/site-packages/rapidocr_onnxruntime/ch_ppocr_det', 'rapidocr_onnxruntime/ch_ppocr_det'),
    (r'C:/Users/25048/anaconda3/envs/sword/lib/site-packages/rapidocr_onnxruntime/ch_ppocr_rec', 'rapidocr_onnxruntime/ch_ppocr_rec'),
    (r'C:/Users/25048/anaconda3/envs/sword/lib/site-packages/rapidocr_onnxruntime/ch_ppocr_cls', 'rapidocr_onnxruntime/ch_ppocr_cls'),
    (r'C:/Users/25048/anaconda3/envs/sword/lib/site-packages/rapidocr_onnxruntime/cal_rec_boxes', 'rapidocr_onnxruntime/cal_rec_boxes'),
    ('lifetrace_backend/*.py', 'lifetrace_backend'),  # 后端模块
]
```

**性能优化说明:**
1. **外部模型文件**: 将15.4MB的ONNX模型文件作为外部数据文件，避免嵌入到可执行文件中
2. **减少I/O开销**: 避免PyInstaller在运行时从临时目录解压缩模型文件的开销
3. **配置优化**: 在`rapidocr_config.yaml`中指定外部模型路径:
   ```yaml
   Models:
     det_model_path: "models/ch_PP-OCRv4_det_infer.onnx"
     rec_model_path: "models/ch_PP-OCRv4_rec_infer.onnx"
     cls_model_path: "models/ch_ppocr_mobile_v2.0_cls_infer.onnx"
   ```
4. **性能提升**: 启动时间从52秒优化到约17秒，提升约67%

**隐藏导入模块:**
- RapidOCR相关: `rapidocr_onnxruntime.*`
- 图像处理: `PIL`, `numpy`, `onnxruntime`
- 后端模块: `lifetrace_backend.*`

### 2. LifeTrace_Server 打包配置 (`build_server.spec`)

**主要特点:**
- 入口文件: `lifetrace_backend/server.py`
- 包含Web模板和静态文件
- 支持FastAPI和Jinja2模板引擎

**关键配置:**
```python
datas=[
    ('config/default_config.yaml', 'config'),  # 默认配置
    ('lifetrace_backend/*.py', 'lifetrace_backend'),  # 后端模块
    ('lifetrace_backend/templates', 'lifetrace_backend/templates'),  # Web模板
]
```

**隐藏导入模块:**
- Web框架: `fastapi`, `uvicorn`, `jinja2`
- 数据库: `sqlalchemy`, `pydantic`
- 后端服务: `lifetrace_backend.*`

### 3. LifeTrace_Recorder 打包配置 (`build_recorder.spec`)

**主要特点:**
- 入口文件: `recorder_standalone.py`
- 专注于屏幕截图和文件监控
- 轻量化配置，排除不必要的依赖

**关键配置:**
```python
datas=[
    ('config/default_config.yaml', 'config'),  # 配置文件
    ('lifetrace_backend/*.py', 'lifetrace_backend'),  # 后端模块
]
```

**隐藏导入模块:**
- 截图相关: `mss`, `PIL`, `imagehash`
- 系统监控: `psutil`, `watchdog`
- 数据处理: `numpy`, `scipy`

## 打包操作步骤

### 准备工作

1. **激活Python环境**
   ```bash
   conda activate sword  # 或你的环境名称
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements/requirements.txt
   pip install -r requirements/requirements_rapidocr.txt  # OCR模块需要
   pip install pyinstaller
   ```

3. **确保配置文件完整**
   - `config/config.yaml`
   - `config/default_config.yaml`
   - `config/rapidocr_config.yaml`

### 执行打包

#### 方法一: 使用PyInstaller命令

```bash
# 打包OCR模块
pyinstaller build_ocr.spec

# 打包Server模块
pyinstaller build_server.spec

# 打包Recorder模块
pyinstaller build_recorder.spec
```

#### 方法二: 使用批处理文件

```bash
# 如果存在对应的.bat文件
build_ocr.bat
build_server.bat
build_recorder.bat
```

### 打包结果

打包完成后，所有可执行文件将生成在 `dist/` 目录下：

```
dist/
├── LifeTrace_OCR.exe      (~304MB)
├── LifeTrace_Server.exe   (~293MB)
├── LifeTrace_Recorder.exe (~80MB)
├── config/                # 配置文件目录
└── data/                  # 数据目录
```

## 验证打包结果

### 1. 检查可执行文件

```bash
# 进入dist目录
cd dist

# 测试各模块帮助信息
.\LifeTrace_Server.exe --help
.\LifeTrace_Recorder.exe --help
.\LifeTrace_OCR.exe --help
```

### 2. 预期输出

**LifeTrace_Server.exe --help:**
```
usage: LifeTrace_Server.exe [-h] [--host HOST] [--port PORT] [--config CONFIG] [--debug]

LifeTrace Web Server

optional arguments:
  -h, --help       show this help message and exit
  --host HOST      服务器地址
  --port PORT      服务器端口
  --config CONFIG  配置文件路径
  --debug          启用调试模式
```

**LifeTrace_Recorder.exe --help:**
```
usage: LifeTrace_Recorder.exe [-h] [--config CONFIG] [--interval INTERVAL] [--screens SCREENS] [--debug]

LifeTrace Screen Recorder

optional arguments:
  -h, --help           show this help message and exit
  --config CONFIG      配置文件路径
  --interval INTERVAL  截图间隔（秒）
  --screens SCREENS    要截图的屏幕，用逗号分隔或使用"all"
  --debug              启用调试日志
```

**LifeTrace_OCR.exe:**
- 正常启动会显示 "查询到 0 条未处理的截图记录"
- 表示OCR服务正常运行，等待处理任务

## 常见问题及解决方案

### 1. RapidOCR初始化失败

**问题:** `RapidOCR` 初始化错误，找不到配置文件或模型文件

**解决方案:**
- 确保 `build_ocr.spec` 中包含完整的 `rapidocr_onnxruntime` 包
- 检查RapidOCR包路径是否正确
- 手动复制缺失的配置文件到 `dist/config/` 目录
- **性能优化版本**: 确保 `models/` 目录被正确复制到 `dist/` 目录

### 2. OCR性能优化问题

**问题:** 打包后OCR处理速度明显变慢，启动时间过长

**根本原因:**
- PyInstaller将ONNX模型文件嵌入到可执行文件中
- 运行时需要从临时目录解压缩模型文件，造成I/O开销

**优化步骤:**
1. **准备外部模型文件:**
   ```bash
   # 创建models目录
   mkdir models

   # 复制ONNX模型文件
   python -c "
   import rapidocr_onnxruntime
   import os, shutil
   pkg_path = rapidocr_onnxruntime.__path__[0]
   models_path = os.path.join(pkg_path, 'models')
   for f in os.listdir(models_path):
       if f.endswith('.onnx'):
           shutil.copy2(os.path.join(models_path, f), 'models/')
   "
   ```

2. **修改打包配置 (`build_ocr.spec`):**
   - 将完整的 `rapidocr_onnxruntime` 包替换为分离的代码和数据
   - 添加 `('models', 'models')` 到 `datas` 列表
   - 排除模型文件的嵌入打包

3. **更新配置文件 (`config/rapidocr_config.yaml`):**
   ```yaml
   Models:
     det_model_path: "models/ch_PP-OCRv4_det_infer.onnx"
     rec_model_path: "models/ch_PP-OCRv4_rec_infer.onnx"
     cls_model_path: "models/ch_ppocr_mobile_v2.0_cls_infer.onnx"
   ```

4. **修改OCR初始化代码:**
   - 在 `simple_ocr.py` 中添加外部模型路径支持
   - 直接传递模型文件路径给RapidOCR构造函数

5. **打包后手动操作:**
   ```bash
   # 打包完成后，确保复制models目录
   Copy-Item -Path "models" -Destination "dist" -Recurse -Force
   ```

**性能提升效果:**
- 启动时间: 从52秒优化到17秒 (提升67%)
- 内存使用: 减少模型文件解压缩的内存开销
- 磁盘I/O: 避免临时文件的频繁读写

### 3. 模板文件缺失

**问题:** Server模块启动时找不到HTML模板

**解决方案:**
- 确保 `build_server.spec` 中正确配置了templates目录
- 检查 `lifetrace_backend/templates` 目录是否存在

### 3. 依赖模块缺失

**问题:** 运行时提示某些模块无法导入

**解决方案:**
- 在对应的 `.spec` 文件的 `hiddenimports` 中添加缺失模块
- 重新执行打包命令

### 4. 配置文件路径问题

**问题:** 程序无法找到配置文件

**解决方案:**
- 确保 `config/` 目录被正确打包
- 检查程序中配置文件的相对路径设置
- 必要时手动复制配置文件到 `dist/config/`

## 打包优化建议

### 1. 减小文件体积
- 在 `.spec` 文件中使用 `excludes` 排除不必要的模块
- 避免打包开发工具和测试框架

### 2. 提高启动速度
- 使用 `--onefile` 选项创建单文件可执行程序（可选）
- 优化隐藏导入列表，只包含必要模块

### 3. 增强兼容性
- 测试在不同Windows版本上的运行情况
- 确保所有依赖的DLL文件被正确打包

## 部署说明

### 单机部署
1. 将整个 `dist/` 目录复制到目标机器
2. 确保目标机器有足够的磁盘空间和内存
3. 按需启动各个模块

### 分布式部署
- **LifeTrace_Server**: 部署在服务器上，提供Web服务
- **LifeTrace_Recorder**: 部署在需要监控的客户端机器
- **LifeTrace_OCR**: 可以与Server部署在同一台机器，或独立部署

## 维护和更新

### 代码更新后重新打包
1. 更新源代码
2. 检查依赖是否有变化
3. 更新对应的 `.spec` 文件（如有必要）
4. 重新执行打包命令
5. 测试新版本功能

### 配置文件更新
- 直接替换 `dist/config/` 目录下的配置文件
- 无需重新打包整个应用

---

**注意:** 本指南基于Windows环境下的打包操作，其他操作系统可能需要调整相应的路径和配置。
