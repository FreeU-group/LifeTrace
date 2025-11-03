# Static Assets 说明

本目录存放本地化的 JavaScript 库文件，避免依赖外部 CDN。

## 当前文件

| 文件名 | 说明 | 版本 | 来源 |
|--------|------|------|------|
| `lucide.min.js` | Lucide Icons 图标库 | latest | https://cdn.jsdelivr.net/npm/lucide@latest/dist/umd/lucide.min.js |
| `turndown.min.js` | HTML to Markdown 转换库 | 7.1.2 | https://cdn.jsdelivr.net/npm/turndown@7.1.2/dist/turndown.min.js |

## 更新方法

如需更新这些库到最新版本，可以使用以下 PowerShell 命令：

```powershell
# 更新 Lucide Icons
Invoke-WebRequest -Uri 'https://cdn.jsdelivr.net/npm/lucide@latest/dist/umd/lucide.min.js' -OutFile 'lucide.min.js'

# 更新 Turndown
Invoke-WebRequest -Uri 'https://cdn.jsdelivr.net/npm/turndown@7.1.2/dist/turndown.min.js' -OutFile 'turndown.min.js'
```

## 使用位置

这些库在以下 HTML 模板中被引用：

### lucide.min.js
- `templates/chat.html` - 聊天界面图标
- `templates/settings.html` - 设置页面图标
- `templates/app_usage.html` - 应用使用统计图标
- `templates/analytics.html` - 用户行为分析图标

### turndown.min.js
- `templates/chat.html` - Markdown 编辑器功能

## 注意事项

1. 这些文件应该在打包（PyInstaller）时被包含
2. server.py 已配置 `/static` 路由来服务这些文件
3. 本地化可以确保离线环境下功能正常
