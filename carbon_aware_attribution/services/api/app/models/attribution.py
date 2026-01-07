from dataclasses import dataclass
from sqlalchemy import text
from sqlalchemy.engine import Engine
import numpy as np

@dataclass(frozen=True)
class PathRecord:
    channels: list[str]   # ordered touches
    converted: int        # 0/1

class AttributionModel:
    """
    Lightweight baseline:
    - Build user paths from events
    - Compute channel contribution via Shapley-like proxy using leave-one-out lift
    This is not full causal MTA, but demonstrates strong modeling structure.
    """
    def __init__(self, engine: Engine):
        self.engine = engine

    def fetch_paths(self, lookback_days: int = 30, max_paths: int = 20000) -> list[PathRecord]:
        # Calculate lookback in ms in Python
        lookback_ms = int(lookback_days) * 24 * 3600 * 1000
        with self.engine.begin() as conn:
            rows = conn.execute(text("""
                WITH windowed AS (
                  SELECT user_id, ts_ms, event_type, channel
                  FROM ad_events
                  WHERE ts_ms >= (EXTRACT(EPOCH FROM NOW()) * 1000)::BIGINT - :lookback_ms
                ),
                clicks AS (
                  SELECT user_id, ts_ms, channel
                  FROM windowed
                  WHERE event_type IN ('impression','click')
                ),
                conv AS (
                  SELECT user_id, MIN(ts_ms) AS conv_ts
                  FROM windowed
                  WHERE event_type='conversion'
                  GROUP BY user_id
                )
                SELECT c.user_id,
                       array_agg(c.channel ORDER BY c.ts_ms) AS path,
                       CASE WHEN v.conv_ts IS NULL THEN 0 ELSE 1 END AS converted
                FROM clicks c
                LEFT JOIN conv v ON v.user_id = c.user_id
                GROUP BY c.user_id, converted
                LIMIT :max_paths
            """), {"lookback_ms": lookback_ms, "max_paths": int(max_paths)}).fetchall()

        out: list[PathRecord] = []
        for user_id, path, converted in rows:
            if not path:
                continue
            out.append(PathRecord(channels=list(path), converted=int(converted)))
        return out

    def shapley_proxy(self, paths: list[PathRecord]) -> dict[str, float]:
        """
        Leave-one-out lift:
          contribution(channel) = P(conv | path) - P(conv | path without channel)
        Averaged over all occurrences.
        """
        if not paths:
            return {}

        # Estimate conv prob by path signature
        def sig(chs: list[str]) -> str:
            return " > ".join(chs)

        conv_by_sig = {}
        cnt_by_sig = {}
        for p in paths:
            s = sig(p.channels)
            conv_by_sig[s] = conv_by_sig.get(s, 0) + p.converted
            cnt_by_sig[s] = cnt_by_sig.get(s, 0) + 1

        def pconv(chs: list[str]) -> float:
            s = sig(chs)
            return (conv_by_sig.get(s, 0) / cnt_by_sig.get(s, 1)) if s in cnt_by_sig else 0.0

        contrib = {}
        denom = {}

        for p in paths:
            base = pconv(p.channels)
            uniq = set(p.channels)
            for ch in uniq:
                reduced = [x for x in p.channels if x != ch]
                red = pconv(reduced) if reduced else 0.0
                lift = base - red
                contrib[ch] = contrib.get(ch, 0.0) + lift
                denom[ch] = denom.get(ch, 0) + 1

        # normalize to sum to 1 (optional)
        scores = {k: (contrib[k] / max(1, denom[k])) for k in contrib}
        total = sum(max(0.0, v) for v in scores.values())
        if total > 0:
            scores = {k: max(0.0, v) / total for k, v in scores.items()}
        return scores

    def compute_channel_attribution(self) -> dict[str, float]:
        paths = self.fetch_paths()
        return self.shapley_proxy(paths)