# 项目助手截图幻觉问题修复

## 问题描述

在项目助手中，当用户询问"接下来我应该做什么任务"等不需要查询历史数据的问题时，AI 回复中会出现编造的截图引用（如 [截图ID: xxx]），这些截图并不真实存在。

## 问题根因

### 1. 意图识别与数据检索的不匹配

当用户询问任务建议时，系统的意图识别模块正确地判断不需要查询数据库（`needs_database=False`），因此不会检索任何历史记录数据。

### 2. 提示词要求与实际上下文的冲突

原有的项目助手提示词包含以下要求：
```yaml
**你的职责：**
1. 帮助用户分析和总结与该项目相关的工作内容
2. 基于用户的历史记录（屏幕截图和OCR文本）提供有用的见解
3. 在回答中引用具体的截图ID来源，格式为：[截图ID: xxx]
```

这导致 LLM 在没有实际历史数据的情况下，仍然试图满足"引用截图ID"的要求，从而编造了不存在的截图。

## 解决方案

### 1. 区分有数据和无数据的提示词

在 `lifetrace/config/prompt.yaml` 中，为项目助手创建了 4 个不同场景的提示词：

#### 无历史数据场景（用于任务建议、规划等）
- `system_prompt`: 基础项目助手提示词
- `system_prompt_with_selected_tasks`: 带选中任务的提示词

这两个提示词的特点：
- 强调基于任务列表和项目目标提供建议
- **明确禁止编造截图或数据**
- 不要求引用截图ID

#### 有历史数据场景（用于查询历史工作记录）
- `system_prompt_with_data`: 带历史数据的提示词
- `system_prompt_with_data_and_selected_tasks`: 带历史数据和选中任务的提示词

这两个提示词的特点：
- 要求基于提供的历史记录提供见解
- **强制要求引用截图ID**
- 明确只使用提供的数据，不编造

### 2. 修改 RAG 服务逻辑

在 `lifetrace/llm/rag_service.py` 的 `process_query_stream` 方法中，根据是否需要查询数据库来选择不同的提示词：

```python
if not needs_db:
    # 不需要数据库查询（不会检索历史数据）
    # 使用无数据版本的提示词
    if project_info:
        if selected_tasks_info_str:
            system_prompt = get_prompt("project_assistant", "system_prompt_with_selected_tasks", ...)
        else:
            system_prompt = get_prompt("project_assistant", "system_prompt", ...)
else:
    # 需要数据库查询（会检索历史数据）
    # 使用有数据版本的提示词
    if project_info:
        if selected_tasks_info_str:
            project_context = get_prompt("project_assistant", "system_prompt_with_data_and_selected_tasks", ...)
        else:
            project_context = get_prompt("project_assistant", "system_prompt_with_data", ...)
```

## 修改的文件

1. `lifetrace/config/prompt.yaml`
   - 修改了 `project_assistant.system_prompt`
   - 修改了 `project_assistant.system_prompt_with_selected_tasks`
   - 新增了 `project_assistant.system_prompt_with_data`
   - 新增了 `project_assistant.system_prompt_with_data_and_selected_tasks`

2. `lifetrace/llm/rag_service.py`
   - 修改了 `process_query_stream` 方法中的提示词选择逻辑
   - 根据 `needs_db` 标志选择合适的提示词模板

## 效果验证

### 修复前
```
用户：接下来我应该做什么任务
AI：根据您的最近工作记录 [截图ID: 12345]，我建议您... [截图ID: 67890]
```

### 修复后
```
用户：接下来我应该做什么任务
AI：根据项目的任务列表，我建议您优先完成以下任务：
1. ⏳ [pending] 任务名称
   描述: 任务描述...
```

## 注意事项

1. **提示词的一致性**：确保所有 4 个提示词模板保持一致的语气和风格
2. **数据可追溯性**：当确实有历史数据时，仍然强制要求引用截图ID，保证信息可追溯
3. **扩展性**：如果将来需要添加更多场景，可以继续扩展提示词模板

## 相关资源

- 提示词配置文件：`lifetrace/config/prompt.yaml`
- RAG 服务实现：`lifetrace/llm/rag_service.py`
- 提示词加载器：`lifetrace/util/prompt_loader.py`

## 日期

2025-11-16
