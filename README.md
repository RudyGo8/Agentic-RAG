# ZhiYuan Agentic RAG

An agentic RAG project with separate backend and frontend:

- Backend: FastAPI + Agent + RAG + Milvus + MySQL + Redis
- Frontend: Vue 3 + Vite
- Streaming: SSE (`content`, `rag_step`, `trace`, `[DONE]`)
- Optional MCP sources: `git`, `mysql` (read-only)

---

## 1. Project Structure

```text
2.Rag_Agent/
  backend/
    app/
      agent/                 # agent runtime / prompt / tracing
      rag/                   # RAG graph + nodes + retrieval services
      routes/common/         # auth/chat/document/version APIs
      mcp/                   # MCP client + wrappers + local mysql MCP server
      tools/                 # tool registry + tool runtime guards
  frontend/
    src/
      views/                 # main workspace UI
      components/            # auth/chat/history/document components
      services/              # API + SSE consumers
```

---

## 2. Core Capabilities

- JWT auth (`register`, `login`, `me`)
- Session history (`list`, `load`, `delete`)
- Document management
  - Single upload: `/api/r1/documents/upload`
  - Batch upload: `/api/r1/documents/batch-upload`
  - Delete vectors by filename
- Agentic chat with SSE stream
- RAG retrieval pipeline (retrieve / grade / rewrite / expand)
- Traceability
  - `rag_step` for real-time progress
  - `trace` for final retrieval/tool usage metadata
- Optional MCP tools
  - `mcp_search_git`
  - `mcp_search_mysql`

---

## 3. Prerequisites

- Python 3.10+
- Node.js 18+
- Docker Desktop (for MySQL / Redis / Milvus stack)

---

## 4. Start Dependencies

```bash
cd backend
docker compose up -d
```

Services in `backend/docker-compose.yml`:

- MySQL
- Redis
- Milvus (etcd + minio + standalone + attu)

---

## 5. Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 6. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

---

## 7. Environment Variables

Configure `backend/.env`.

### Required (typical local)

- `ARK_API_KEY`
- `MODEL`
- `BASE_URL`
- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_USERNAME`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`
- `REDIS_URL`
- `MILVUS_HOST`
- `MILVUS_PORT`
- `MILVUS_COLLECTION`
- `JWT_SECRET_KEY`

### Agent / RAG

- `AGENT_RECURSION_LIMIT` (default `16`, min effective `8`)
- `AUTO_MERGE_ENABLED`
- `AUTO_MERGE_THRESHOLD`
- `LEAF_RETRIEVE_LEVEL`

### MCP (optional)

- `MCP_ENABLED=true|false`
- `MCP_SERVERS_JSON=<json>`
- `MCP_TOOL_TIMEOUT_SECONDS` (default `12`)

Example `MCP_SERVERS_JSON` with local MySQL MCP server:

```json
{
  "mysql-local": {
    "transport": "stdio",
    "command": "python",
    "args": ["app/mcp/mysql_mcp_server.py"]
  }
}
```

Add your Git MCP server entry in the same JSON when needed.

---

## 8. API Overview

### Auth

- `POST /api/r1/auth/register`
- `POST /api/r1/auth/login`
- `GET /api/r1/auth/me`

### Chat

- `POST /api/r1/chat/stream` (SSE)
- `GET /api/r1/chat/sessions`
- `GET /api/r1/chat/sessions/{session_id}`
- `DELETE /api/r1/chat/sessions/{session_id}`

### Documents

- `GET /api/r1/documents`
- `POST /api/r1/documents/upload`
- `POST /api/r1/documents/batch-upload`
- `DELETE /api/r1/documents/{filename}`

### Version

- `GET /api/r1/version/version`

---

## 9. Batch Upload Response

`POST /api/r1/documents/batch-upload` returns:

```json
{
  "total": 3,
  "succeeded": 2,
  "failed": 1,
  "results": [
    {
      "filename": "a.pdf",
      "success": true,
      "chunks_processed": 12,
      "message": "Uploaded a.pdf, processed 12 chunks"
    },
    {
      "filename": "b.docx",
      "success": false,
      "chunks_processed": 0,
      "message": "..."
    }
  ],
  "message": "Batch upload completed: 2 succeeded, 1 failed"
}
```

---

## 10. SSE Event Contract

`/api/r1/chat/stream` emits:

- `{"type":"content","content":"..."}`
- `{"type":"rag_step","step":{"icon":"...","label":"...","detail":"..."}}`
- `{"type":"trace","rag_trace":{...}}`
- `data: [DONE]`

---

## 11. Notes

- Keep route/service/schema boundaries clear when extending features.
- Do not put retrieval orchestration logic into frontend.
- Keep SSE event names stable to avoid frontend regressions.
