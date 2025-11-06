# Toast 通知实现文档

## 概述

实现了统一的 Toast 通知系统，在右上角显示各种操作的成功或失败信息。所有 Toast 通知使用统一的样式和配置。

## 实现内容

### 1. 安装依赖

```bash
pnpm add sonner
```

使用了 `sonner` - 一个现代、轻量且美观的 Toast 通知库。

### 2. 创建统一的 Toast 配置

#### 2.1 `frontend/lib/toast.ts` (新建)

创建了统一的 Toast 工具模块，包含：

**默认配置**
```typescript
const DEFAULT_CONFIG = {
  success: { duration: 3000 },  // 成功消息 3 秒
  error: { duration: 4000 },    // 错误消息 4 秒
  warning: { duration: 4000 },  // 警告消息 4 秒
  info: { duration: 3000 },     // 信息消息 3 秒
};
```

**基础通知方法**
- `toast.success()` - 成功通知
- `toast.error()` - 错误通知
- `toast.warning()` - 警告通知
- `toast.info()` - 信息通知

**业务场景快捷方法**
- `toast.configSaved()` - 配置保存成功
- `toast.configSaveFailed(error?)` - 配置保存失败
- `toast.configLoadFailed(error?)` - 配置加载失败
- `toast.eventLimitReached()` - 事件选择达到上限

### 3. 修改的文件

#### 3.1 `frontend/app/layout.tsx`

在根布局中添加了 `Toaster` 组件：

```typescript
import { Toaster } from "sonner";

// 在 body 中添加
<Toaster position="top-right" richColors closeButton />
```

配置说明：
- `position="top-right"`: 通知显示在右上角
- `richColors`: 启用彩色主题
- `closeButton`: 显示关闭按钮

#### 3.2 `frontend/components/common/SettingsModal.tsx`

使用统一的 Toast 配置：

```typescript
import { toast } from '@/lib/toast';

// 配置保存成功
toast.configSaved();

// 配置保存失败
toast.configSaveFailed(errorMsg);

// 配置加载失败
toast.configLoadFailed(errorMsg);
```

#### 3.3 `frontend/app/events/page.tsx`

使用统一的 Toast 配置：

```typescript
import { toast } from '@/lib/toast';

// 事件选择达到上限
if (newSet.size >= 10) {
  toast.eventLimitReached();
  return;
}
```

移除了原来的自定义 Toast UI 组件（第372-398行），统一使用 sonner 库。

## 功能特点

1. **统一配置**: 所有 Toast 通知使用统一的样式和时长配置
2. **位置**: Toast 通知显示在屏幕右上角
3. **自动消失**:
   - 成功/信息消息：3 秒后消失
   - 错误/警告消息：4 秒后消失
4. **可手动关闭**: 每个通知都有关闭按钮
5. **彩色主题**:
   - 成功：绿色
   - 错误：红色
   - 警告：橙色
   - 信息：蓝色
6. **详细信息**: 包含标题和详细描述
7. **优雅动画**: 滑入滑出动画效果
8. **业务场景快捷方法**: 预定义常用场景的通知

## 使用示例

### 基础用法

```typescript
import { toast } from '@/lib/toast';

// 成功通知
toast.success('操作成功', {
  description: '详细描述（可选）',
});

// 错误通知
toast.error('操作失败', {
  description: '详细描述（可选）',
});

// 警告通知
toast.warning('警告信息', {
  description: '详细描述（可选）',
});

// 信息通知
toast.info('提示信息', {
  description: '详细描述（可选）',
});
```

### 业务场景快捷方法

```typescript
import { toast } from '@/lib/toast';

// 配置相关
toast.configSaved();                    // 配置保存成功
toast.configSaveFailed('网络错误');      // 配置保存失败
toast.configLoadFailed('服务器错误');    // 配置加载失败

// 事件相关
toast.eventLimitReached();              // 事件选择达到上限
```

### 自定义时长

```typescript
import { toast } from '@/lib/toast';

// 自定义显示时长
toast.success('操作成功', {
  duration: 5000,  // 5秒后消失
});
```

## 样式

Toast 通知会自动适配系统的明暗主题。

## 测试

### 配置保存测试
1. 打开设置模态框
2. 修改配置并保存
3. 观察右上角绿色成功通知："配置保存成功"
4. 尝试触发错误（如网络断开），观察红色错误通知："配置保存失败"

### 事件选择测试
1. 进入事件页面
2. 选择事件，达到 10 个上限后
3. 尝试再选择一个事件
4. 观察右上角橙色警告通知："已达到选择上限"

## 相关文件

- `frontend/lib/toast.ts` - 统一的 Toast 配置和工具（新建）
- `frontend/app/layout.tsx` - Toaster 组件配置
- `frontend/components/common/SettingsModal.tsx` - 配置相关 Toast
- `frontend/app/events/page.tsx` - 事件相关 Toast
- `frontend/package.json` - sonner 依赖

## 注意事项

1. **统一使用** `@/lib/toast` 而不是直接使用 `sonner`
2. Toast 通知是全局的，只需在根布局添加一次 Toaster 组件
3. 优先使用预定义的业务场景方法（如 `toast.configSaved()`）
4. 通知会自动堆叠显示，不会重叠
5. 通知数量过多时会自动管理显示队列
6. 所有 Toast 的时长和样式已统一配置，无需每次指定

## 扩展指南

如果需要添加新的业务场景快捷方法，在 `frontend/lib/toast.ts` 中添加：

```typescript
export const toast = {
  // ... 现有方法

  // 新增业务场景
  uploadSuccess: () => {
    return toast.success('上传成功', {
      description: '文件已成功上传',
      duration: DEFAULT_CONFIG.success.duration,
    });
  },
};
```
