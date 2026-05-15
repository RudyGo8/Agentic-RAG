import os

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

from app.utils.log import get_logger

load_dotenv()
logger = get_logger(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_PAT_TOKEN", "")
MCP_URL = "https://api.githubcopilot.com/mcp/"

class MCPClientManager:
    def __init__(self):
        self._tools = []

    async def initialize(self):
        if not GITHUB_TOKEN:
            logger.info("MCP skipped: no GITHUB_PAT_TOKEN")
            return
        try:
            # 连接 mcp 服务：远程
            client = MultiServerMCPClient({
                "github": {
                    "transport": "streamable_http",
                    "url": MCP_URL,
                    "headers": {"Authorization": f"Bearer {GITHUB_TOKEN}"},
                }
            })
            self._tools = await client.get_tools()
            logger.info("GitHub MCP loaded tools=%s", [t.name for t in self._tools])
        except Exception as exc:
            logger.warning("GitHub MCP init failed err=%s", exc)

    async def get_agent_tools(self):
        await self.initialize()
        return list(self._tools)


mcp_client_manager = MCPClientManager()
