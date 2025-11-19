# 🎛️ 复杂任务界面生成 & 自然语言编辑 MVP

一个用于论文原型的内部设计工具 demo：输入任务描述 / Persona / 组件库，即可生成多页面栅格布局，并用自然语言指令进行 UI-diff 级别的可控编辑。

## ✨ 亮点功能（V0.1）

- **F1 任务上下文**：任务需求 + Persona + 场景模板 + 组件库 JSON，内置多套 Persona/场景/组件库，可一键预览摘要。
- **F2 多阶段生成**：根据场景自动拆解 2–3 个 Page，组装 Section → 组件 → 布局，支持 12 栅格启发式排版，并暴露 Priority Queue 调试视图。
- **F3 自然语言编辑**：内置指令解析器（Add/Remove/Move/Update），生成 UI-diff JSON 并落地到 Schema，自动处理列宽冲突、标注修改组件。
- **F4 跨页面一致性**：指令中提到“保持一致 / 所有 XX”，会根据 role 扩散到同名组件，模拟 role-based propagation。
- **F5 调试 & 导出**：研究模式展示 Priority Queue、UI-diff 历史、上下文摘要，支持一键导出 Schema JSON，用于后续前端工程或论文附录。

## 🧱 技术架构

| 层 | 技术 | 说明 |
| --- | --- | --- |
| 前端 | React 18 + Axios + 自定义 CSS | 三列工作台：任务输入 / 预览 & 编辑 / 调试视图 |
| 后端 | Flask + 内存 SessionManager | Schema 生成器 + 指令解析 / diff 引擎 |
| 数据 | JSON Schema | Page/Section/Component、PriorityQueue、UI-diff 结构均在 `backend/data` 内定义模板 |

核心模块：
- `backend/schema_generator.py`：根据场景模板与任务文本生成 Stage plan、PriorityQueue 与 UI Schema。
- `backend/diff_engine.py`：基于规则的指令解析器，输出 Add/Remove/Update/Reorder diff，并负责冲突处理。
- `backend/session_manager.py`：管理上下文、Schema、undo 栈和 diff 历史。

## 🚀 快速开始

1. **安装依赖**
   ```bash
   cd backend && pip install -r requirements.txt
   cd ../frontend && npm install
   ```
2. **启动服务**
   ```bash
   # 终端 A
   cd backend
   python app.py  # 默认 http://localhost:5000

   # 终端 B
   cd frontend
   npm start  # 默认 http://localhost:3000
   ```
   > 也可执行 `./start.sh` 同时拉起前后端。

## 🧭 使用流程

1. **配置上下文（F1）**
   - 粘贴任务描述（可包含多段文本）
   - 选择 Persona & 场景模板，或补充 Persona 的关注点
   - 如需自定义组件库，粘贴数组 JSON；否则使用内置库
   - 点击“同步上下文”后，可看到 Persona / 任务 / 组件统计摘要

2. **生成界面族（F2）**
   - 点击“生成界面族”，系统按照 Stage 模板拆分 Page
   - 每个 Page 自动划分 Section，并从组件库检索匹配组件
   - 预览区展示 12 栅格布局、每个 Section 的组件占位及信息绑定

3. **自然语言编辑（F3/F4）**
   - 在指令框输入需求，例如：
     - “在监控页面顶部增加一个 KPI 卡片突出系统健康度”
     - “把告警列表移到右侧栏并缩窄宽度”
     - “让所有过滤条改成双行布局保持一致”
   - 系统会生成 UI-diff，自动高亮受影响组件，并记录日志/警告
   - 支持“撤销一步”和“导出 Schema”

4. **调试视图（F5）**
   - 右侧面板显示 Priority Queue 前 10 个信息项
   - 展示 UI-diff 历史记录、角色/场景摘要，便于论文实验记录

## 📦 数据结构速览

```ts
type Component = {
  id: string;
  role?: string;           // GlobalFilterBar, AlertTable...
  type: string;            // Table / Chart / CardRow...
  dataRole: string;
  layout: { colSpan: number; order: number };
  style: { density?: 'low'|'medium'|'high'; emphasis?: 'normal'|'highlight' };
  infoRefs: string[];
};

type Section = {
  id: string;
  role: 'header'|'main'|'sidebar'|'footer';
  layout: { row: number; colStart: number; colSpan: number; order: number };
  components: Component[];
};

type Page = {
  id: string;
  name: string;
  stage: string;
  description: string;
  sections: Section[];
};

type UIDiff = {
  scope: 'current_page' | 'same_role_across_pages';
  operations: Operation[];
};
```

更多模板与默认组件参考 `backend/data/defaults.py`。

## 🧪 指令解析覆盖的语义

- `add` / `增加` / `新增` → 在指定页面 & 区域添加组件并生成默认 layout
- `delete` / `删除` / `移除` → 根据角色或上下文定位组件并移除
- `move` / `移动` / `挪到` → 通过新的 section 关键字（顶部 / 右侧等）移动组件
- `缩小` / `放大` → 调整组件 `colSpan` 并适配 12 栅格
- 含“所有/一致/跨页面” → 自动进入 `same_role_across_pages` 范围，复制 style/layout

若指令无法解析会给出 warning，避免 silent failure。

## 🏁 目前限制（与需求文档一致）

- 仅支持 Web 桌面端栅格布局，不包含 XR/移动端
- 指令解析基于规则+模板，未接入真实 LLM（可在 V1.1 接入 LoRA / Instruct4Edit）
- 布局优化为启发式得分，接口层面预留 NSGA-II 可能性
- 数据暂存于内存，关闭进程后会话重置

欢迎在 `frontend/src/components/*` 或 `backend/*.py` 中扩展更多场景、组件与指令规则。

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
