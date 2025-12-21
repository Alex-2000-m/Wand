# 🪄 Wand - 您的全能 AI 助手

![Wand Banner](https://via.placeholder.com/1200x300/1e1e1e/ffffff?text=Wand+AI+Assistant)

> **Wand** 是一个基于 Electron 和 React 构建的现代化 AI 助手应用。它不仅仅是一个聊天机器人，更是一个集成了代码编辑、文件管理、文档预览和智能工具调用的全能工作台。

![Electron](https://img.shields.io/badge/Electron-28.1.0-47848F?style=flat-square&logo=electron&logoColor=white)
![React](https://img.shields.io/badge/React-18.2.0-61DAFB?style=flat-square&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.3.3-3178C6?style=flat-square&logo=typescript&logoColor=white)
![Python](https://img.shields.io/badge/Python-Backend-3776AB?style=flat-square&logo=python&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4.0-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)

## ✨ 核心特性

### 🤖 强大的 AI 对话
- **多模型支持**：无缝切换 SiliconFlow (DeepSeek), 阿里云百炼, OpenAI 等多种大模型服务。
- **流式响应**：体验流畅的打字机效果，实时获取 AI 回复。
- **思维链可视化**：独创的 `<thinking>` 折叠块，让 AI 的思考过程透明化，支持自动折叠与展开。
- **Debug 模式**：内置调试工具，可查看原始消息 JSON，方便开发者调试 Prompt。

### 📝 全能编辑器与查看器
- **多格式支持**：
  - **Markdown**：支持实时预览与源码编辑切换。
  - **PDF**：内置高性能 PDF 阅读器。
  - **HTML**：支持 HTML 文件渲染预览。
  - **代码文件**：支持多种编程语言的语法高亮编辑。
- **标签页管理**：像 IDE 一样管理多个打开的文件。

### 🛠️ 智能工具系统 (Agentic Workflow)
- **Python 后端驱动**：利用 Python 强大的生态系统处理复杂任务。
- **工具生成与执行**：AI 可以根据需求动态生成 Python 工具代码并执行。
- **文件系统操作**：支持读取、写入、列出目录等文件操作能力。

### 🎨 现代化 UI/UX
- **暗色主题**：精心调优的深色模式，护眼且专业。
- **响应式布局**：可拖拽调整侧边栏和对话框宽度。
- **文件资源管理器**：内置轻量级文件树，方便浏览项目结构。

## 🚀 快速开始

### 环境要求
- Node.js (v16+)
- Python (v3.8+)
- npm 或 yarn

### 安装步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/your-username/wand.git
   cd wand
   ```

2. **安装依赖**
   ```bash
   npm install
   ```

3. **配置 Python 环境**
   确保 `python` 命令在您的系统路径中可用，并且安装了必要的依赖（如 `openai`, `requests` 等，详见 `src/backend/requirements.txt`）。

4. **启动开发服务器**
   ```bash
   npm run dev
   ```

5. **构建生产版本**
   ```bash
   npm run build
   ```

## ⚙️ 配置指南

启动应用后，点击右上角的 **设置 (Settings)** 图标进行配置：

1. **选择服务商**：支持 SiliconFlow, Aliyun, OpenAI 或自定义。
2. **输入 API Key**：填入对应服务商的 API 密钥。
3. **模型选择**：
   - 配置高速模型（用于简单任务）
   - 配置强力模型（用于复杂推理）
   - 配置长上下文模型（用于文档分析）

## 📂 项目结构

```
Wand/
├── src/
│   ├── main/                 # Electron 主进程
│   │   ├── index.ts          # 应用入口
│   │   ├── ai-service.ts     # AI 服务桥接
│   │   └── file-service.ts   # 文件系统服务
│   ├── renderer/             # React 渲染进程 (UI)
│   │   ├── src/
│   │   │   ├── components/   # UI 组件 (ChatInterface, Editor, etc.)
│   │   │   ├── App.tsx       # 主应用组件
│   │   │   └── index.css     # Tailwind 样式
│   │   └── index.html
│   ├── preload/              # 预加载脚本 (IPC 安全通信)
│   └── backend/              # Python 后端
│       ├── cli.py            # AI 交互入口
│       ├── llm_processor.py  # LLM 处理逻辑
│       └── tools.py          # 工具函数库
├── electron.vite.config.ts   # 构建配置
├── package.json
└── README.md
```

## 🤝 贡献

欢迎提交 Pull Request 或 Issue！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交改动 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

[MIT](LICENSE) © 2025 Wand Team
