# LLM 健康检查与配置引导功能说明

## 功能概述

在启动前端应用时，系统会自动进行 LLM 服务健康检查。如果检测到 LLM 服务未配置或不可用，将自动弹出设置界面，引导用户完成 API Key 配置。

## 功能特性

### 1. 启动时健康检查

- **自动检测**: 前端启动时自动调用 `/health/llm` 接口检查 LLM 服务状态
- **加载提示**: 健康检查期间显示"正在检查系统状态..."的加载界面
- **智能判断**: 根据检查结果决定是否需要强制显示设置界面

### 2. 设置界面增强

#### 必填字段标识
- API Key 和 Base URL 标记为必填项（红色星号 *）
- 在未配置状态下，保存按钮会被禁用

#### API 测试按钮
- 新增"测试 API 连接"按钮
- 在填写 API Key 和 Base URL 后可以测试连接
- 实时反馈测试结果（成功 ✓ 或失败 ✗）

#### 强制配置模式
- 当健康检查失败时，设置对话框进入强制配置模式：
  - 显示警告提示："⚠️ 需要配置 API Key 才能使用 LLM 功能"
  - 无法通过点击背景或关闭按钮关闭对话框
  - 只有成功保存配置后才能关闭
  - 关闭后自动重新进行健康检查

### 3. 健康检查状态

后端 LLM 健康检查返回的状态：

| 状态 | 说明 | 前端响应 |
|------|------|----------|
| `healthy` | LLM 服务正常 | 正常进入应用 |
| `unconfigured` | API Key 或 Base URL 未配置 | 强制显示设置界面 |
| `unavailable` | RAG 服务未初始化 | 强制显示设置界面 |
| `error` | LLM 服务异常（连接失败、认证失败等） | 强制显示设置界面 |

## 技术实现

### 后端实现

#### 新增健康检查端点

**文件**: `lifetrace/routers/health.py`

```python
@router.get("/health/llm")
async def llm_health_check():
    """LLM服务健康检查"""
    try:
        # 检查RAG服务是否已初始化
        if deps.rag_service is None:
            return {
                "status": "unavailable",
                "message": "RAG服务未初始化",
                "timestamp": datetime.now().isoformat(),
            }

        # 检查配置是否完整
        config = deps.config.get_config()
        llm_key = config.get("llm_key")
        base_url = config.get("base_url")

        if not llm_key or not base_url:
            return {
                "status": "unconfigured",
                "message": "LLM配置不完整，请设置API Key和Base URL",
                "timestamp": datetime.now().isoformat(),
            }

        # 测试LLM连接
        from openai import OpenAI

        client = OpenAI(api_key=llm_key, base_url=base_url)
        model = config.get("llm_model", "qwen3-max")

        # 发送最小化测试请求
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5,
            timeout=10,
        )

        return {
            "status": "healthy",
            "message": "LLM服务正常",
            "model": model,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        deps.logger.error(f"LLM健康检查失败: {e}")
        return {
            "status": "error",
            "message": f"LLM服务异常: {str(e)}",
            "timestamp": datetime.now().isoformat(),
        }
```

### 前端实现

#### 1. API 调用

**文件**: `frontend/lib/api.ts`

```typescript
// 健康检查
healthCheck: () => apiClient.get('/health'),

llmHealthCheck: () => apiClient.get('/health/llm'),
```

#### 2. 主布局组件

**文件**: `frontend/components/layout/MainLayout.tsx`

核心功能：
- 在组件挂载时调用 `checkLlmHealth()`
- 根据健康检查结果决定是否显示设置界面
- 处理设置界面的打开和关闭逻辑
- 在强制配置模式下，关闭后重新检查健康状态

```typescript
const checkLlmHealth = async () => {
  setIsChecking(true);
  try {
    const response = await api.llmHealthCheck();
    const status = response.data.status;

    // 如果状态不是 healthy，强制显示设置界面
    if (status !== 'healthy') {
      setIsHealthCheckRequired(true);
      setIsSettingsOpen(true);
    } else {
      // 健康检查通过，关闭设置窗口
      setIsHealthCheckRequired(false);
      setIsSettingsOpen(false);
    }
  } catch (error) {
    console.error('LLM健康检查失败:', error);
    // 网络错误或其他错误，也强制显示设置界面
    setIsHealthCheckRequired(true);
    setIsSettingsOpen(true);
  } finally {
    setIsChecking(false);
  }
};
```

#### 3. 设置对话框组件

**文件**: `frontend/components/common/SettingsModal.tsx`

新增特性：
- `isRequired` 属性：标识是否为强制配置模式
- `handleTest` 函数：测试 API 连接
- 在强制配置模式下禁用背景点击关闭
- 在强制配置模式下隐藏关闭按钮和取消按钮

#### 4. 头部组件重构

**文件**: `frontend/components/layout/Header.tsx`

- 移除内部的 SettingsModal 状态管理
- 通过 props 接收 `onSettingsClick` 回调
- 将设置状态提升到 MainLayout 统一管理

## 使用流程

### 首次使用

1. 用户启动前端应用
2. 系统显示"正在检查系统状态..."
3. 检测到 LLM 未配置
4. 自动弹出设置界面（强制模式）
5. 用户填写 API Key 和 Base URL
6. 点击"测试 API 连接"按钮验证配置
7. 测试成功后点击"保存"
8. 系统自动重新检查健康状态
9. 检查通过，进入正常使用

### 正常使用

1. 用户启动前端应用
2. 系统显示"正在检查系统状态..."
3. 健康检查通过
4. 直接进入应用主界面

### 配置失效

1. 当 API Key 失效或网络问题导致 LLM 不可用时
2. 用户可以手动点击设置按钮
3. 修改配置并测试
4. 保存后继续使用

## 测试方法

### 测试场景 1：未配置状态

1. 清空 `lifetrace/config/config.yaml` 中的 `llm_key` 和 `base_url`
2. 启动后端服务
3. 启动前端应用
4. 预期结果：自动弹出设置界面，显示警告提示

### 测试场景 2：已配置状态

1. 确保 `config.yaml` 中有有效的 API Key 和 Base URL
2. 启动后端服务
3. 启动前端应用
4. 预期结果：健康检查通过，直接进入应用

### 测试场景 3：配置错误

1. 在 `config.yaml` 中填写无效的 API Key
2. 启动后端服务
3. 启动前端应用
4. 预期结果：检测到错误，自动弹出设置界面

### 测试场景 4：API 测试按钮

1. 打开设置界面
2. 填写 API Key 和 Base URL
3. 点击"测试 API 连接"
4. 预期结果：显示测试成功或失败的提示信息

## 相关文件

### 后端
- `lifetrace/routers/health.py` - 健康检查路由
- `lifetrace/routers/config.py` - 配置管理路由
- `lifetrace/server.py` - 路由注册

### 前端
- `frontend/components/layout/MainLayout.tsx` - 主布局组件（健康检查逻辑）
- `frontend/components/layout/Header.tsx` - 头部组件（设置按钮）
- `frontend/components/common/SettingsModal.tsx` - 设置对话框
- `frontend/lib/api.ts` - API 接口定义

## 注意事项

1. **首次启动延迟**: 健康检查需要调用 LLM API，可能会有几秒延迟
2. **超时时间**: LLM 测试请求设置了 10 秒超时
3. **错误处理**: 网络错误、超时等都会触发强制配置模式
4. **配置热重载**: 保存配置后会自动重新加载，无需重启后端

## 未来改进

- [ ] 添加多个 LLM 服务商的支持和切换
- [ ] 提供更详细的错误信息和解决方案
- [ ] 添加配置模板和常用服务商的快速配置
- [ ] 支持离线模式（禁用 LLM 相关功能）
