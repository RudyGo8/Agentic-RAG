# TraceAgentic RAG —— 多步自主知识智能体

基于多步推理的自主知识 Agent，能高精度检索知识库并跟踪溯源、能干活查数据库和Github并得到的订单表数据分析

> **解决痛点**：企业中智能体检索知识库时幻觉严重——单一检索命中率低、语义漂移导致答非所问、无决策追溯无法排查。本项目通过 **HyDE 假设文档扩展 + StepBack 反向抽象 + 多步 Agent 自主推理 + 全链路可观测**，从检索深度和召回广度两个维度压制幻觉。

**技术栈**
- 后端：FastAPI + LangChain Agent + LangSmith + Milvus + MySQL + Redis
- 前端：Vue 3 + Vite + Element Plus
- 流式：SSE（`content` / `rag_step` / `trace` / `[DONE]`）
- 工具调用：Function Tool（内置 RAG 检索）+ MCP（Git / MySQL，可按需扩展）

---

## 更新日志

### 2026-05-15 (v0.2.2)

- **数据分析助手**：prompt 新增【运营数据规则】 、SQL模版、时间解析表
- **前端渲染**：ECharts图表展示


### 2026-04-15 (v0.2.1)

- **日志体系重构**：迁移至 structlog，开发彩色/生产 JSON 双模式，三方库噪音压制
- **日志配置解耦**：从 `config.py` 拆出独立 `app/utils/log.py`，环境变量控制
- **MCP网关服务**：添加 Gateway 入口，服务器配置改为独立 JSON 文件，扩展性强

### 2026-02（v0.2）

- **RAG 流水线重写**：四阶段检索/评分/重写/扩展，HyDE + StepBack + AutoMerge
- **Embedding 统一**：统一嵌入接口，小叶级检索 + 自动合并
- **可观测流式**：SSE 新增 `rag_step` 进度 + `trace` 决策追溯

### 2025-06 / 2025-10（v0.1）

- **MCP 工具集成**：Git / MySQL（只读），`MCP_SERVERS_JSON` 环境变量驱动
- **Agentic RAG 基础**：FastAPI + Agent + Milvus 搭建
- **JWT 认证 + 文档管理 + 会话持久化**

---

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

### 在线可观测

- **LangSmith** 全链路追踪：每次 Agent 调用自动记录 prompt、检索步骤、工具调用、最终回答
- **SSE `trace` 事件**：前端实时展示检索元数据，可回溯每次决策

---

## 快速开始

```bash
# 1. 启动基础服务
cd backend && docker compose up -d      # MySQL + Redis + Milvus

# 2. 配置环境变量
cp backend/.env.example backend/.env    # 填 ARK_API_KEY 等必填项

# 3. 后端
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 4. 前端
cd frontend
npm install && npm run dev
```
