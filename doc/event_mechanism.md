# LifeTrace 事件机制说明

## 概述

**事件（Event）** 是 LifeTrace 中的核心概念，用于将属于同一个用户行为主题的多张截图整合为一个逻辑单元。事件机制基于前台应用的连续使用区间来自动聚合截图，使得用户可以更高效地回顾和检索历史记录。

## 设计理念

### 问题背景

在传统的截图管理中，截图是以时间序列独立存储的。但实际使用场景中，用户往往是在一个应用内持续工作一段时间（例如在 Chrome 浏览器中浏览网页、在 VS Code 中编写代码），这段时间内产生的多张截图实际上属于同一个**工作会话**或**行为主题**。

### 解决方案

LifeTrace 通过**事件机制**自动识别和聚合这些连续的截图：
- 当用户持续使用同一个前台应用时，所有截图归属于同一个事件
- 当用户切换到不同应用时，自动结束当前事件并创建新事件
- 每个事件记录了应用名称、窗口标题、开始时间、结束时间等信息

## 数据模型

### Event 表结构

```python
class Event(Base):
    """事件模型（按前台应用连续使用区间聚合截图）"""
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    app_name = Column(String(200))                    # 应用名称
    window_title = Column(String(500))                # 首个或最近的窗口标题
    start_time = Column(DateTime)                     # 事件开始时间
    end_time = Column(DateTime)                       # 事件结束时间（应用切换时填充）
    created_at = Column(DateTime)                     # 创建时间
```

**字段说明：**
- `app_name`: 前台应用程序名称（如 "chrome.exe", "code.exe"）
- `window_title`: 窗口标题，可能在事件过程中更新为最新值
- `start_time`: 事件开始时间（创建事件时的时间戳）
- `end_time`: 事件结束时间（切换应用或程序退出时填充，为空表示事件正在进行）
- `created_at`: 数据库记录创建时间

### Screenshot 与 Event 的关联

```python
class Screenshot(Base):
    """截图记录模型"""
    __tablename__ = 'screenshots'

    id = Column(Integer, primary_key=True)
    file_path = Column(String(500), nullable=False, unique=True)
    # ... 其他字段
    event_id = Column(Integer)                        # 关联的事件ID
    app_name = Column(String(200))                    # 前台应用名称
    window_title = Column(String(500))                # 窗口标题
    created_at = Column(DateTime)                     # 截图时间
```

每个截图通过 `event_id` 字段关联到所属的事件。

## 核心实现

### 1. 事件创建与维护逻辑

**核心方法：** `DatabaseManager.get_or_create_event()`

位置：`lifetrace_backend/storage.py`

```python
def get_or_create_event(self, app_name: Optional[str],
                       window_title: Optional[str],
                       timestamp: Optional[datetime] = None) -> Optional[int]:
    """按当前前台应用和窗口标题维护事件。

    事件切分规则：
    - 应用名相同 + 窗口标题相同 → 复用现有事件
    - 应用名不同 或 窗口标题不同 → 创建新事件
    """
```

**工作流程：**

1. **查找当前未结束的事件**
   ```python
   last_event = self._get_last_open_event(session)
   ```
   - 查询 `end_time` 为 `NULL` 的最新事件

2. **判断是否复用事件**
   ```python
   should_reuse = self._should_reuse_event(
       old_app=last_event.app_name,
       old_title=last_event.window_title,
       new_app=app_name,
       new_title=window_title
   )
   ```

   **判断逻辑（非常简单）：**
   - 应用名相同 + 窗口标题相同 → 复用事件
   - 应用名不同 或 窗口标题不同 → 创建新事件

   **应用场景示例：**
   - 🌐 **浏览器**：访问不同网页（标题不同）→ 创建新事件
   - 📝 **编辑器**：打开不同文件（标题不同）→ 创建新事件
   - 📁 **文件管理器**：切换目录（标题不同）→ 创建新事件
   - ✅ **持续编辑同一文件**（标题相同）→ 复用同一事件

3. **复用事件**
   ```python
   if should_reuse:
       # 应用名和标题都相同，继续使用同一事件
       return last_event.id
   ```

4. **创建新事件**
   ```python
   # 关闭旧事件
   last_event.end_time = now_ts
   closed_event_id = last_event.id

   # 创建新事件
   new_event = Event(
       app_name=app_name,
       window_title=window_title,
       start_time=now_ts
   )
   session.add(new_event)
   return new_event.id
   ```
   - 关闭旧事件并触发AI摘要生成
   - 创建新事件

### 2. 截图录制集成

**位置：** `lifetrace_backend/recorder.py`

在保存截图到数据库时，自动调用事件管理逻辑：

```python
def _save_to_database(self, file_path: str, file_hash: str, width: int, height: int,
                     screen_id: int, app_name: str, window_title: str, timestamp):
    # 获取或创建事件（基于当前前台应用）
    event_id = db_manager.get_or_create_event(
        app_name or "未知应用",
        window_title or "未知窗口",
        timestamp
    )

    # 保存截图并关联事件
    screenshot_id = db_manager.add_screenshot(
        file_path=file_path,
        file_hash=file_hash,
        width=width,
        height=height,
        screen_id=screen_id,
        app_name=app_name or "未知应用",
        window_title=window_title or "未知窗口",
        event_id=event_id  # 关联到事件
    )
```

**工作流程：**
1. 录制器每次截图时获取当前前台窗口信息（应用名称、窗口标题）
2. 调用 `get_or_create_event()` 获取当前事件ID
3. 将截图记录与事件ID关联存储

### 3. 主动关闭事件

**位置：** `lifetrace_backend/storage.py`

```python
def close_active_event(self, end_time: Optional[datetime] = None) -> bool:
    """主动结束当前事件（可在程序退出时调用）"""
    last_event = self._get_last_open_event(session)
    if last_event and last_event.end_time is None:
        last_event.end_time = end_time or datetime.now()
        return True
    return False
```

**使用场景：**
- 程序正常退出时，关闭最后一个未结束的事件
- **黑名单应用切换时**：当用户从白名单应用切换到黑名单应用时，自动关闭白名单应用的事件
- 确保数据完整性，避免遗留"永远未结束"的事件

### 4. 黑名单场景下的事件处理

**位置：** `lifetrace_backend/recorder.py`

当检测到黑名单应用时，系统会：

1. **跳过截图**：不保存任何截图文件（保护隐私）
2. **关闭上一个事件**：调用 `close_active_event()` 确保白名单应用的事件正确结束
3. **不创建新事件**：黑名单应用不会在事件表中留下记录

```python
if self._is_app_blacklisted(app_name, window_title):
    # 关闭上一个未结束的事件（如果存在）
    # 这样可以确保从白名单应用切换到黑名单应用时，白名单应用的事件能正确结束
    db_manager.close_active_event()
    return captured_files  # 跳过截图
```

**示例场景：**

| 时间 | 应用 | 操作 | Event 状态 |
|------|------|------|-----------|
| 10:00 | Chrome | 正常截图 | Event #1: start_time=10:00, end_time=NULL |
| 10:30 | 微信（黑名单）| 检测到黑名单，关闭 Event #1 | Event #1: end_time=10:30 ✅ |
| 10:30-11:00 | 微信（黑名单）| 持续跳过截图 | 无事件记录 |
| 11:00 | VS Code | 正常截图 | Event #2: start_time=11:00, end_time=NULL |

**注意事项：**
- Chrome 的使用时长被正确记录为 30 分钟（10:00-10:30）
- 微信的使用时间（10:30-11:00）不会被记录（隐私保护）
- 时间线上会出现 30 分钟的空白（从 10:30 到 11:00）
- 事件摘要会为 Chrome 事件自动生成（异步）

## API 接口

### 1. 获取事件列表

**端点：** `GET /api/events`

**参数：**
- `limit`: 返回数量限制（1-200，默认50）
- `offset`: 分页偏移量
- `start_date`: 开始日期过滤（ISO格式）
- `end_date`: 结束日期过滤（ISO格式）
- `app_name`: 应用名称模糊搜索

**响应：**
```json
[
  {
    "id": 123,
    "app_name": "chrome.exe",
    "window_title": "LifeTrace - 事件机制说明",
    "start_time": "2025-10-10T14:30:00",
    "end_time": "2025-10-10T15:45:00",
    "screenshot_count": 45,
    "first_screenshot_id": 5678
  }
]
```

**实现位置：** `lifetrace_backend/server.py:list_events()`

### 2. 获取事件详情

**端点：** `GET /api/events/{event_id}`

**响应：**
```json
{
  "id": 123,
  "app_name": "chrome.exe",
  "window_title": "LifeTrace - 事件机制说明",
  "start_time": "2025-10-10T14:30:00",
  "end_time": "2025-10-10T15:45:00",
  "screenshots": [
    {
      "id": 5678,
      "file_path": "data/screenshots/20251010_143001.png",
      "app_name": "chrome.exe",
      "window_title": "LifeTrace - 首页",
      "created_at": "2025-10-10T14:30:01",
      "width": 1920,
      "height": 1080
    }
    // ... 更多截图
  ]
}
```

**实现位置：** `lifetrace_backend/server.py:get_event_detail()`

### 3. 搜索事件

**端点：** `POST /api/event-search`

**请求体：**
```json
{
  "query": "编写代码",
  "limit": 20
}
```

**功能：**
- 基于OCR文本内容搜索相关事件
- 返回包含搜索关键词的事件摘要列表

**实现位置：** `lifetrace_backend/server.py:search_events()`

## 事件切分效果示例

### 浏览器场景（不同网页 = 不同事件）

```
时间   应用          窗口标题                      行为             事件ID
──────────────────────────────────────────────────────────────────────
10:00  chrome.exe   "GitHub - LifeTrace"         创建事件1         1
10:02  chrome.exe   "GitHub - LifeTrace"         复用事件1         1
                    (标题相同，继续浏览同一页面)
10:05  chrome.exe   "GitHub - Issues"            创建事件2         2
                    (标题不同，切换到Issues页面)
10:10  chrome.exe   "YouTube - Music"            创建事件3         3
                    (标题不同，访问YouTube)
10:12  chrome.exe   "YouTube - Music"            复用事件3         3
                    (标题相同，继续观看)
10:20  code.exe     "main.py - VSCode"           创建事件4         4
                    (应用切换)
```

**结果：**
- ✅ 事件1：浏览 GitHub - LifeTrace 页面
- ✅ 事件2：浏览 GitHub - Issues 页面
- ✅ 事件3：观看 YouTube 音乐
- ✅ 事件4：编写 main.py

### 编辑器场景（不同文件 = 不同事件）

```
时间   应用          窗口标题                      行为             事件ID
──────────────────────────────────────────────────────────────────────
11:00  code.exe     "main.py - VSCode"           创建事件1         1
11:03  code.exe     "main.py - VSCode"           复用事件1         1
                    (标题相同，继续编辑同一文件)
11:05  code.exe     "utils.py - VSCode"          创建事件2         2
                    (标题不同，切换到utils.py)
11:10  code.exe     "config.yaml - VSCode"       创建事件3         3
                    (标题不同，切换到config.yaml)
11:15  chrome.exe   "Stack Overflow"             创建事件4         4
                    (应用切换)
```

**结果：**
- ✅ 事件1：编辑 main.py
- ✅ 事件2：编辑 utils.py
- ✅ 事件3：编辑 config.yaml
- ✅ 事件4：查阅 Stack Overflow

## 使用场景

### 1. 工作回顾

用户可以按事件查看历史记录，而不是逐张浏览截图：
- "今天上午我在 VS Code 里编辑了哪些文件？"
- "昨天下午在 Chrome 浏览器里访问了哪些网页？"

得益于精确的事件切分，每个不同的页面/文件都会被记录为独立的事件：
- ✅ 每个网页 = 1个事件
- ✅ 每个编辑的文件 = 1个事件
- ✅ 持续编辑同一文件 = 同一事件（不会被过度切分）

### 2. 行为统计

基于事件可以统计：
- 每天在各个应用上的使用时长（`end_time - start_time`）
- 应用切换频率
- 工作效率分析（专注时长）

### 3. 智能检索

结合OCR文本内容和事件元数据：
- "搜索我在看 LifeTrace 文档时的截图"
- "查找我在编写 Python 代码时的所有记录"

### 4. 时间线展示

前端可以按事件组织时间线视图：
- 每个事件显示为一个卡片（应用图标、标题、时长、截图数量）
- 点击展开查看该事件内的所有截图
- 提供更清晰的视觉层次结构

## 数据查询示例

### 1. 查询某个事件的所有截图

```python
screenshots = db_manager.get_event_screenshots(event_id=123)
```

### 2. 按日期查询事件列表

```python
events = db_manager.list_events(
    start_date=datetime(2025, 10, 10, 0, 0, 0),
    end_date=datetime(2025, 10, 10, 23, 59, 59),
    limit=100
)
```

### 3. 查询某个应用的所有事件

```python
events = db_manager.list_events(
    app_name="chrome.exe",
    limit=50
)
```

### 4. 获取事件统计信息

```sql
-- 每个事件的截图数量
SELECT event_id, COUNT(*) as screenshot_count
FROM screenshots
WHERE event_id IS NOT NULL
GROUP BY event_id;

-- 每个应用的使用时长（秒）
SELECT app_name,
       SUM(JULIANDAY(end_time) - JULIANDAY(start_time)) * 86400 as total_seconds
FROM events
WHERE end_time IS NOT NULL
GROUP BY app_name;
```

## 优势与特点

### 1. 自动化

- **无需用户干预**：系统自动根据前台应用切换来创建和管理事件
- **实时更新**：每次截图时自动关联到正确的事件

### 2. 智能聚合

- **语义化分组**：按工作会话自动分组，而不是简单的时间切片
- **动态边界**：事件边界由实际的应用切换行为决定

### 3. 高效检索

- **减少检索粒度**：从"查找某张截图"变为"查找某个工作会话"
- **提升浏览效率**：一次性查看某个会话的所有相关截图

### 4. 数据分析

- **行为洞察**：分析应用使用模式、工作效率
- **时间统计**：精确计算各应用的使用时长
- **活动重建**：完整还原某个时间段的工作流程

## 技术细节

### 1. 并发处理

由于截图是周期性进行的，多个截图请求可能同时访问事件表：
- 使用数据库事务确保一致性
- `get_or_create_event()` 在单个事务中完成查询和更新

### 2. 窗口标题更新

在同一个应用内，窗口标题可能频繁变化（如浏览器切换标签页）：
- 当前实现：保留最新的窗口标题
- 未来扩展：可以记录窗口标题变化历史

### 3. 事件边界判断

**当前策略：** 仅基于应用名称判断
- 优点：简单、稳定
- 缺点：无法区分同一应用内的不同任务

**可选优化方向：**
- 结合窗口标题变化（需要更复杂的启发式规则）
- 加入时间间隔判断（超过N分钟自动分割事件）
- 使用机器学习识别任务边界

### 4. 旧数据兼容

`event_id` 字段允许为空，兼容旧版本数据：
- 旧截图的 `event_id` 为 `NULL`
- 新截图都会关联到事件
- 可以后续通过脚本迁移旧数据

## AI智能摘要功能

### 概述

从2025年10月开始，LifeTrace支持为每个事件自动生成AI智能摘要，包括简洁的标题和描述性摘要。这一功能利用大语言模型（LLM）分析事件中所有截图的OCR文本内容，自动提取关键信息并生成易于理解的摘要。

### 数据模型扩展

**Event表新增字段：**
- `ai_title`: 字符串字段，存储AI生成的事件标题（≤10字）
- `ai_summary`: 文本字段，存储AI生成的事件摘要（≤30字，支持markdown粗体）

### 核心功能

#### 1. 自动生成机制

**触发时机：** 当事件结束时（应用切换导致事件关闭）

**工作流程：**
1. 检测到事件关闭（`get_or_create_event`方法）
2. 在后台线程中异步触发摘要生成
3. 收集事件内所有截图的OCR文本
4. 调用LLM生成标题和摘要
5. 更新Event表的`ai_title`和`ai_summary`字段

**实现位置：**
- 服务类：`lifetrace_backend/event_summary_service.py`
- 集成点：`lifetrace_backend/storage.py` 的 `get_or_create_event()`方法

#### 2. LLM Prompt设计

```
你是一个活动摘要助手。根据用户在应用中的操作截图OCR文本，生成简洁的标题和摘要。

应用名称：{app_name}
窗口标题：{window_title}
时间范围：{start_time} 至 {end_time}

OCR文本内容：
{ocr_texts}

要求：
1. 生成一个标题（不超过10个字），概括用户在做什么
2. 生成一个摘要（不超过30个字），描述活动的关键内容，重点部分用**加粗**标记
3. 标题要简洁有力，摘要要突出核心信息
4. 如果OCR文本为空或无意义，基于应用名称和窗口标题生成

请以JSON格式返回：
{
  "title": "标题内容",
  "summary": "摘要内容，**重点部分**"
}
```

#### 3. 后备方案

当OCR数据不足或LLM不可用时，系统会使用后备方案：
- 基于应用名称和窗口标题生成简单描述
- 例如："Chrome使用" / "在**Chrome**中活动"

#### 4. 前端展示

**位置：** `lifetrace_backend/templates/chat.html` 的"忆往昔"面板

**展示逻辑：**
- 优先显示`ai_title`，如果为空则显示原始`window_title`
- 优先显示`ai_summary`，如果为空则显示默认描述
- Markdown格式的`**粗体**`自动转换为HTML的`<strong>`标签

**实现代码：**
```javascript
// 优先使用AI生成的标题和摘要
const displayTitle = event.ai_title || windowTitle;
let displaySummary = event.ai_summary;

if (!displaySummary) {
    displaySummary = `应用: ${appName}<br>正在进行的活动记录和截图捕捉`;
} else {
    // 将markdown格式的**粗体**转换为HTML
    displaySummary = displaySummary.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
}
```

### API接口扩展

#### 1. 事件列表和详情API更新

**GET /api/events** 和 **GET /api/events/{event_id}**

响应中新增字段：
```json
{
  "id": 123,
  "app_name": "chrome.exe",
  "window_title": "LifeTrace文档",
  "ai_title": "浏览文档",
  "ai_summary": "查看**LifeTrace**项目的事件机制说明文档",
  ...
}
```

#### 2. 手动触发API

**POST /api/events/{event_id}/generate-summary**

允许用户手动触发单个事件的摘要生成或重新生成：

**响应：**
```json
{
  "success": true,
  "event_id": 123,
  "ai_title": "浏览文档",
  "ai_summary": "查看**LifeTrace**项目的事件机制说明文档"
}
```

### 批量生成工具

**脚本：** `lifetrace_backend/event_summary_commands.py`

#### 查看统计信息
```bash
python -m lifetrace_backend.event_summary_commands stats
```

输出示例：
```
事件摘要统计
总事件数: 1250
已结束事件: 1180
已生成摘要: 850
需要生成摘要: 330
摘要覆盖率: 72.0%
```

#### 批量生成历史事件摘要
```bash
# 为所有未生成摘要的历史事件生成摘要
python -m lifetrace_backend.event_summary_commands generate-summaries

# 强制重新生成所有事件的摘要
python -m lifetrace_backend.event_summary_commands generate-summaries --force

# 限制处理数量（处理最近的100个事件）
python -m lifetrace_backend.event_summary_commands generate-summaries --limit 100
```

### 技术特点

#### 1. 异步处理
- 使用后台线程生成摘要，不阻塞截图保存流程
- 确保系统响应速度和用户体验

#### 2. 智能容错
- OCR数据不足时使用后备方案
- LLM调用失败时降级处理
- 不影响核心截图和事件管理功能

#### 3. 增量更新
- 只对新关闭的事件生成摘要
- 已有摘要的事件不重复处理（除非手动触发）
- 支持批量为历史数据补充摘要

#### 4. 模型灵活性
- 当前使用Qwen模型（阿里通义千问）
- 兼容OpenAI API格式
- 可轻松切换到其他大语言模型

### 使用效果

**传统展示：**
- 标题：`LifeTrace - Chrome`
- 描述：应用: chrome.exe / 正在进行的活动记录和截图捕捉

**AI摘要展示：**
- 标题：`浏览文档`
- 描述：查看**LifeTrace**项目的事件机制说明文档

AI生成的摘要更加简洁、易懂，突出关键信息，显著提升了用户浏览历史记录的效率。

## 未来扩展方向

### 1. 事件标签

允许用户为事件添加自定义标签：
- "工作"、"学习"、"娱乐"等
- 支持标签过滤和统计

### 2. 自动事件分类

基于窗口内容（OCR文本、应用类型）自动分类事件：
- 编程（VS Code + GitHub）
- 写作（Word + 浏览器）
- 研究（Chrome + PDF阅读器）

### 3. 跨应用事件

识别相关的跨应用任务流：
- "编写代码" = VS Code + Chrome（查文档）+ Terminal
- 通过时间关系和内容关联自动聚合

### 4. 智能时间间隔

动态调整事件分割逻辑：
- 短暂切换应用（<1分钟）不分割事件
- 长时间空闲后重新开始新事件
- 根据用户习惯学习最佳分割策略

## 总结

事件机制是 LifeTrace 的核心创新之一，它将离散的截图转化为有意义的工作会话单元。通过自动化的事件创建和管理，系统能够：

1. **提升用户体验**：按工作会话组织视图，更符合用户认知
2. **增强检索能力**：从截图级检索提升到会话级检索
3. **支持数据分析**：为行为统计和工作效率分析提供基础
4. **保持简单高效**：自动化运行，无需用户手动管理

这一机制为 LifeTrace 从"截图记录工具"向"个人工作流追踪系统"的演进奠定了重要基础。

---

**文档版本：** 1.1  
**最后更新：** 2025-10-11  
**维护者：** LifeTrace Team  
**更新内容：** 新增AI智能摘要功能说明
