import asyncio
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from app.mcp_gateway.mcp_config import MCPConfig
from app.utils.log import get_logger

load_dotenv()
logger = get_logger(__name__)


class MCPClientManager:
    def __init__(self):
        self._tools = []
        self._initialized = False
        self.mcp_config = MCPConfig()

    async def initialize(self):
        if self._initialized:
            return
        self._initialized = True


        self.mcp_config.load()
        servers = self.mcp_config.get_servers()

        if not servers:
            logger.warning("没有启用的 MCP 服务")
            return

        try:
            client = MultiServerMCPClient(servers)
            self._tools = await client.get_tools()

            tool_names = [t.name for t in self._tools]
            logger.info(f"MCP 工具加载完成，共 {len(self._tools)} 个 |{tool_names})")

        except Exception as exc:
            logger.error("MCP 初始化失败: %s", exc)


    # 供agent使用
    async def get_agent_tools(self):
        await self.initialize()
        return list(self._tools)


mcp_client_manager = MCPClientManager()

if __name__ == '__main__':
    print("正在测试 MCP 工具列表...\n")
    tools = asyncio.run(mcp_client_manager.get_agent_tools())
    if tools:
        print(f"{len(tools)} tools found")
        for tool in sorted(tools, key=lambda t: t.name):
            print(f"{tool.name}: {tool.description}")


