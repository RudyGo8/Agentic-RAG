# 更新日志

本文件记录项目的显著变更。格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/)。

## [0.2.3] - 2026-05-31

- **MCP 热插拔**：生命周期添加后台任务，监听 mcp_json 文件，有变动就初始化 mcp 服务，返回所有工具
- **单服务隔离加载**：单个 mcp 服务挂了不影响全局 mcp 服务

## [0.2.2] - 2026-05-15

- **数据分析助手**：prompt 新增【运营数据规则】、SQL 模版、时间解析表
- **前端渲染**：ECharts 图表展示

## [0.2.1] - 2026-04-15

- **日志体系重构**：迁移至 structlog，开发彩色/生产 JSON 双模式，三方库噪音压制
- **日志配置解耦**：从 `config.py` 拆出独立 `app/utils/log.py`，环境变量控制
- **MCP 网关服务**：添加 Gateway 入口，服务器配置改为独立 JSON 文件，扩展性强

## [0.2] - 2026-02

- **RAG 流水线重写**：四阶段检索/评分/重写/扩展，HyDE + StepBack + AutoMerge
- **Embedding 统一**：统一嵌入接口，小叶级检索 + 自动合并
- **可观测流式**：SSE 新增 `rag_step` 进度 + `trace` 决策追溯

## [0.1] - 2025-06 / 2025-10

- **MCP 工具集成**：Git / MySQL（只读），`MCP_SERVERS_JSON` 环境变量驱动
- **Agentic RAG 基础**：FastAPI + Agent + Milvus 搭建
- **JWT 认证 + 文档管理 + 会话持久化**
