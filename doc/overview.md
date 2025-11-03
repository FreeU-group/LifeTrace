# LifeTrace Chat页面整体架构说明

## 📋 一、架构概览

Chat页面采用 **RAG (检索增强生成)** 架构，将用户的自然语言查询转化为对历史截图数据的智能分析和回答。

```
用户输入 → 意图识别 → 查询解析 → 数据检索 → 上下文构建 → LLM生成 → 流式输出
```

---

## 🎨 二、前端层 (`chat.html`)

### 主要特点

- 响应式聊天界面，支持左右分栏布局
- 使用 `marked.js` 渲染 Markdown 格式的回复
- 支持流式输出（逐字显示LLM回复）
- 集成 `Chart.js` 用于数据可视化
- 支持主题切换（亮色/暗色模式）
- 包含截图ID引用的可点击链接

### 关键功能

- 消息历史记录显示
- 实时流式输出
- 查询建议展示
- 错误处理和重试机制

---

## 🚀 三、后端路由层 (`server.py`)

### 主要路由端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/chat` | GET | 渲染聊天页面 |
| `/api/chat` | POST | 普通聊天接口（非流式） |
| `/api/chat/stream` | POST | 流式聊天接口（推荐使用） |
| `/api/chat/new` | POST | 创建新对话会话 |
| `/api/chat/session/{id}` | DELETE | 清除指定会话 |
| `/api/chat/history` | GET | 获取聊天历史 |
| `/api/chat/suggestions` | GET | 获取查询建议 |
| `/api/chat/query-types` | GET | 获取支持的查询类型 |
| `/api/rag/health` | GET | RAG服务健康检查 |

### 会话管理

- 内存中的会话存储（`chat_sessions` 字典）
- 每个会话维护独立的上下文历史
- 自动限制上下文长度（最多50条消息）

---

## 🧠 四、核心服务层

### 1. RAG服务 (`rag_service.py`)

**职责：** 整合完整的RAG流水线

#### 核心方法

```python
# 非流式处理
async def process_query(user_query: str) -> Dict[str, Any]

# 流式处理（推荐）
async def process_query_stream(user_query: str) -> Dict[str, Any]

# 获取查询建议
def get_query_suggestions(partial_query: str) -> List[str]
```

#### 处理流程

1. **意图识别** - 判断是否需要查询数据库
2. **查询解析** - 提取查询条件
3. **数据检索** - 从数据库获取相关数据
4. **统计分析** - 如果是统计类查询，生成统计信息
5. **上下文构建** - 整理数据为LLM可理解的格式
6. **LLM生成** - 调用LLM生成回复

---

### 2. LLM客户端 (`llm_client.py`)

**职责：** 与AI模型进行交互

#### 当前配置

- 模型：`qwen3-max` (通义千问)
- API地址：阿里云 DashScope

#### 核心功能

```python
# 意图分类（判断是否需要查询数据库）
def classify_intent(user_query: str) -> Dict[str, Any]

# 查询解析（提取时间、应用、关键词）
def parse_query(user_query: str) -> Dict[str, Any]

# 生成总结
def generate_summary(query: str, context_data: List) -> str

# 流式聊天
def stream_chat(messages: List, temperature: float) -> Generator
```

#### 意图类型

- `database_query` - 需要查询数据库（如搜索、统计）
- `general_chat` - 一般对话（如问候、闲聊）
- `system_help` - 系统帮助请求

---

### 3. 查询解析器 (`query_parser.py`)

**职责：** 将自然语言转换为结构化查询条件

#### 输出数据结构：QueryConditions

```python
@dataclass
class QueryConditions:
    start_date: Optional[datetime]    # 开始时间
    end_date: Optional[datetime]      # 结束时间
    app_names: Optional[List[str]]    # 应用名称列表
    keywords: Optional[List[str]]     # 搜索关键词
    limit: int = 1000                 # 结果数量限制
```

#### 解析策略

- 优先使用LLM解析（智能准确）
- 备用规则解析（LLM不可用时）
- 应用名称标准化映射

---

### 4. 检索服务 (`retrieval_service.py`)

**职责：** 从数据库检索相关数据

#### 核心方法

```python
# 根据条件检索
def search_by_conditions(conditions: QueryConditions) -> List[Dict]

# 获取统计信息
def get_statistics(conditions: QueryConditions) -> Dict

# 相关性评分
def _calculate_relevance(screenshot, ocr_text, conditions) -> float
```

#### 查询逻辑

- 联合查询 `Screenshot` 和 `OCRResult` 表
- 支持时间范围、应用名称、关键词过滤
- 按时间倒序排列
- 计算相关性评分（关键词匹配度）

---

### 5. 上下文构建器 (`context_builder.py`)

**职责：** 将检索数据整理为LLM可理解的格式

#### 核心方法

```python
# 构建搜索上下文
def build_search_context(query: str, data: List) -> str

# 构建统计上下文
def build_statistics_context(query: str, data: List, stats: Dict) -> str

# 构建总结上下文
def build_summary_context(query: str, data: List) -> str
```

#### 上下文特点

- 强制要求标注截图ID来源 `[截图ID: xxx]`
- 按应用分组展示
- 自动截断过长文本
- 包含时间戳、应用名、窗口标题、OCR文本

---

## 🔄 五、完整数据流

```
┌─────────────┐
│ 用户输入查询 │
└──────┬──────┘
       │
       ↓
┌──────────────────┐
│ 1. 意图识别      │ ← LLMClient.classify_intent()
│   - 数据库查询？  │
│   - 一般对话？    │
└──────┬───────────┘
       │
       ↓
┌──────────────────┐
│ 2. 查询解析      │ ← QueryParser.parse_query()
│   - 时间范围     │
│   - 应用名称     │
│   - 关键词       │
└──────┬───────────┘
       │
       ↓
┌──────────────────┐
│ 3. 数据检索      │ ← RetrievalService.search_by_conditions()
│   - SQL查询      │
│   - 相关性评分   │
└──────┬───────────┘
       │
       ↓
┌──────────────────┐
│ 4. 上下文构建    │ ← ContextBuilder.build_context()
│   - 格式化数据   │
│   - 添加截图ID   │
└──────┬───────────┘
       │
       ↓
┌──────────────────┐
│ 5. LLM生成       │ ← LLMClient.stream_chat()
│   - 流式输出     │
│   - Token记录    │
└──────┬───────────┘
       │
       ↓
┌──────────────────┐
│ 6. 返回给用户    │
│   - Markdown格式 │
│   - 截图ID引用   │
└──────────────────┘
```

---

## 🎯 六、关键设计特点

1. **流式输出优先** - 提升用户体验，实时查看生成过程
2. **意图识别优化** - 避免不必要的数据库查询
3. **截图ID溯源** - 所有信息都标注来源，保证可追溯性
4. **多级备用方案** - LLM不可用时使用规则方案
5. **会话管理** - 支持多轮对话上下文
6. **Token使用记录** - 完整记录API调用消耗

---

## 📊 七、支持的查询类型

| 类型 | 示例 | 特点 |
|------|------|------|
| **搜索** | "查找包含'会议'的记录" | 关键词匹配 |
| **统计** | "统计本周各应用使用情况" | 聚合分析 |
| **总结** | "总结今天的微信聊天" | 内容概括 |
| **对话** | "你好" | 不查询数据库 |

---

## ✨ 核心优势

- ✅ **智能理解** - LLM驱动的自然语言理解
- ✅ **准确检索** - 结构化数据库查询
- ✅ **上下文增强** - RAG提供可靠的数据支撑
- ✅ **流式体验** - 实时反馈，降低等待感
- ✅ **可追溯性** - 所有信息都有截图ID来源

---

## 📝 技术栈

- **前端**: HTML5, CSS3, JavaScript, marked.js, Chart.js
- **后端**: FastAPI, Python 3.8+
- **数据库**: SQLite (SQLAlchemy ORM)
- **AI模型**: 阿里云通义千问 (qwen3-max)
- **架构模式**: RAG (Retrieval-Augmented Generation)

---

## 🔧 配置说明

### LLM配置

LLM客户端配置位于 `lifetrace_backend/llm_client.py`:

```python
# 通义千问配置
api_key = "sk-ef4b56e3bc9c4693b596415dd364af56"
base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
model = "qwen3-max"
```

### 会话配置

服务器会话管理位于 `lifetrace_backend/server.py`:

```python
# 会话上下文最大长度
max_context_length = 50

# 会话存储（内存）
chat_sessions = defaultdict(dict)
```

---

## 🚦 使用流程示例

### 1. 用户发起查询

```
用户输入: "总结今天的微信聊天记录"
```

### 2. 意图识别

```json
{
  "intent_type": "database_query",
  "needs_database": true
}
```

### 3. 查询解析

```json
{
  "start_date": "2025-10-10 00:00:00",
  "end_date": "2025-10-10 23:59:59",
  "app_names": ["WeChat", "微信"],
  "keywords": null,
  "query_type": "summary"
}
```

### 4. 数据检索

从数据库检索到15条相关截图记录。

### 5. 上下文构建

```
找到 15 条相关记录:

=== WeChat (15 条记录) ===
1. [WeChat] 2025-10-10 09:30 [截图ID: 12345]
   内容: 早上好！今天的会议安排...
2. [WeChat] 2025-10-10 14:20 [截图ID: 12346]
   内容: 项目进度更新...
...
```

### 6. LLM生成回复

```
根据您今天的微信聊天记录，主要内容包括：

1. 早上的问候和会议安排讨论 [截图ID: 12345]
2. 下午的项目进度汇报 [截图ID: 12346]
3. 晚上的工作总结交流 [截图ID: 12350]

今天您在微信上主要进行了工作相关的沟通...
```

---

## 📚 相关文档

- [OCR优化说明](./OCR_优化说明.md)
- [向量数据库使用](./vector_db_usage.md)
- [多模态搜索指南](./multimodal_search_guide.md)
- [前端集成说明](./前端集成说明.md)

---

*最后更新: 2025年10月*
