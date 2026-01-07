# core/db.py
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from app.core.config import settings

def get_engine() -> Engine:
    return create_engine(settings.postgres_dsn, pool_pre_ping=True)

def init_schema(engine: Engine) -> None:
    ddl = """
    CREATE TABLE IF NOT EXISTS ad_events(
      event_id TEXT PRIMARY KEY,
      event_type TEXT NOT NULL,
      ts_ms BIGINT NOT NULL,
      user_id TEXT NOT NULL,
      campaign_id TEXT NOT NULL,
      adgroup_id TEXT NOT NULL,
      channel TEXT NOT NULL,
      geo TEXT,
      cost_usd DOUBLE PRECISION NOT NULL,
      revenue_usd DOUBLE PRECISION NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_ad_events_user_ts ON ad_events(user_id, ts_ms);

    CREATE TABLE IF NOT EXISTS attribution_credits(
      id BIGSERIAL PRIMARY KEY,
      ts_ms BIGINT NOT NULL,
      conversion_event_id TEXT NOT NULL,
      credited_campaign_id TEXT NOT NULL,
      credit DOUBLE PRECISION NOT NULL
    );
    """
    with engine.begin() as conn:
        for stmt in ddl.split(";"):
            s = stmt.strip()
            if s:
                conn.execute(text(s))