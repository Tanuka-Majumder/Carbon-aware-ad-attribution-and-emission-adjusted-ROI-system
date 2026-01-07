from services.api.app.models.anomaly import RobustZScoreAnomaly

def test_anomaly_flags_outlier():
    s = [10]*30 + [1000]
    det = RobustZScoreAnomaly()
    flags = det.flags(s, threshold=4.0)
    assert flags[-1] is True