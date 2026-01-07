from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, Any
import time

EventType = Literal["impression", "click", "conversion"]

class AdEvent(BaseModel):
    event_id: str = Field(..., description="Globally unique id for idempotency")
    event_type: EventType
    ts_ms: int = int(time.time() * 1000)

    user_id: Optional[str] = "anonymous"
    campaign_id: Optional[str] = "unknown_campaign"
    adgroup_id: Optional[str] = "unknown_adgroup"
    channel: str  # e.g., 'search', 'social', 'display'
    geo: Optional[str] = None

    cost_usd: float = 0.0
    revenue_usd: float = 0.0  # set for conversions

    # Optional payload
    attrs: Dict[str, Any] = {}