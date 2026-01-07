def estimate_emissions_g(
    kwh: float,
    gco2_per_kwh: float,
    pue: float = 1.2,
) -> float:
    """
    Simple operational emissions estimate:
      emissions = kWh * PUE * intensity(gCO2/kWh)
    """
    return float(kwh) * float(pue) * float(gco2_per_kwh)