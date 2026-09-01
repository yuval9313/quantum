import os
from uuid import uuid4

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/quantom")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CONSUMER_ID = os.getenv("HOSTNAME", str(uuid4()))
