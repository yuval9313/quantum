import os
from uuid import uuid4

DATABASE_URL = os.getenv("DATABASE_URL", None)
if DATABASE_URL is None:
    raise ValueError("DATABASE_URL environment variable is not set")

REDIS_URL = os.getenv("REDIS_URL", None)
if REDIS_URL is None:
    raise ValueError("REDIS_URL environment variable is not set")

CONSUMER_ID = os.getenv("HOSTNAME", str(uuid4()))

MAX_RETRIES = int(os.getenv("MAX_RETRIES", "5"))
