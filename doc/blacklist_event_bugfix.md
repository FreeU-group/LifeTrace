# 黑名单机制事件关闭 Bug 修复

## 问题描述

**Bug ID**: 黑名单切换时事件未正确关闭

**严重级别**: 中等

**影响版本**: 修复前所有版本

### 问题现象

当用户从白名单应用切换到黑名单应用时，白名单应用的事件（Event）不会被正确关闭，导致：

1. **时长计算错误**：白名单应用的使用时长会被错误地延长
2. **时间线不准确**：事件的 `end_time` 一直保持为 `NULL`，直到切换到下一个白名单应用

### 复现步骤

1. 配置黑名单：`config.yaml` 中设置 `blacklist.enabled: true` 和 `blacklist.apps: ["微信"]`
2. 启动 LifeTrace
3. 使用 Chrome 浏览器（白名单应用）30 分钟
4. 切换到微信（黑名单应用）30 分钟
5. 切换到 VS Code（白名单应用）

**预期结果**：
- Chrome 的 Event 在 10:30 被关闭（使用时长 30 分钟）
- 微信不产生 Event 记录
- VS Code 在 11:00 创建新 Event

**实际结果（修复前）**：
- Chrome 的 Event 在 11:00 才被关闭（使用时长被错误记录为 60 分钟）
- 包含了使用微信的 30 分钟

## 根本原因

在 `lifetrace_backend/recorder.py` 的 `capture_all_screens()` 方法中：

```python
# 检查是否在黑名单中
if self._is_app_blacklisted(app_name, window_title):
    logger.debug(f"当前应用 '{app_name}' 或窗口 '{window_title}' 在黑名单中，跳过所有屏幕截图")
    print(f"[黑名单] 跳过截图 - 应用: {app_name}, 窗口: {window_title}")
    return captured_files  # ❌ 直接返回，不做任何数据库操作
```

**问题点**：
- 直接返回，不调用任何数据库操作
- `get_or_create_event()` 不会被调用
- 事件关闭逻辑在 `get_or_create_event()` 中，因此上一个事件不会被关闭

## 修复方案

### 修改 1：`lifetrace_backend/recorder.py`

在检测到黑名单应用时，增加关闭上一个活跃事件的逻辑：

```python
# 检查是否在黑名单中
if self._is_app_blacklisted(app_name, window_title):
    logger.debug(f"当前应用 '{app_name}' 或窗口 '{window_title}' 在黑名单中，跳过所有屏幕截图")
    print(f"[黑名单] 跳过截图 - 应用: {app_name}, 窗口: {window_title}")

    # ✅ 新增：关闭上一个未结束的事件（如果存在）
    try:
        db_manager.close_active_event()
        logger.debug("已关闭上一个活跃事件")
    except Exception as e:
        logger.error(f"关闭活跃事件失败: {e}")

    return captured_files
```

### 修改 2：`lifetrace_backend/storage.py`

增强 `close_active_event()` 方法，使其在关闭事件时也触发事件摘要生成：

```python
def close_active_event(self, end_time: Optional[datetime] = None) -> bool:
    """主动结束当前事件（可在程序退出时调用）"""
    try:
        closed_event_id = None
        with self.get_session() as session:
            last_event = self._get_last_open_event(session)
            if last_event and last_event.end_time is None:
                last_event.end_time = end_time or datetime.now()
                closed_event_id = last_event.id
                session.flush()

        # ✅ 新增：在session关闭后，异步生成已关闭事件的摘要
        if closed_event_id:
            try:
                from lifetrace_backend.event_summary_service import generate_event_summary_async
                generate_event_summary_async(closed_event_id)
            except Exception as e:
                logging.error(f"触发事件摘要生成失败: {e}")

        return closed_event_id is not None
    except SQLAlchemyError as e:
        logging.error(f"结束事件失败: {e}")
        return False
```

## 修复效果

### 修复后的行为

| 时间 | 应用 | 操作 | Event 状态 | 说明 |
|------|------|------|-----------|------|
| 10:00 | Chrome | 正常截图 | Event #1: start_time=10:00, end_time=NULL | ✅ 创建事件 |
| 10:30 | 微信（黑名单）| 检测到黑名单 | Event #1: end_time=10:30 | ✅ 立即关闭 Chrome 事件 |
| 10:30-11:00 | 微信 | 持续跳过截图 | 无事件记录 | ✅ 无黑名单应用记录 |
| 11:00 | VS Code | 正常截图 | Event #2: start_time=11:00, end_time=NULL | ✅ 创建新事件 |

### 数据准确性

- ✅ **Chrome 使用时长**：30 分钟（10:00-10:30）
- ✅ **微信使用时长**：不记录（隐私保护）
- ✅ **时间线完整性**：事件正确关闭，无数据污染
- ✅ **事件摘要**：Chrome 事件会自动生成 AI 摘要

## 测试建议

### 手动测试

1. 配置黑名单应用
2. 按照复现步骤操作
3. 检查数据库 `events` 表：
   ```sql
   SELECT id, app_name, start_time, end_time,
          (julianday(end_time) - julianday(start_time)) * 24 * 60 as duration_minutes
   FROM events
   ORDER BY start_time DESC
   LIMIT 5;
   ```
4. 验证白名单应用的事件 `end_time` 是否正确设置

### 自动化测试

```python
def test_blacklist_closes_previous_event():
    """测试黑名单切换时是否正确关闭上一个事件"""
    # 1. 模拟白名单应用（Chrome）
    recorder.capture_all_screens()  # app_name="chrome.exe"

    # 2. 获取当前活跃事件
    event_before = db_manager.get_last_open_event()
    assert event_before.end_time is None

    # 3. 切换到黑名单应用（微信）
    recorder.capture_all_screens()  # app_name="WeChat.exe"

    # 4. 验证上一个事件已关闭
    event_after = db_manager.get_event_by_id(event_before.id)
    assert event_after.end_time is not None

    # 5. 验证没有为黑名单应用创建新事件
    latest_event = db_manager.get_last_open_event()
    assert latest_event is None  # 没有新的未结束事件
```

## 相关文档

- [事件机制文档](./event_mechanism.md)
- [黑名单配置文档](../config/default_config.yaml)

## 修复日期

2025-10-11

## 修复人员

AI Assistant (Claude Sonnet 4.5)
