# -*- coding: utf-8 -*-
"""
@File    : mcp_config
@Project : TraceAgentic_RAG
@Author  : Rudy
@Date    : 2026/5/15 19:50
@Desc    : 

Copyright (c) 2026 Rudy. All rights reserved.
"""
import json
import os
import re
from typing import Dict, Any

from app.utils.log import get_logger

logger = get_logger(__name__)


class MCPConfig:
    def __init__(self):
        # 直接指向 mcp 目录下的 json
        self.config_path = os.path.join(os.path.dirname(__file__), "mcp_servers.json")
        self._config: Dict = {}

    # 加载并解析 json配置
    def load(self) -> Dict[str, Any]:
        if not os.path.exists(self.config_path):
            logger.warning(f"MCP 配置文件不存在: {self.config_path}")
            return {}

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                # 转为python字典
                raw = json.load(f)

            self._config = self._replace_env(raw)
            logger.info(f"MCP 配置加载成功: {list(self._config.keys())}")
            return self._config
        except Exception as exc:
            logger.error(f"加载 MCP 配置失败: {exc}")
            return {}

    # 递归遍历数据结构
    def _replace_env(self, data):
        if isinstance(data, dict):
            return {k: self._replace_env(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._replace_env(i) for i in data]
        if isinstance(data, str):
            # 替换字符串中所有 ${VAR}
            def _sub(m):
                return os.getenv(m.group(1), "")

            return re.sub(r'\$\{(\w+)\}', _sub, data)
        return data

    def get_servers(self) -> Dict[str, Dict]:
        """返回 MultiServerMCPClient 可用的配置"""
        servers = {}
        for name, cfg in self._config.items():
            if cfg.get("enabled", False):
                server_cfg = {k: v for k, v in cfg.items() if k != "enabled"}
                servers[name] = server_cfg
        return servers