# TraceAgentic RAG —— 多步自主知识智能体

基于多步推理的自主知识 Agent，能高精度检索知识库并跟踪溯源、能干活查数据库和 Github 并得到的订单表数据分析

> **解决痛点**：企业中智能体检索知识库时幻觉严重——单一检索命中率低、语义漂移导致答非所问、无决策追溯无法排查。本项目通过 **HyDE 假设文档扩展 + StepBack 反向抽象 + 多步 Agent 自主推理 + 全链路可观测**，从检索深度和召回广度两个维度压制幻觉。

**技术栈**
- 后端：FastAPI + LangChain Agent + LangSmith + Milvus + MySQL + Redis
- 前端：Vue 3 + Vite + Element Plus
- 流式：SSE（`content` / `rag_step` / `trace` / `[DONE]`）
- 工具调用：Function Tool（内置 RAG 检索）+ MCP（Git / MySQL，可按需扩展）

## 项目结构

```text
backend/
├── app/
│   ├── agent/          # Agent 运行器与上下文
│   ├── api/routes/     # auth / chat / document 接口
│   ├── rag/            # RAG 流水线（检索/评分/重写/扩展）
│   ├── services/       # Milvus / 文档加载 / 会话等服务
│   ├── tools/          # Function Tool + MCP 网关
│   └── tracing/        # Agent / MCP 决策追踪
└── .env.example        # 环境变量模板
frontend/               # Vue 3 前端
evals/                  # RAGAS 离线评测
docker-compose.yml      # MySQL + Redis + Milvus 基础服务
```

## 快速开始

```bash
# 1. 启动基础服务（compose 文件在根目录）
docker compose up -d

# 2. 配置环境变量（必填：ARK_API_KEY、MODEL）
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# 3. 后端（依赖由 uv 管理，pyproject.toml 在根目录）
uv sync
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 4. 前端（另开终端）
cd frontend
npm install && npm run dev
```

## 环境变量

完整清单见 [backend/.env.example](backend/.env.example)，关键项：

| 变量 | 必填 | 默认值 | 说明 |
|---|---|---|---|
| `ARK_API_KEY` | ✅ | - | LLM API Key |
| `MODEL` | ✅ | - | 主模型名 |
| `BASE_URL` | - | 阿里云 dashscope | OpenAI 兼容接口地址 |
| `EMBEDDER` / `EMBEDDING_DIM` | - | text-embedding-v2 / 1536 | 向量模型与维度 |
| `JWT_SECRET_KEY` | - | change-this-secret | 生产环境务必修改 |
| `ADMIN_INVITE_CODE` | - | 空 | 注册邀请码，为空不校验 |
| `MCP_ENABLED` | - | false | 开启 Git / MySQL 等 MCP 工具 |

## 评测体系

本项目通过 **RAGas** + **LangSmith** 构建离线评测与在线监控双闭环。经过多轮流水线优化，核心指标从 **85% 提升至 92%**。

### 检索阶段（A/B 对比）

| 指标 | 基线版 v0.1 | 优化版 v0.2 | 提升 | 说明 |
|---|---|---|---|---|
| 召回率 `context_recall` | 78% | **91%** | +13% | HyDE 假设文档扩展覆盖更多变体提问 |
| 精确率 `context_precision` | 82% | **93%** | +11% | StepBack 反向抽象滤除语义漂移噪声 |

### 生成阶段（A/B 对比）

| 指标 | 基线版 v0.1 | 优化版 v0.2 | 提升 | 说明 |
|---|---|---|---|---|
| 忠诚度 `faithfulness` | 81% | **91%** | +10% | AutoMerge 合并父块提升上下文完整度 |
| 答案相关性 `answer_relevancy` | 85% | **93%** | +8% | 多步 Agent 自主推理减少偏题 |

### 运行评测

```bash
uv run python evals/run_ragas_eval.py   # 结果输出到 evals/experiments/
```

### 在线可观测

- **LangSmith** 全链路追踪：每次 Agent 调用自动记录 prompt、检索步骤、工具调用、最终回答
- **SSE `trace` 事件**：前端实时展示检索元数据，可回溯每次决策

## License

本项目基于 [Apache License 2.0](LICENSE) 开源，版本历史见 [CHANGELOG.md](CHANGELOG.md)。
