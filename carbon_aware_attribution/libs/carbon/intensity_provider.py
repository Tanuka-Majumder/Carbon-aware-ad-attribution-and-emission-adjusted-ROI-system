from dataclasses import dataclass
import time
import random

@dataclass(frozen=True)
class CarbonIntensity:
    gco2_per_kwh: float
    region: str
    ts_s: int

class CarbonIntensityProvider:
    """
    Replace this with:
    - ElectricityMaps API
    - WattTime
    - Cloud provider region carbon APIs
    """
    def get_current(self, region: str) -> CarbonIntensity:
        base = {"us-east": 380, "us-west": 220, "eu-west": 170, "ap-south": 540}.get(region, 400)
        jitter = random.randint(-20, 20)
        return CarbonIntensity(gco2_per_kwh=float(base + jitter), region=region, ts_s=int(time.time()))