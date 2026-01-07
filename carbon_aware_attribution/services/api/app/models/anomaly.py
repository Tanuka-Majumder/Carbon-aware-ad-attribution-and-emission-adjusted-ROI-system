import numpy as np

class RobustZScoreAnomaly:
    """
    Detect anomalies on a univariate metric using robust z-score (MAD).
    """
    def score(self, series: list[float]) -> list[float]:
        x = np.asarray(series, dtype=float)
        if len(x) < 10:
            return [0.0] * len(x)
        med = np.median(x)
        mad = np.median(np.abs(x - med)) + 1e-9
        z = 0.6745 * (x - med) / mad
        return z.tolist()

    def flags(self, series: list[float], threshold: float = 4.0) -> list[bool]:
        z = self.score(series)
        return [abs(v) >= threshold for v in z]