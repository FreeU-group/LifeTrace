# 事件上下文对话功能增强

## 概述

本文档描述了如何使用选中的事件作为上下文与大模型进行对话的功能。

## 功能特点

### 1. 事件选择
- 在事件页面 (`/events`) 可以选择一个或多个事件
- 点击事件卡片左下角的复选框即可选中/取消选中
- 选中的事件会被添加到全局上下文中

### 2. 上下文显示
- 选中事件后，页面顶部会显示一个提示条，显示已选择的事件数量
- 提供"清空选择"和"前往对话"两个快捷按钮

### 3. 对话功能
- 在对话页面 (`/chat`)，中间区域会显示所有选中的事件
- 每个事件卡片显示：
  - 事件ID和应用名称
  - AI摘要或普通摘要
  - 事件开始时间
  - 删除按钮（鼠标悬停时显示）

### 4. 智能问答
- 当有选中的事件时：
  - 输入框提示文字变为"基于选中的事件提问..."
  - 显示提示信息："📌 已选择 X 个事件作为上下文 (将使用流式响应)"
  - 发送消息时会使用流式接口 `/api/chat/stream-with-context`
  - 大模型会基于事件上下文回答问题

- 当没有选中事件时：
  - 使用普通的聊天接口 `/api/chat`
  - 可以选择是否启用RAG功能

## 使用流程

1. **选择事件**
   - 访问事件页面：`http://localhost:3000/events`
   - 浏览事件列表，点击感兴趣的事件左下角的复选框
   - 可以选择多个事件

2. **前往对话**
   - 选择完事件后，点击页面顶部的"前往对话"按钮
   - 或直接访问：`http://localhost:3000/chat`

3. **查看上下文**
   - 在对话页面，中间区域会显示所有选中的事件
   - 可以在这里查看事件详情或删除不需要的事件

4. **开始对话**
   - 在右侧输入框中输入问题
   - 大模型会结合事件上下文给出回答
   - 支持流式响应，实时显示生成内容

## 技术实现

### 前端

#### 全局状态管理
使用 React Context (`SelectedEventsContext`) 管理选中的事件：

```typescript
// lib/context/SelectedEventsContext.tsx
export function useSelectedEvents() {
  return useContext(SelectedEventsContext);
}
```

#### 事件页面 (`app/events/page.tsx`)
- 使用 `useSelectedEvents` hook 访问全局状态
- 实现 `toggleEventSelection` 函数来切换事件选择状态
- 添加选中提示条和"前往对话"按钮

#### 对话页面 (`app/chat/page.tsx`)
- 显示选中的事件列表
- 发送消息时检查是否有选中的事件
- 如果有，构建事件上下文并调用流式接口
- 使用 `ReadableStream` 读取流式响应并实时更新UI

### 后端

#### 流式接口 (`/api/chat/stream-with-context`)
已在后端实现 (`lifetrace/routers/chat.py`)：

```python
@router.post("/stream-with-context")
async def chat_with_context_stream(message: ChatMessageWithContext):
    """带事件上下文的流式聊天接口"""
    # 构建上下文文本
    context_text = ""
    if message.event_context:
        context_parts = []
        for ctx in message.event_context:
            event_text = f"事件ID: {ctx['event_id']}\n{ctx['text']}\n"
            context_parts.append(event_text)
        context_text = "\n---\n".join(context_parts)

    # 构建增强的prompt
    enhanced_message = f"""用户提供了以下事件上下文（来自屏幕记录的OCR文本）：

===== 事件上下文开始 =====
{context_text}
===== 事件上下文结束 =====

用户问题：{message.message}

请基于上述事件上下文回答用户问题。"""

    # ... 调用LLM流式API
```

## API接口

### POST `/api/chat/stream-with-context`

**请求体：**
```json
{
  "message": "用户的问题",
  "event_context": [
    {
      "event_id": 123,
      "text": "事件的AI摘要或文本内容"
    }
  ]
}
```

**响应：**
- 流式文本响应（`text/plain; charset=utf-8`）
- 逐块返回生成的内容

## 示例场景

### 场景1：回顾工作内容
1. 选择今天上午的所有工作事件
2. 提问："我今天上午做了什么？"
3. 大模型会基于选中的事件总结你的工作内容

### 场景2：查找特定信息
1. 选择与某个项目相关的事件
2. 提问："这个项目的关键决策是什么？"
3. 大模型会从事件上下文中提取相关信息

### 场景3：生成报告
1. 选择一周内的所有事件
2. 提问："帮我生成本周的工作总结"
3. 大模型会基于所有事件生成结构化的总结

## 注意事项

1. **上下文长度限制**
   - 选择的事件数量会影响上下文长度
   - 建议选择3-10个事件以获得最佳效果
   - 过多的事件可能导致上下文超出模型限制

2. **流式响应**
   - 使用事件上下文时会自动使用流式响应
   - 可以实时看到生成的内容
   - 响应速度取决于大模型的处理速度

3. **事件质量**
   - 事件的AI摘要质量会影响对话效果
   - 确保事件有有意义的摘要信息

## 未来改进

- [ ] 支持事件排序和过滤
- [ ] 添加事件上下文预览功能
- [ ] 支持保存带上下文的对话
- [ ] 优化长上下文的处理
- [ ] 添加上下文长度提示
