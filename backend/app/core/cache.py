import json

import redis

from app.core.config import REDIS_CACHE_TTL_SECONDS, REDIS_KEY_PREFIX, REDIS_URL
from app.utils.log import get_logger

logger = get_logger(__name__)

try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
except Exception:
    logger.warning("redis_unavailable url=%s", REDIS_URL)
    redis_client = None


class Cache:
    def __init__(self):
        self.client = redis_client
        self.ttl = REDIS_CACHE_TTL_SECONDS
        self.prefix = REDIS_KEY_PREFIX

    def _key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    def get(self, key: str) -> str | None:
        if not self.client:
            return None
        try:
            return self.client.get(self._key(key))
        except Exception:
            logger.warning("redis_get_failed key=%s", key)
            return None

    def get_json(self, key: str) -> any:
        if not self.client:
            return None
        try:
            val = self.client.get(self._key(key))
            if val is None:
                return None
            return json.loads(val)
        except Exception:
            logger.warning("redis_get_json_failed key=%s", key)
            return None

    def set(self, key: str, value: str, ttl: int = None):
        if not self.client:
            return
        try:
            self.client.setex(self._key(key), ttl or self.ttl, value)
        except Exception:
            logger.warning("redis_set_failed key=%s", key)

    def set_json(self, key: str, value: any, ttl: int = None):
        if not self.client:
            return
        try:
            self.client.setex(self._key(key), ttl or self.ttl, json.dumps(value, ensure_ascii=False))
        except Exception:
            logger.warning("redis_set_json_failed key=%s", key)

    def delete(self, key: str):
        if not self.client:
            return
        try:
            self.client.delete(self._key(key))
        except Exception:
            logger.warning("redis_delete_failed key=%s", key)

    def exists(self, key: str) -> bool:
        if not self.client:
            return False
        try:
            return bool(self.client.exists(self._key(key)))
        except Exception:
            logger.warning("redis_exists_failed key=%s", key)
            return False


cache = Cache()
