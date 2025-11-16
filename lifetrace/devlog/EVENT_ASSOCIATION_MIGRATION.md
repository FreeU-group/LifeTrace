# Event 关联表迁移完成报告

## 🎯 迁移目标

将 `events.task_id` 字段迁移到独立的 `event_associations` 关联表，实现：
1. ✅ 保存 project_id（之前会被浪费掉）
2. ✅ 保存置信度、判断理由等元数据
3. ✅ 更清晰的数据结构和扩展性
4. ✅ 完全移除 `events.task_id` 字段

## 📊 迁移完成统计

### 数据库变更
- ✅ 创建 `event_associations` 表
- ✅ 迁移 270 条现有关联数据
- ✅ 移除 `events.task_id` 字段
- ✅ 备份数据库：`lifetrace.db.backup_20251114_114100`

### 代码变更统计
| 文件 | 改动类型 | 说明 |
|------|---------|------|
| `storage/models.py` | 新增模型 | 添加 `EventAssociation` 模型 |
| `storage/database.py` | 大量修改 | 更新所有上下文查询方法 |
| `jobs/task_context_mapper.py` | 重构逻辑 | 保存 project_id 和置信度 |
| `routers/context.py` | 接口更新 | 支持 project_id |
| `schemas/context.py` | Schema 更新 | 添加 project_id 字段 |

## 🗄️ 新表结构

```sql
CREATE TABLE event_associations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,              -- 事件ID
    project_id INTEGER,                     -- 项目ID ✨
    task_id INTEGER,                        -- 任务ID
    project_confidence REAL,                -- 项目置信度 ✨
    task_confidence REAL,                   -- 任务置信度 ✨
    reasoning TEXT,                         -- LLM 判断理由 ✨
    association_method VARCHAR(20),         -- auto/manual ✨
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (event_id) REFERENCES events(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
```

**新增字段说明（标记 ✨）：**
- `project_id`: LLM 第一步判断的项目归属，之前会被丢弃
- `project_confidence`: 项目判断的置信度（0-1）
- `task_confidence`: 任务判断的置信度（0-1）
- `reasoning`: LLM 给出的判断理由
- `association_method`: 区分自动关联(`auto`)和手动关联(`manual`)

## 🔧 核心代码改动

### 1. 数据库查询方法 (`database.py`)

**之前：**
```python
# 直接查询 events.task_id
q = session.query(Event)
if associated:
    q = q.filter(Event.task_id.isnot(None))
```

**现在：**
```python
# LEFT JOIN event_associations 获取关联信息
q = session.query(Event, EventAssociation).outerjoin(
    EventAssociation, Event.id == EventAssociation.event_id
)
if associated:
    q = q.filter(EventAssociation.task_id.isnot(None))
```

### 2. 任务上下文映射器 (`task_context_mapper.py`)

**之前：**
```python
# 只保存 task_id，project_id 被丢弃
project_id = determine_project()  # 结果丢失！
task_id = determine_task(project_id)
update_context_task(context_id, task_id)
```

**现在：**
```python
# 保存所有判断结果
project_id, project_confidence = determine_project()  # ✨ 保存
task_id, task_confidence, reasoning = determine_task(project_id)

# 保存到关联表，包含元数据
create_or_update_event_association(
    event_id=context_id,
    project_id=project_id,              # ✨ 保存
    task_id=task_id,
    project_confidence=project_confidence,  # ✨ 保存
    task_confidence=task_confidence,        # ✨ 保存
    reasoning=reasoning,                    # ✨ 保存
    association_method="auto"
)
```

### 3. API 接口更新 (`routers/context.py`)

**响应数据现在包含：**
```json
{
  "id": 1,
  "app_name": "Google Chrome",
  "project_id": 1,     // ✨ 新增
  "task_id": 5,
  "created_at": "..."
}
```

## 💡 关键改进

### 1. 数据完整性
- ✅ **之前**：project_id 判断结果被丢弃，浪费 LLM 调用
- ✅ **现在**：所有判断结果都被保存

### 2. 可审计性
- ✅ **之前**：无法知道为什么关联到某个任务
- ✅ **现在**：有 reasoning、confidence、method 等元数据

### 3. 灵活性
- ✅ **之前**：必须关联到任务才能保存
- ✅ **现在**：可以只关联到项目，任务关联可选

### 4. 扩展性
- ✅ **之前**：`events` 表字段臃肿
- ✅ **现在**：关联信息独立，易于扩展

## 📈 实际效果

### 迁移前数据分布
```
总 events: 584
├─ 已关联任务: 270 (event.task_id 不为空)
└─ 未关联任务: 314
```

### 迁移后数据分布
```
总 events: 584
├─ event_associations 记录: 270
│   ├─ 关联到项目: 270 (project_id 不为空)
│   └─ 关联到任务: 270 (task_id 不为空)
└─ 未尝试关联: 314
```

## 🔄 向后兼容性

### API 兼容
- ✅ 原有 API 端点保持不变
- ✅ 响应格式兼容（只是新增字段）
- ✅ 请求参数兼容

### 查询兼容
```python
# 这些查询都正常工作
list_contexts(associated=True)      # 获取已关联的
list_contexts(task_id=5)            # 按任务过滤
list_contexts(project_id=1)         # ✨ 新功能：按项目过滤
```

## 📝 后续优化建议

### 1. 清理低质量关联
```sql
-- 查找置信度过低的自动关联
SELECT * FROM event_associations
WHERE association_method = 'auto'
AND (project_confidence < 0.5 OR task_confidence < 0.5);
```

### 2. 分析关联准确性
```sql
-- 统计不同置信度范围的关联数量
SELECT
    CASE
        WHEN task_confidence >= 0.9 THEN 'high'
        WHEN task_confidence >= 0.7 THEN 'medium'
        ELSE 'low'
    END as confidence_level,
    COUNT(*) as count
FROM event_associations
WHERE task_id IS NOT NULL
GROUP BY confidence_level;
```

### 3. 优化未关联的 events
```sql
-- 找出可能需要手动关联的高价值 events
SELECT e.*
FROM events e
LEFT JOIN event_associations ea ON e.id = ea.event_id
WHERE ea.id IS NULL
AND e.auto_association_attempted = 1
ORDER BY e.start_time DESC;
```

## ⚠️ 注意事项

1. **备份已创建**：`lifetrace.db.backup_20251114_114100`
2. **需要重启服务**：让新代码生效
3. **旧的 task_context_mapper 任务**：如果正在运行，需要重启
4. **前端可能需要更新**：如果显示 project_id

## 🎉 总结

这次迁移实现了：
- ✅ 彻底移除 `events.task_id`
- ✅ 创建规范的 `event_associations` 关联表  
- ✅ 保存所有 LLM 判断元数据
- ✅ 支持按项目查询 events
- ✅ 向后兼容，0 linter 错误

**数据更完整，结构更清晰，可扩展性更强！** 🚀

---

**迁移时间：** 2025-11-14  
**影响版本：** v0.2.0+  
**迁移工具：** `lifetrace/scripts/migrate_to_event_associations.py`
