from backend.trust_service import TrustService


def test_normal_prediction_increases_trust():
    service = TrustService(storage_path=":memory:")
    score = service.update("veh_1", "Normal", 0.99)
    assert 0.0 <= score <= 1.0
    assert score >= 0.5


def test_malicious_prediction_reduces_trust():
    service = TrustService(storage_path=":memory:")
    service.scores["veh_2"] = 0.9
    score = service.update("veh_2", "Attack/Malicious", 0.97)
    assert score < 0.9


def test_trust_level_thresholds_are_configurable():
    service = TrustService(storage_path=":memory:")
    assert service.get_level(0.10) == "CRITICAL"
    assert service.get_level(0.50) == "LOW"
    assert service.get_level(0.85) == "HIGH"


def test_repeated_malicious_events_penalize_more():
    service = TrustService(storage_path=":memory:")
    service.scores["veh_3"] = 0.8
    service.update("veh_3", "Attack/Malicious", 0.95)
    score = service.update("veh_3", "Attack/Malicious", 0.97)
    assert score < 0.8
