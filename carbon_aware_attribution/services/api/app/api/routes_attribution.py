from fastapi import APIRouter, Depends
from sqlalchemy.engine import Engine
from redis import Redis

from app.core.db import get_engine
from app.core.redis import get_redis
from app.models.attribution import AttributionModel
from sqlalchemy import text
from app.models.anomaly import RobustZScoreAnomaly
from app.models.budget_optimizer import EmissionAdjustedBudgetOptimizer, Campaign

router = APIRouter()

def eng() -> Engine:
    return get_engine()

def rds() -> Redis:
    return get_redis()

@router.get("/attribution/channels")
def channel_attribution(engine: Engine = Depends(eng)):
    model = AttributionModel(engine)
    return {"channel_weights": model.compute_channel_attribution()}

# New endpoint: Channel-level KPIs
@router.get("/metrics/channels")
def channel_kpis(engine: Engine = Depends(eng)):
    # Aggregate per channel: emissions, conversions, revenue, cost
    with engine.begin() as conn:
        rows = conn.execute(text("""
            SELECT channel,
                   SUM(CASE WHEN event_type='conversion' THEN 1 ELSE 0 END) AS conversions,
                   SUM(cost_usd) AS cost_usd,
                   SUM(revenue_usd) AS revenue_usd,
                   COUNT(*) AS events
            FROM ad_events
            GROUP BY channel
        """)).fetchall()
    # Estimate emissions using lookup table (same as dashboard)
    emissions_g = {
        "email": 0.3,
        "display": 1.2,
        "search": 1.0,
        "video": 3.5,
        "social": 2.0,
        "tiktok": 2.8,
        "influencer": 2.8,
    }
    DEFAULT_EMISSIONS_G = 1.5
    out = []
    for ch, conversions, cost_usd, revenue_usd, events in rows:
        eg = emissions_g.get(str(ch).lower(), DEFAULT_EMISSIONS_G)
        out.append({
            "channel": ch,
            "emissions_g": eg * events,
            "conversions": conversions,
            "revenue_usd": revenue_usd,
            "cost_usd": cost_usd,
        })
    return out

# New endpoint: Journey-level KPIs
@router.get("/journeys")
def journey_kpis(engine: Engine = Depends(eng)):
    # Aggregate per user/journey: emissions, conversions, revenue, cost, channel path
    with engine.begin() as conn:
        rows = conn.execute(text("""
            SELECT user_id,
                   array_agg(channel ORDER BY ts_ms) AS path,
                   SUM(CASE WHEN event_type='conversion' THEN 1 ELSE 0 END) AS conversions,
                   SUM(cost_usd) AS cost_usd,
                   SUM(revenue_usd) AS revenue_usd,
                   COUNT(*) AS events
            FROM ad_events
            GROUP BY user_id
        """)).fetchall()
    emissions_g = {
        "email": 0.3,
        "display": 1.2,
        "search": 1.0,
        "video": 3.5,
        "social": 2.0,
        "tiktok": 2.8,
        "influencer": 2.8,
    }
    DEFAULT_EMISSIONS_G = 1.5
    out = []
    for user_id, path, conversions, cost_usd, revenue_usd, events in rows:
        # Estimate emissions for journey
        eg = sum(emissions_g.get(str(ch).lower(), DEFAULT_EMISSIONS_G) for ch in path)
        out.append({
            "user_id": user_id,
            "path": path,
            "emissions_g": eg,
            "conversions": conversions,
            "revenue_usd": revenue_usd,
            "cost_usd": cost_usd,
        })
    return out

@router.get("/rt/campaign/{campaign_id}")
def realtime_campaign_metrics(campaign_id: str, redis: Redis = Depends(rds)):
    key = f"rt:campaign:{campaign_id}"
    return {"campaign_id": campaign_id, "metrics": redis.hgetall(key)}

@router.post("/anomaly/score")
def anomaly_score(payload: dict):
    series = payload.get("series", [])
    detector = RobustZScoreAnomaly()
    return {"z": detector.score(series), "flags": detector.flags(series)}

@router.post("/budget/optimize")
def budget_optimize(payload: dict):
    # Payload format: { "total_budget_usd":..., "max_total_carbon_g":..., "campaigns":[...] }
    total_budget = float(payload["total_budget_usd"])
    max_carbon = float(payload["max_total_carbon_g"])
    camps = [
        Campaign(
            campaign_id=c["campaign_id"],
            max_budget_usd=float(c["max_budget_usd"]),
            min_budget_usd=float(c.get("min_budget_usd", 0.0)),
            expected_conversions_per_usd=float(c["expected_conversions_per_usd"]),
            expected_carbon_g_per_usd=float(c["expected_carbon_g_per_usd"]),
        )
        for c in payload["campaigns"]
    ]
    opt = EmissionAdjustedBudgetOptimizer()
    alloc = opt.optimize_max_conv_under_carbon(camps, total_budget, max_carbon)
    return {"allocation_usd": alloc}