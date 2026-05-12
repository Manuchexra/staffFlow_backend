import redis.asyncio as redis
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# ⚡ Redis client with connection pooling for performance
try:
    redis_client = redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        max_connections=20,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
        health_check_interval=30,
    )
    logger.info("✅ Redis client initialized successfully")
except Exception as e:
    logger.error(f"❌ Redis connection error: {e}")
    raise