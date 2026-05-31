import asyncio

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

from app.tools.mcp_gateway.mcp_config import MCPConfig
from app.utils.log import get_logger

load_dotenv()
logger = get_logger(__name__)


class MCPClientManager:
    def __init__(self):
        self._tools = []
        self._initialized = False
        self._lock = asyncio.Lock()
        self._last_config_mtime = 0.0
        self.mcp_config = MCPConfig()

    async def initialize(self):
        # 避免初始化和reload并发冲突
        async with self._lock:
            if self._initialized:
                return

            self._initialized = True
            self.mcp_config.load()
            self._last_config_mtime = self.mcp_config.get_mtime()
            servers = self.mcp_config.get_servers()

            if not servers:
                self._tools = []
                logger.warning("No enabled MCP servers")
                return

            # 单服务隔离，某个服务挂了不影响其他的mcp 服务
            tools = []
            for name, server_cfg in servers.items():
                try:
                    server_tools = await MultiServerMCPClient({name: server_cfg}).get_tools()
                    tools.extend(server_tools)
                    logger.info("MCP server loaded: name=%s count=%s", name, len(server_tools))
                except Exception as exc:
                    logger.error("MCP server failed: name=%s error=%s", name, exc)

            self._tools = tools
            logger.info("MCP tools loaded: count=%s names=%s", len(self._tools), [t.name for t in self._tools])
    # 加载
    async def reload(self):
        async with self._lock:
            self._initialized = False
            self._tools = []

        await self.initialize()
        return list(self._tools)

    # 每30秒检查配置文件是否变更，变了就reload
    async def watch_config_loop(self, interval_seconds: int = 30):
        await self.initialize()

        while True:
            await asyncio.sleep(interval_seconds)
            current_mtime = self.mcp_config.get_mtime()
            if current_mtime and current_mtime != self._last_config_mtime:
                logger.info("MCP config changed; reloading tools")
                await self.reload()

    async def get_agent_tools(self):
        await self.initialize()
        return list(self._tools)


mcp_client_manager = MCPClientManager()


if __name__ == "__main__":
    print("Testing MCP tools...\n")
    tools = asyncio.run(mcp_client_manager.get_agent_tools())
    if tools:
        print(f"{len(tools)} tools found")
        for tool in sorted(tools, key=lambda t: t.name):
            print(f"{tool.name}: {tool.description}")
