from redis import Redis

class IdempotencyStore:
    """
    Redis-backed idempotency keys.
    Ensures exactly-once effects in a >= once stream.
    """
    def __init__(self, r: Redis, ttl_s: int):
        self.r = r
        self.ttl_s = ttl_s

    def seen(self, key: str) -> bool:
        return self.r.exists(f"idem:{key}") == 1

    def mark(self, key: str) -> None:
        self.r.setex(f"idem:{key}", self.ttl_s, "1")