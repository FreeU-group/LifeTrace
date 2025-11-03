# LifeTrace Web 服务内存优化指南

## 内存占用分析

### 主要内存占用来源

#### 1. 深度学习模型（最大内存消耗）

**后端加载的模型**：

```python
# lifetrace_backend/server.py (第 304-310 行)
ocr_processor = SimpleOCRProcessor()  # OCR 模型
vector_service = create_vector_service(config, db_manager)  # 文本嵌入模型
multimodal_vector_service = create_multimodal_vector_service(config, db_manager)  # 多模态模型
```

**模型内存占用估算**：

| 模型 | 说明 | 预估内存 | 配置项 |
|------|------|---------|--------|
| **RapidOCR** | OCR 识别模型 | ~200-300MB | `ocr.enabled` |
| **SentenceTransformer** | 文本嵌入模型<br/>`shibing624/text2vec-base-chinese` | ~400-600MB | `vector_db.enabled`<br/>`vector_db.embedding_model` |
| **CrossEncoder** | 文本重排序模型<br/>`BAAI/bge-reranker-base` | ~200-400MB | `vector_db.enabled`<br/>`vector_db.rerank_model` |
| **CLIP 模型** | 多模态嵌入<br/>`openai/clip-vit-base-patch32` | ~600-800MB | `multimodal.enabled` |
| **Qwen/Claude API** | RAG 服务（仅 API 调用，无本地模型） | ~50-100MB | - |

**总计**：如果所有功能启用，可能占用 **1.5GB - 2.5GB** 内存！

#### 2. 图像加载（前端 vs 后端）

**前端图像加载**：
```tsx
// front/components/DetailPanel.tsx
<ImageWithFallback
  src={`http://localhost:8840/api/screenshots/${id}/image`}
  alt="截图"
/>
```

- ✅ **不占用后端内存**：前端通过 HTTP 请求获取图像
- ❌ **占用浏览器内存**：如果一次性加载大量高分辨率截图
- 问题：没有缩略图机制，每次都加载原图

**后端图像处理**：
```python
# lifetrace_backend/server.py
@app.get("/api/screenshots/{screenshot_id}/image")
async def get_screenshot_image(screenshot_id: int):
    # 每次请求时读取文件并返回
    return FileResponse(screenshot['file_path'])
```

- ✅ 直接返回文件，不缓存在内存
- ❌ 但多模态向量服务会加载图像进行嵌入

#### 3. 其他内存占用

- **FastAPI 服务**：~50-100MB
- **SQLAlchemy 连接池**：~50-100MB
- **Python 运行时**：~50-100MB

---

## 优化方案

### 方案 1：禁用向量数据库（推荐 - 已配置）

**当前配置状态**：
```yaml
# config/config.yaml
vector_db:
  enabled: false  # ✅ 已禁用
```

**节省内存**：~600-1000MB

**影响**：
- ❌ 无法使用语义搜索功能
- ✅ 仍可使用关键词搜索
- ✅ 其他功能正常

### 方案 2：禁用多模态功能（强烈推荐）

**修改配置**：
```yaml
# config/config.yaml 或 config/default_config.yaml
multimodal:
  enabled: false  # 禁用多模态
```

**节省内存**：~600-800MB

**影响**：
- ❌ 无法使用图像+文本联合搜索
- ✅ 文本搜索和其他功能正常

### 方案 3：延迟加载模型

**实现思路**：
```python
# lifetrace_backend/server.py
class LazyVectorService:
    def __init__(self):
        self._service = None

    def get_service(self):
        if self._service is None:
            # 仅在第一次使用时加载
            self._service = create_vector_service(config, db_manager)
        return self._service

vector_service = LazyVectorService()
```

**优点**：
- 启动时不占用内存
- 仅在使用时加载

**缺点**：
- 首次使用时有延迟
- 代码改动较大

### 方案 4：添加图像缩略图功能（推荐）

**问题**：前端每次都加载原始分辨率截图（可能 1920x1080 或更高）

**解决方案**：生成缩略图

```python
# lifetrace_backend/server.py
from PIL import Image
import io

@app.get("/api/screenshots/{screenshot_id}/thumbnail")
async def get_screenshot_thumbnail(
    screenshot_id: int,
    max_width: int = 400,
    max_height: int = 300
):
    """返回缩略图"""
    screenshot = db_manager.get_screenshot_by_id(screenshot_id)
    if not screenshot:
        raise HTTPException(status_code=404)

    # 打开图像
    img = Image.open(screenshot['file_path'])

    # 生成缩略图
    img.thumbnail((max_width, max_height), Image.LANCZOS)

    # 转换为 bytes
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG', quality=85)
    img_byte_arr.seek(0)

    return StreamingResponse(img_byte_arr, media_type="image/jpeg")
```

**前端使用**：
```tsx
// 列表视图使用缩略图
<img src={`/api/screenshots/${id}/thumbnail`} />

// 详细视图使用原图
<img src={`/api/screenshots/${id}/image`} />
```

**节省内存**：
- 后端：不直接节省（PIL 临时占用）
- 前端：大幅减少浏览器内存（缩小 10-20 倍）

### 方案 5：使用轻量级模型

**文本嵌入模型替换**：
```yaml
vector_db:
  # 原模型：~500MB
  # embedding_model: shibing624/text2vec-base-chinese

  # 轻量级模型：~150MB
  embedding_model: sentence-transformers/all-MiniLM-L6-v2
```

**节省内存**：~300-400MB

**权衡**：
- ❌ 中文效果可能略差
- ✅ 英文效果依然良好
- ✅ 速度更快

### 方案 6：使用 CPU 而非 GPU

**当前配置**：
```yaml
ocr:
  use_gpu: false  # ✅ 已配置
```

如果使用 GPU：
- ❌ CUDA 库会额外占用 1-2GB 内存
- ✅ 推理速度更快

---

## 推荐配置（低内存模式）

```yaml
# config/config.yaml
ocr:
  enabled: true
  use_gpu: false  # CPU 模式

vector_db:
  enabled: false  # 禁用向量搜索

multimodal:
  enabled: false  # 禁用多模态

# 其他功能正常启用
record:
  enabled: true
heartbeat:
  enabled: true
```

**预期内存占用**：~400-600MB

**保留功能**：
- ✅ 截图录制
- ✅ OCR 文字识别
- ✅ 关键词搜索
- ✅ 事件时间线
- ✅ AI 对话（使用 API）
- ❌ 语义搜索
- ❌ 图像搜索

---

## 内存监控

### 查看当前内存占用

**Windows PowerShell**：
```powershell
Get-Process | Where-Object {$_.ProcessName -like "*python*"} |
Select-Object ProcessName, @{Name="Memory(MB)";Expression={[math]::Round($_.WS/1MB,2)}}
```

**Linux/macOS**：
```bash
ps aux | grep python | awk '{print $11, $6/1024 "MB"}'
```

### Python 内存分析

```python
# 添加到 server.py
import psutil
import os

@app.get("/api/system/memory")
async def get_memory_info():
    """获取系统内存信息"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()

    return {
        "rss_mb": round(memory_info.rss / 1024 / 1024, 2),  # 物理内存
        "vms_mb": round(memory_info.vms / 1024 / 1024, 2),  # 虚拟内存
        "percent": process.memory_percent()
    }
```

---

## 常见问题

### Q1: 为什么启动时内存占用这么高？

**A**: 深度学习模型在启动时一次性加载到内存：
- OCR 模型：~200-300MB
- 嵌入模型：~400-600MB
- 多模态模型：~600-800MB

**解决**：禁用不需要的功能（见方案 1-2）

### Q2: 前端加载图片很慢怎么办？

**A**: 实现缩略图功能（见方案 4）

### Q3: 能否使用云端 API 替代本地模型？

**A**: 可以，但需要网络请求：
- OCR：可使用百度 OCR、腾讯 OCR 等 API
- 嵌入：可使用 OpenAI Embeddings API
- 成本：每月可能产生费用

### Q4: 内存泄漏怎么办？

**A**: 检查并重启服务：
```bash
# 重启 LifeTrace Server
taskkill /F /IM LifeTrace_Server.exe
start LifeTrace_Server.exe
```

---

## 总结

**立即可做的优化**：
1. ✅ 确认 `vector_db.enabled: false`（已完成）
2. ✅ 添加 `multimodal.enabled: false`（强烈推荐）
3. ✅ 实现缩略图功能（优化前端体验）

**预期效果**：
- 内存从 1.5-2.5GB 降至 400-600MB
- 减少 **60-75%** 内存占用
- 保留核心功能

**长期优化**：
- 延迟加载模型
- 使用轻量级模型
- 添加内存监控接口
