'''
@create_time: 2025/09/03
@Author: GeChao
@File: config.py
'''
import os
from dotenv import load_dotenv

load_dotenv()

MYSQL_USERNAME = os.getenv("MYSQL_USERNAME", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "123456")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3308"))
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "rag_mysql")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_KEY_PREFIX = os.getenv("REDIS_KEY_PREFIX", "rag_agent")
REDIS_CACHE_TTL_SECONDS = int(os.getenv("REDIS_CACHE_TTL_SECONDS", "300"))

MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
MILVUS_COLLECTION = os.getenv("MILVUS_COLLECTION", "rag_embeddings")

ARK_API_KEY = os.getenv("ARK_API_KEY", "")
MODEL = os.getenv("MODEL")
BASE_URL = os.getenv("BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
EMBEDDER = os.getenv("EMBEDDER", "text-embedding-v2")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1536"))
GRADE_MODEL = os.getenv("GRADE_MODEL", "qwen-plus")

AUTO_MERGE_ENABLED = os.getenv("AUTO_MERGE_ENABLED", "true")
AUTO_MERGE_THRESHOLD = os.getenv("AUTO_MERGE_THRESHOLD", "2")
LEAF_RETRIEVE_LEVEL = os.getenv("LEAF_RETRIEVE_LEVEL", "3")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))
ADMIN_INVITE_CODE = os.getenv("ADMIN_INVITE_CODE", "")
PASSWORD_PBKDF2_ROUNDS = int(os.getenv("PASSWORD_PBKDF2_ROUNDS", "310000"))

MCP_ENABLED = os.getenv("MCP_ENABLED", "false").lower() == "true"

AGENT_RECURSION_LIMIT = max(8, int(os.getenv("AGENT_RECURSION_LIMIT", "16")))
