# 🎨 HTML 智能编辑器

一个基于 React + Flask 的全栈应用，使用自然语言和 LLM API 来智能修改 HTML 网页。

## ✨ 主要功能

- 📁 **文件上传** - 支持拖放或点击上传 HTML 文件
- 🤖 **多 API 支持** - 集成 OpenRouter、OpenAI、SiliconFlow、Gemini
- ✏️ **自然语言修改** - 用人类语言描述想要的修改
- 👁️ **实时预览** - 左右分屏对比原始和修改后的效果
- 📜 **修改历史** - 记录所有修改，支持回退和下载
- ⬇️ **一键下载** - 下载任意历史版本的 HTML 文件

## 🏗️ 技术栈

### 后端
- **Flask** - Python Web 框架
- **Flask-CORS** - 跨域支持
- **Requests** - HTTP 客户端
- **google-generativeai** - Gemini API SDK

### 前端
- **React 18** - 用户界面库
- **Axios** - HTTP 客户端
- **CSS3** - 现代样式设计

## 📋 先决条件

- Python 3.8+
- Node.js 16+
- npm 或 yarn
- 至少一个 LLM API 密钥（OpenRouter、OpenAI、Gemini 或 SiliconFlow）

## 🚀 快速开始

### 1. 克隆或下载项目后

```bash
cd html-editor-app
```

### 2. 配置 API 密钥

复制环境变量模板并填入您的 API 密钥：

```bash
cp .env.example .env
```

编辑 `.env` 文件，至少填入一个 API 密钥：

```env
# 选择您有密钥的服务
OPENROUTER_API_KEY=your_key_here
# 或
OPENAI_API_KEY=your_key_here
# 或
GOOGLE_API_KEY=your_key_here
# 或
SILICONFLOW_API_KEY=your_key_here
```

### 3. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 4. 安装前端依赖

```bash
cd ../frontend
npm install
```

### 5. 启动应用

#### 方式一：使用启动脚本（推荐）

在项目根目录运行：

```bash
chmod +x start.sh
./start.sh
```

#### 方式二：手动启动

**启动后端：**

```bash
cd backend
python app.py
```

后端将在 `http://localhost:8000` 运行

**启动前端（新终端）：**

```bash
cd frontend
npm start
```

前端将在 `http://localhost:3000` 自动打开浏览器

## 📖 使用指南

### 基本工作流程

1. **上传 HTML 文件**
   - 点击或拖放 HTML 文件到上传区域
   - 原始页面将在左侧预览

2. **选择 API 提供商和模型**
   - 在下拉菜单中选择您配置了密钥的提供商
   - 选择具体的模型（如 GPT-4o-mini、Gemini 等）

3. **输入修改指令**
   - 用自然语言描述您想要的修改
   - 例如："将背景色改为深色"、"增大标题字体"
   - 可以使用快速模板或自定义输入

4. **执行修改**
   - 点击"执行修改"按钮或按 Ctrl+Enter
   - 等待 AI 处理（通常 10-30 秒）
   - 修改后的页面将在右侧显示

5. **查看历史和回退**
   - 所有修改都会记录在历史面板
   - 点击"回退"可以恢复到任意历史版本
   - 点击"下载"可以保存特定版本

### 指令示例

**好的指令（推荐）：**
- ✅ "将主标题字体大小增加 50%"
- ✅ "把背景颜色改成柔和的浅蓝色"
- ✅ "为所有按钮添加 10px 的圆角"
- ✅ "增加段落之间的间距到 20px"
- ✅ "将导航栏设置为固定在顶部"

**避免的指令：**
- ❌ "修改代码"（太模糊）
- ❌ "让它更好看"（主观且不具体）
- ❌ "改"（没有说明改什么）

## 🔧 API 配置指南

### OpenRouter

1. 访问 [https://openrouter.ai/](https://openrouter.ai/)
2. 注册账号并获取 API 密钥
3. 将密钥填入 `OPENROUTER_API_KEY`

**推荐模型：**
- `openai/gpt-4o-mini` - 快速且经济
- `anthropic/claude-3.5-sonnet` - 高质量输出
- `google/gemini-2.0-flash-exp:free` - 免费选项

### OpenAI

1. 访问 [https://platform.openai.com/](https://platform.openai.com/)
2. 创建 API 密钥
3. 将密钥填入 `OPENAI_API_KEY`

**推荐模型：**
- `gpt-4o-mini` - 性价比高
- `gpt-4o` - 最强性能

### Google Gemini

1. 访问 [https://ai.google.dev/](https://ai.google.dev/)
2. 获取 API 密钥
3. 将密钥填入 `GOOGLE_API_KEY`

**推荐模型：**
- `gemini-2.0-flash-exp` - 快速且免费
- `gemini-1.5-pro` - 更强大的推理能力

### SiliconFlow

1. 访问 [https://siliconflow.cn/](https://siliconflow.cn/)
2. 注册并获取 API 密钥
3. 将密钥填入 `SILICONFLOW_API_KEY`

**推荐模型：**
- `deepseek-ai/DeepSeek-V3` - 强大的中文支持
- `Qwen/Qwen2.5-72B-Instruct` - 高性能

## 🗂️ 项目结构

```
html-editor-app/
├── backend/                 # Flask 后端
│   ├── app.py              # 主应用和路由
│   ├── api_clients.py      # API 客户端封装
│   ├── session_manager.py  # 会话管理
│   ├── html_processor.py   # HTML 处理工具
│   ├── config.py           # 配置管理
│   └── requirements.txt    # Python 依赖
├── frontend/               # React 前端
│   ├── public/            # 静态资源
│   ├── src/
│   │   ├── components/    # React 组件
│   │   ├── services/      # API 服务
│   │   ├── styles/        # CSS 样式
│   │   ├── App.js        # 主应用组件
│   │   └── index.js      # 入口文件
│   └── package.json       # Node 依赖
├── .env.example           # 环境变量模板
├── README.md              # 本文档
└── start.sh              # 启动脚本
```

## 🔌 API 端点

### 后端 REST API

- `POST /api/session` - 创建新会话
- `POST /api/upload` - 上传 HTML 文件
- `POST /api/modify` - 执行 HTML 修改
- `GET /api/history/<session_id>` - 获取修改历史
- `POST /api/revert` - 回退到指定版本
- `GET /api/current/<session_id>` - 获取当前 HTML
- `POST /api/download` - 下载 HTML 文件
- `GET /api/models/<provider>` - 获取可用模型列表
- `GET /api/health` - 健康检查

## 🎯 架构设计

### 扩展性设计

应用采用**两阶段处理架构**，为未来扩展预留接口：

#### 当前模式（直接模式）
```
用户指令 → LLM → 完整 HTML 代码
```

#### 未来扩展（解耦模式）
```
用户指令 → LLM → JSON 变更描述 → 代码生成器 → HTML/React/Vue
```

**预留字段：**
- 历史记录中的 `change_description` 字段
- API 响应中的 `metadata` 字段

这种设计可以支持：
- 多种输出格式（HTML、React JSX、Vue SFC）
- 降低 LLM 上下文消耗
- 批量应用修改
- 缓存变更意图

## ❓ 常见问题

### Q: 为什么修改没有生效？

A: 可能的原因：
1. API 密钥未配置或无效
2. 指令不够具体
3. 原始 HTML 结构复杂导致 LLM 理解困难
4. 网络问题导致请求超时

### Q: 支持哪些文件格式？

A: 目前仅支持 `.html` 和 `.htm` 格式的纯 HTML 文件。

### Q: 修改会覆盖原文件吗？

A: 不会。所有修改都在内存中进行，不会影响您的原始文件。

### Q: 可以同时使用多个 API 吗？

A: 可以。您可以配置多个 API 密钥，在使用时切换不同的提供商。

### Q: 历史记录会保存吗？

A: 历史记录仅在当前会话中保存（内存中），刷新页面会丢失。如需永久保存，请下载修改后的文件。

### Q: 如何提高修改质量？

A: 建议：
1. 使用清晰、具体的指令
2. 一次只修改一个方面
3. 尝试不同的模型
4. 对于复杂修改，分多步骤进行

## 🛠️ 开发

### 添加新的 API 提供商

1. 在 `backend/config.py` 中添加端点和密钥配置
2. 在 `backend/api_clients.py` 中实现客户端类
3. 在 `frontend/src/components/ApiSelector.js` 中添加 UI 选项
4. 在 `backend/app.py` 的 `/api/models/<provider>` 中添加模型列表

### 自定义样式

所有样式文件位于 `frontend/src/styles/` 目录，使用 CSS 变量便于主题定制。

## 📄 许可证

本项目仅供学习和研究使用。

## 🙏 致谢

- 基于 Instruct4Edit 项目的设计理念
- 使用 OpenRouter、OpenAI、Gemini、SiliconFlow 提供的强大 LLM 能力

## 📧 反馈与支持

如遇到问题或有建议，欢迎提交 Issue。

---

**享受智能化的网页编辑体验！** 🎉

