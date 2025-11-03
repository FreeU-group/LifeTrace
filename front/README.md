# LifeTrace Desktop - 桌面版应用

LifeTrace的Electron桌面应用版本，提供完整的原生桌面体验。

## 特性

- 🎨 精美的用户界面设计
- 🌓 明暗主题切换
- ⌨️ 完整的键盘快捷键支持
- 🔍 智能搜索和筛选
- 📱 响应式布局
- 🏃‍♂️ 高性能渲染

## 快速开始

### 前置条件

确保LifeTrace后端服务正在运行：
```bash
# 在LifeTrace主目录中启动后端
cd ../
python -m lifetrace serve
# 或者
lifetrace serve
```

后端服务默认运行在 `http://localhost:8840`

### 开发模式

1. 安装依赖
```bash
npm install
```

2. 启动开发服务器
```bash
npm run dev
```

3. 在另一个终端启动Electron
```bash
npm run electron
```

或者一键启动开发模式：
```bash
npm run electron-dev
```

### API连接测试

可以通过以下方式测试API连接：
1. 打开 `test-api.html` 文件在浏览器中查看API连接状态
2. 检查浏览器控制台的网络请求
3. 确保后端服务返回截图数据

### 构建生产版本

1. 构建React应用
```bash
npm run build
```

2. 打包Electron应用
```bash
npm run dist
```

构建完成后，可执行文件将在 `dist-electron` 目录中。

## 快捷启动脚本

Windows用户可以直接运行：
- `dev.bat` - 启动开发模式
- `build.bat` - 构建生产版本

## 键盘快捷键

### 基本导航
- `↑/↓` - 在搜索结果中上下导航
- `←/→` - 在标签页间切换，或在区域间移动
- `Enter` - 打开选中的项目或执行操作
- `Esc` - 返回搜索框
- `Tab` - 在不同区域间循环切换

### 功能区域
- **搜索区域** - 输入关键词进行搜索
- **标签区域** - 选择不同类型的内容（全部、应用、文档、时光机）
- **结果区域** - 浏览搜索结果
- **详情区域** - 查看选中项目的详细信息和执行操作

### 数据来源说明
- **应用分类** - 使用模拟数据（预设的常用应用）
- **文档分类** - 使用模拟数据（预设的文档示例）
- **时光机分类** - 使用真实API数据（从LifeTrace后端获取的截图记录）
- **全部分类** - 混合显示模拟数据和API数据

### 主题和设置
- 点击右上角的主题切换按钮可在明暗主题间切换
- 点击设置按钮可进入设置页面

## 技术栈

### 前端
- **React 18** - 用户界面框架
- **TypeScript** - 类型安全的JavaScript
- **Tailwind CSS** - 样式框架
- **Radix UI** - 高质量的UI组件库
- **Lucide React** - 图标库

### 桌面化
- **Electron** - 跨平台桌面应用框架
- **Electron Builder** - 应用打包工具

### 开发工具
- **Vite** - 快速的构建工具
- **PostCSS** - CSS处理器

## 项目结构

```
front/
├── public/                 # 静态资源
│   ├── electron.js        # Electron主进程
│   ├── preload.js        # 预加载脚本
│   └── icon.svg          # 应用图标
├── components/            # React组件
│   ├── SearchHeader.tsx  # 搜索头部
│   ├── SearchTabs.tsx    # 标签栏
│   ├── SearchResults.tsx # 搜索结果
│   ├── DetailPanel.tsx   # 详情面板
│   ├── Settings.tsx      # 设置页面
│   └── ui/               # 基础UI组件
├── styles/               # 样式文件
│   └── globals.css       # 全局样式
├── App.tsx              # 主应用组件
├── main.tsx             # 应用入口
└── package.json         # 项目配置
```

## 开发说明

### 环境要求
- Node.js 16+
- npm 或 yarn

### 添加新功能
1. 在 `components/` 目录下创建新组件
2. 在 `App.tsx` 中集成新组件
3. 更新类型定义和状态管理

### 样式开发
- 使用Tailwind CSS类名进行样式设计
- 主题相关的样式在 `styles/globals.css` 中定义
- 组件特定样式直接在组件文件中编写

### 键盘交互
- 键盘事件处理在 `App.tsx` 的 `useEffect` 中统一管理
- 焦点状态通过 `focusArea` 状态控制
- 添加新的键盘快捷键需要更新事件处理逻辑

## 故障排除

### 构建问题
1. 确保所有依赖已正确安装：`npm install`
2. 清理缓存：`npm run build`
3. 检查Node.js版本是否兼容

### Electron启动问题
1. 确保已先构建React应用：`npm run build`
2. 检查 `public/electron.js` 文件路径
3. 验证端口是否被占用

### 权限问题（Windows）
如果遇到符号链接权限错误，请：
1. 以管理员身份运行命令提示符
2. 或使用目录构建模式而不是打包模式

## 许可证

本项目采用MIT许可证。详见LICENSE文件。

## 贡献

欢迎提交Issue和Pull Request来改进项目。

---

**LifeTrace Desktop** - 让你的数字生活轨迹更清晰
