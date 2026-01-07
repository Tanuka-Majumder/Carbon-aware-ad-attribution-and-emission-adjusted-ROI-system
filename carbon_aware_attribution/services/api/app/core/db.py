from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from app.core.config import settings

def get_engine() -> Engine:
    return create_engine(settings.postgres_dsn, pool_pre_ping=True)