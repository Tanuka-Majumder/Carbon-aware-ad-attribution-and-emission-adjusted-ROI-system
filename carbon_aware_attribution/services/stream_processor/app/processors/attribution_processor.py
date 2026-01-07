from dataclasses import dataclass
from sqlalchemy import text
from sqlalchemy.engine import Engine
from redis import Redis

from app.schemas import AdEvent
from app.processors.idempotency import IdempotencyStore

@dataclass(frozen=True)
class ProcessorDeps:
    engine: Engine
    redis: Redis
    idem: IdempotencyStore

class AttributionProcessor:
    """
    Writes events to warehouse (Postgres) and maintains online aggregates (Redis).
    Also computes *streaming* attribution credits (simple baseline).
    """
    def __init__(self, deps: ProcessorDeps):
        self.deps = deps

    def process(self, ev: AdEvent) -> None:
        if self.deps.idem.seen(ev.event_id):
            return

        # 1) Persist raw event (append-only)
        self._insert_event(ev)

        # 2) Update online counters
        self._update_redis(ev)

        # 3) Streaming attribution (baseline): last-touch credit on conversion
        if ev.event_type == "conversion":
            self._last_touch_credit(ev)

        self.deps.idem.mark(ev.event_id)

    def _insert_event(self, ev: AdEvent) -> None:
        q = text("""
        INSERT INTO ad_events(event_id, event_type, ts_ms, user_id, campaign_id, adgroup_id,
                             channel, geo, cost_usd, revenue_usd)
        VALUES (:event_id, :event_type, :ts_ms, :user_id, :campaign_id, :adgroup_id,
                :channel, :geo, :cost_usd, :revenue_usd)
        ON CONFLICT (event_id) DO NOTHING
        """)
        with self.deps.engine.begin() as conn:
            conn.execute(q, ev.model_dump())

    def _update_redis(self, ev: AdEvent) -> None:
        r = self.deps.redis
        # per-campaign near-real-time metrics
        key = f"rt:campaign:{ev.campaign_id}"
        pipe = r.pipeline()
        pipe.hincrbyfloat(key, "cost_usd", float(ev.cost_usd))
        if ev.event_type == "conversion":
            pipe.hincrby(key, "conversions", 1)
            pipe.hincrbyfloat(key, "revenue_usd", float(ev.revenue_usd))
        elif ev.event_type == "click":
            pipe.hincrby(key, "clicks", 1)
        elif ev.event_type == "impression":
            pipe.hincrby(key, "impressions", 1)
        pipe.execute()

    def _last_touch_credit(self, ev: AdEvent) -> None:
        """
        Baseline: give 100% credit to the last click from same user in last N days (here: 7d).
        If none, fallback to current conversion's campaign.
        """
        with self.deps.engine.begin() as conn:
            q = text("""
            SELECT campaign_id
            FROM ad_events
            WHERE user_id = :user_id
              AND event_type = 'click'
              AND ts_ms <= :ts_ms
              AND ts_ms >= :ts_ms - (7 * 24 * 3600 * 1000)
            ORDER BY ts_ms DESC
            LIMIT 1
            """)
            row = conn.execute(q, {"user_id": ev.user_id, "ts_ms": ev.ts_ms}).fetchone()

        credited_campaign = row[0] if row else ev.campaign_id

        with self.deps.engine.begin() as conn:
            conn.execute(
                text("""
                INSERT INTO attribution_credits(ts_ms, conversion_event_id, credited_campaign_id, credit)
                VALUES (:ts_ms, :conversion_event_id, :credited_campaign_id, :credit)
                """),
                {
                    "ts_ms": ev.ts_ms,
                    "conversion_event_id": ev.event_id,
                    "credited_campaign_id": credited_campaign,
                    "credit": 1.0,
                }
            )