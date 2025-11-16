# 自动关联优化：避免重复处理

## 问题背景

在之前的实现中，`task_context_mapper` 服务存在一个严重的 token 浪费问题：

**原逻辑：** 只有成功关联到任务的 event 才会更新 `task_id` 字段，未成功关联的 event（如无法确定项目、置信度不够等）会被反复处理，导致：

- **重复调用 LLM**：相同的 event 每次运行都会调用 2 次 LLM（确定项目 + 关联任务）
- **高 token 消耗**：每个 event 平均消耗 ~3000 tokens，如果有 300+ 个无法关联的 events，会持续浪费 token
- **无意义的计算**：即使判断过"无法关联"，下次还会再判断一遍

## 解决方案

### 核心思想

**无论自动关联成功与否，只要执行过一次就打上标记，不再重复处理。**

### 实现细节

#### 1. 数据库模型变更

在 `Event` 模型中添加新字段：

```python
auto_association_attempted = Column(Boolean, default=False)  # 是否已尝试过自动关联
```

#### 2. 数据库迁移

执行迁移脚本 `migrate_add_auto_association_attempted.py`：

```bash
python lifetrace/scripts/migrate_add_auto_association_attempted.py
```

迁移内容：
- 添加 `auto_association_attempted` 字段
- 将所有已关联任务的 events 标记为已尝试（`auto_association_attempted = 1`）

#### 3. 查询逻辑更新

`list_contexts()` 和 `count_contexts()` 方法新增参数：

```python
def list_contexts(
    self,
    associated: bool | None = None,
    task_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
    mapping_attempted: bool | None = None,  # 新增
) -> list[dict[str, Any]]:
```

- `mapping_attempted=False`: 获取未尝试过自动关联的 events
- `mapping_attempted=True`: 获取已尝试过自动关联的 events
- `mapping_attempted=None`: 不过滤（全部）

#### 4. 处理逻辑优化

`task_context_mapper.py` 的关键修改：

```python
def _get_unassociated_contexts(self, limit: int = 10):
    # 改为使用 mapping_attempted=False，而不是 associated=False
    contexts = self.db_manager.list_contexts(
        mapping_attempted=False,
        limit=limit,
        offset=0
    )
    return contexts

def _process_single_context(self, context: dict[str, Any]):
    context_id = context["id"]
    try:
        # ... 处理逻辑 ...
    finally:
        # ⚠️ 重要：无论成功与否，都标记为已尝试
        self.db_manager.mark_context_mapping_attempted(context_id)
```

#### 5. 新增数据库方法

```python
def mark_context_mapping_attempted(self, context_id: int) -> bool:
    """标记上下文已尝试过自动关联

    无论自动关联成功与否，都应该调用此方法标记，避免重复处理浪费 token
    """
    event.auto_association_attempted = True
    session.flush()
```

## 优化效果

### 数据统计（当前状态）

```
总 events 数: 583
├─ 已尝试自动关联: 260
└─ 未尝试自动关联: 323
```

### Token 消耗对比

**优化前：**
- 每次运行都会处理所有"未关联到任务"的 events
- 如果有 300 个无法关联的 events，每次运行都会：
  - 调用 LLM 次数：300 × 2 = 600 次
  - 预计消耗：~1,800,000 tokens
  - 每天运行 24 次（每小时 1 次）：约 ¥1.2/天

**优化后：**
- 每个 event 只处理一次
- 323 个未尝试的 events，全部处理完：
  - 调用 LLM 次数：323 × 2 = 646 次
  - 预计消耗：~1,900,000 tokens
  - 一次性成本：约 ¥1.5
  - 之后不再产生额外消耗 ✅

**节省：避免了每天重复处理的 ¥1.2 成本！**

## 适用场景

这个优化适用于以下情况：

1. ✅ **无法确定项目归属**：OCR 文本不足，无法判断属于哪个项目
2. ✅ **没有进行中的任务**：项目存在但没有 `in_progress` 状态的任务
3. ✅ **置信度不够**：LLM 判断的置信度低于阈值（默认 0.7）
4. ✅ **LLM 调用失败**：网络问题、API 限流等临时性错误

## 注意事项

### 如果需要重新尝试关联

如果后续添加了新项目或新任务，想要让某些 events 重新尝试自动关联：

```sql
-- 重置所有未关联的 events
UPDATE events
SET auto_association_attempted = 0
WHERE task_id IS NULL;

-- 或重置特定 event
UPDATE events
SET auto_association_attempted = 0
WHERE id = <event_id>;
```

### 兼容性

- ✅ 向后兼容：旧数据会在迁移时自动处理
- ✅ API 兼容：`list_contexts()` 的原有参数保持不变，新参数为可选
- ✅ 不影响手动关联：用户仍可通过 UI 手动关联 events 到任务

## 相关文件

- `lifetrace/storage/models.py`: Event 模型定义
- `lifetrace/storage/database.py`: 数据库操作方法
- `lifetrace/jobs/task_context_mapper.py`: 自动关联服务
- `lifetrace/scripts/migrate_add_auto_association_attempted.py`: 数据库迁移脚本

## 总结

这次优化从根本上解决了重复处理的问题，**将持续性的 token 消耗转变为一次性成本**，显著提升了系统的经济性和效率。

---

**更新时间：** 2025-11-14  
**影响版本：** v0.2.0+
