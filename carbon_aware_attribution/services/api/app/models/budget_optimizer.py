
from app.core.config import get_model

def score_campaign(cost_usd, clicks):
    model = get_model()
    return float(model.predict([[cost_usd, clicks]])[0])
from dataclasses import dataclass
import numpy as np
import cvxpy as cp

@dataclass(frozen=True)
class Campaign:
    campaign_id: str
    max_budget_usd: float
    min_budget_usd: float
    expected_conversions_per_usd: float   # performance model output
    expected_carbon_g_per_usd: float      # carbon model output

class EmissionAdjustedBudgetOptimizer:
    """
    Maximize conversions with a carbon constraint OR minimize carbon for target conversions.
    """
    def optimize_max_conv_under_carbon(
        self,
        campaigns: list[Campaign],
        total_budget_usd: float,
        max_total_carbon_g: float,
    ) -> dict[str, float]:
        n = len(campaigns)
        b = cp.Variable(n, nonneg=True)

        max_b = np.array([c.max_budget_usd for c in campaigns], dtype=float)
        min_b = np.array([c.min_budget_usd for c in campaigns], dtype=float)
        conv_rate = np.array([c.expected_conversions_per_usd for c in campaigns], dtype=float)
        carbon_rate = np.array([c.expected_carbon_g_per_usd for c in campaigns], dtype=float)

        objective = cp.Maximize(conv_rate @ b)
        constraints = [
            b <= max_b,
            b >= min_b,
            cp.sum(b) <= total_budget_usd,
            carbon_rate @ b <= max_total_carbon_g,
        ]

        prob = cp.Problem(objective, constraints)
        prob.solve(solver=cp.ECOS, verbose=False)

        if b.value is None:
            raise RuntimeError("Optimization failed (infeasible or solver error).")

        alloc = {campaigns[i].campaign_id: float(max(0.0, b.value[i])) for i in range(n)}
        return alloc