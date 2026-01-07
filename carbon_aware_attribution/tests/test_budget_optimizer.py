from services.api.app.models.budget_optimizer import Campaign, EmissionAdjustedBudgetOptimizer

def test_budget_optimizer_respects_constraints():
    camps = [
        Campaign("A", max_budget_usd=100, min_budget_usd=0, expected_conversions_per_usd=0.05, expected_carbon_g_per_usd=10),
        Campaign("B", max_budget_usd=100, min_budget_usd=0, expected_conversions_per_usd=0.04, expected_carbon_g_per_usd=2),
    ]
    opt = EmissionAdjustedBudgetOptimizer()
    alloc = opt.optimize_max_conv_under_carbon(camps, total_budget_usd=100, max_total_carbon_g=300)

    assert sum(alloc.values()) <= 100 + 1e-6
    # carbon constraint
    carbon = alloc["A"] * 10 + alloc["B"] * 2
    assert carbon <= 300 + 1e-6