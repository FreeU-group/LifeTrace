# 会话 API 404 错误修复

## 问题描述

前端 `AppLayout.tsx` 组件在加载时调用了 `api.getConversations()` 接口，但后端并没有实现该接口，导致 404 错误。

## 错误信息

```
Request failed with status code 404
at async loadConversations (components/layout/AppLayout.tsx:51:24)
```

## 问题原因

前端代码中存在以下 API 调用，但后端未实现：

1. `GET /api/conversations` - 获取会话列表
2. `DELETE /api/conversations/:id` - 删除会话

后端 `lifetrace/routers/chat.py` 使用的是基于 session 的会话管理（`/api/chat/history`），而不是 conversation 接口。

## 解决方案

### 临时方案（已实施）

禁用前端的会话列表功能：

1. 注释掉 `loadConversations()` 中的 API 调用
2. 注释掉 `deleteConversation()` 中的 API 调用  
3. 隐藏会话列表 UI 组件
4. 保留"新建"按钮，用于清空当前聊天

### 永久方案（可选）

如果需要完整的会话管理功能，需要在后端添加：

#### 1. 数据模型

在 `lifetrace/storage/models.py` 中添加会话模型：

```python
class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True)
    title = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    messages = Column(JSON)  # 存储消息列表
```

#### 2. API 接口

在 `lifetrace/routers/chat.py` 中添加：

```python
@router.get("/conversations")
async def get_conversations():
    """获取会话列表"""
    # 实现逻辑
    pass

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """删除指定会话"""
    # 实现逻辑
    pass
```

## 影响范围

- 前端不再显示会话列表
- 用户仍可以使用聊天功能
- "新建"按钮用于清空当前对话
- 事件上下文聊天功能正常工作

## 相关文件

- `frontend/components/layout/AppLayout.tsx` - 前端布局组件
- `frontend/lib/api.ts` - API 定义
- `lifetrace/routers/chat.py` - 后端聊天路由
