# 任务摘要优化 - 基于 event_associations 表

## 背景

之前的任务摘要服务使用内存中的 `_summarized_contexts` 集合来跟踪哪些上下文已经被用于摘要，这种方式存在以下问题：

1. **数据不持久化**：服务重启后会丢失已摘要的标记
2. **无法跨实例共享**：如果有多个服务实例运行，标记状态不一致
3. **数据库结构变更**：event 和 task 的关系已经迁移到 `event_associations` 表

## 改进方案

在 `event_associations` 表中添加 `used_in_summary` 字段，用于持久化标记某个 event-task 关联是否已用于生成任务摘要。

## 实现细节

### 1. 数据库模型更新

**文件**: `lifetrace/storage/models.py`

在 `EventAssociation` 模型中添加新字段：

```python
# 摘要状态
used_in_summary = Column(Boolean, default=False, nullable=False, index=True)  # 是否已用于任务摘要
```

**索引优化**：添加了索引以提高按 `used_in_summary` 过滤时的查询性能。

### 2. 数据库迁移脚本

**文件**: `lifetrace/scripts/migrate_add_used_in_summary.py`

创建迁移脚本来添加新字段：

```bash
python3 lifetrace/scripts/migrate_add_used_in_summary.py
```

执行结果：
- 添加 `used_in_summary` 字段，默认值为 `False`
- 创建索引 `idx_event_associations_used_in_summary`
- 所有现有记录初始化为未使用状态

### 3. DatabaseManager 扩展

**文件**: `lifetrace/storage/database.py`

#### 3.1 扩展 `list_contexts` 方法

添加 `used_in_summary` 过滤参数：

```python
def list_contexts(
    self,
    associated: bool | None = None,
    task_id: int | None = None,
    project_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
    mapping_attempted: bool | None = None,
    used_in_summary: bool | None = None,  # 新增参数
) -> list[dict[str, Any]]:
```

**用法示例**：

```python
# 获取任务的所有未被用于摘要的上下文
new_contexts = db_manager.list_contexts(
    task_id=123,
    used_in_summary=False,
    limit=1000
)
```

#### 3.2 扩展 `count_contexts` 方法

同样添加 `used_in_summary` 过滤参数，用于统计未使用的上下文数量。

#### 3.3 新增 `mark_contexts_used_in_summary` 方法

批量标记 event-task 关联为已用于摘要：

```python
def mark_contexts_used_in_summary(self, task_id: int, event_ids: list[int]) -> bool:
    """标记 event-task 关联为已用于摘要"""
```

**特点**：
- 批量更新，性能高效
- 只更新指定任务的指定事件
- 记录日志便于追踪

### 4. TaskSummaryService 重构

**文件**: `lifetrace/jobs/task_summary.py`

#### 4.1 移除内存缓存

删除以下内容：
- `self._summarized_contexts` 字典
- `_get_new_contexts()` 方法
- `_mark_contexts_as_summarized()` 方法

#### 4.2 使用数据库字段过滤

在 `_process_all_tasks()` 中直接查询未使用的上下文：

```python
# 获取该任务关联的所有上下文，只获取未被用于摘要的
new_contexts = self.db_manager.list_contexts(
    task_id=task_id,
    used_in_summary=False,
    limit=1000,
    offset=0
)
```

#### 4.3 更新标记逻辑

生成摘要后，在数据库中标记：

```python
if progress_id:
    # 标记这些上下文已被摘要（在数据库中标记）
    event_ids = [ctx["id"] for ctx in new_contexts]
    self.db_manager.mark_contexts_used_in_summary(task_id, event_ids)
```

#### 4.4 重构 `clear_summary_history` 方法

使用数据库操作而不是清空内存字典：

```python
def clear_summary_history(self, task_id: int | None = None):
    """将数据库中的 used_in_summary 标记重置为 False"""
    from lifetrace.storage.models import EventAssociation
    from sqlalchemy import update

    with self.db_manager.get_session() as session:
        if task_id is None:
            stmt = update(EventAssociation).values(used_in_summary=False)
        else:
            stmt = update(EventAssociation).where(
                EventAssociation.task_id == task_id
            ).values(used_in_summary=False)
        result = session.execute(stmt)
        session.commit()
```

## 工作流程

### 自动摘要流程

1. **定期扫描**：调度器每小时（可配置）触发一次
2. **查询新数据**：通过 `used_in_summary=False` 过滤获取未用于摘要的 events
3. **判断是否触发**：如果新 events 数量 >= `min_new_contexts`（默认5个）
4. **生成摘要**：调用 LLM 基于新 events 生成进展摘要
5. **保存结果**：保存到 `task_progress` 表
6. **标记已使用**：调用 `mark_contexts_used_in_summary` 批量标记

### 手动触发流程

通过 API 手动触发：

```bash
POST /api/projects/{project_id}/tasks/{task_id}/generate-summary
```

逻辑相同，但立即执行而不等待调度。

### 重新生成摘要

如果需要重新生成摘要（例如调整了摘要prompt），可以：

```python
# 清除单个任务的摘要历史
summary_service.clear_summary_history(task_id=123)

# 清除所有任务的摘要历史
summary_service.clear_summary_history(task_id=None)
```

## 优势

### 1. 数据持久化
- ✅ 服务重启后状态保持
- ✅ 可以恢复中断的摘要任务
- ✅ 支持分布式部署

### 2. 更精确的控制
- ✅ 每个 event-task 关联独立标记
- ✅ 同一 event 可能关联多个 task，分别标记
- ✅ 支持灵活的查询和统计

### 3. 更好的可追溯性
- ✅ 可以查询哪些 events 被用于哪次摘要
- ✅ 结合 `task_progress` 表可以完整追踪摘要历史
- ✅ 便于调试和问题排查

### 4. 性能优化
- ✅ 添加索引提高查询速度
- ✅ 批量更新减少数据库操作
- ✅ 避免重复处理节省 token 成本

## 配置

在 `config.yaml` 中的相关配置：

```yaml
jobs:
  task_summary:
    enabled: true           # 是否启用任务摘要
    interval: 3600          # 检查间隔（秒）
    min_new_contexts: 5     # 触发摘要的最小新上下文数
```

## API 接口

### 查询任务进展

```bash
# 获取任务的进展记录列表
GET /api/projects/{project_id}/tasks/{task_id}/progress

# 获取任务最新的进展记录
GET /api/projects/{project_id}/tasks/{task_id}/progress/latest
```

### 手动触发摘要

```bash
POST /api/projects/{project_id}/tasks/{task_id}/generate-summary
```

## 统计数据

迁移完成后的统计：
- 总关联记录数：440
- 有任务关联的记录：289
- 已用于摘要的记录：0（全部初始化为未使用）

## 向后兼容性

✅ 完全向后兼容，不影响现有功能：
- 所有现有 API 保持不变
- 摘要生成逻辑保持一致
- 只是改变了数据存储方式

## 测试建议

1. **基本功能测试**
   - 创建任务并关联 events
   - 验证自动摘要生成
   - 验证标记正确更新

2. **边界条件测试**
   - event 数量不足 min_new_contexts
   - 任务没有关联 events
   - 所有 events 都已用于摘要

3. **重置功能测试**
   - 清除单个任务的历史
   - 清除所有任务的历史
   - 重新生成摘要

## 后续优化建议

1. **摘要质量优化**
   - 可以在 `task_progress` 表中记录使用了哪些 event_ids
   - 实现更细粒度的摘要历史追踪

2. **性能监控**
   - 添加摘要生成时长监控
   - 统计 token 使用量
   - 分析摘要触发频率

3. **用户交互**
   - 前端展示哪些 events 被用于某次摘要
   - 支持用户选择性地将某些 events 排除或包含在摘要中
   - 提供摘要质量反馈机制

## 总结

这次优化将任务摘要的状态管理从内存迁移到数据库，使系统更加健壮、可靠和易于维护。通过在 `event_associations` 表中添加 `used_in_summary` 字段，实现了：

- ✅ 持久化的摘要状态跟踪
- ✅ 更精确的新数据识别
- ✅ 更好的分布式支持
- ✅ 完整的数据可追溯性

这为未来更高级的摘要功能（如增量摘要、智能摘要等）奠定了基础。
