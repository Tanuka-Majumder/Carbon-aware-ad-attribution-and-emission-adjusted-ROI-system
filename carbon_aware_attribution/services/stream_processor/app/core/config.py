from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "local"

    kafka_bootstrap: str
    kafka_topic_events: str = "ad_events"
    kafka_consumer_group: str = "attribution-stream-v1"

    postgres_dsn: str
    redis_url: str

    # Stream processing knobs
    max_batch_messages: int = 500
    poll_timeout_s: float = 1.0
    idempotency_ttl_s: int = 7 * 24 * 3600

settings = Settings()