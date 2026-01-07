

from pathlib import Path
from joblib import load
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://app:app@postgres:5432/attribution"
    @property
    def postgres_dsn(self):
        return self.DATABASE_URL

settings = Settings()

MODEL_PATH = Path("/app/data/conv_model.joblib")

_model = None

def get_model():
    global _model
    if _model is None:
        if not MODEL_PATH.exists():
            raise RuntimeError("Model file not found at /app/data/conv_model.joblib")
        _model = load(MODEL_PATH)
    return _model