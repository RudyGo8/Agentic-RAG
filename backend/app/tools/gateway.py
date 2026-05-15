from app.mcp_gateway.client_manager import mcp_client_manager
from app.tools.registry import TOOL_REGISTRY


# 工具网关-统一入口
class ToolGateway:

    def __init__(self, registry, mcp_manager):
        self._registry = registry
        self._mcp = mcp_manager

    async def get_tools(self):
        local = [spec.tool for spec in self._registry.values()]
        mcp = await self._mcp.get_agent_tools()
        return local + mcp

    async def get_mcp_tool_names(self):
        tools = await self._mcp.get_agent_tools()
        # 字典推导式：安全获取属性
        return {getattr(t, "name", "").strip() for t in tools if getattr(t, "name", None)}


tool_gateway = ToolGateway(TOOL_REGISTRY, mcp_client_manager)
