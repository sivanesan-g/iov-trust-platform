import math

import numpy as np

from drl.config import FEATURES
from drl.infer import predict_state


def test_feature_order_matches_contract():
    assert FEATURES == [
        "posx", "posy", "posz",
        "spdx", "spdy", "spdz",
        "aclx", "acly", "aclz",
        "hedx", "hedy", "hedz",
    ]
    assert len(FEATURES) == 12


def test_inference_returns_class_and_confidence_for_valid_packet():
    payload = {
        "posx": 12.3,
        "posy": -4.2,
        "posz": 0.0,
        "spdx": 0.5,
        "spdy": 0.2,
        "spdz": 0.0,
        "aclx": 0.0,
        "acly": 0.0,
        "aclz": 0.0,
        "hedx": 0.0,
        "hedy": 0.0,
        "hedz": 0.0,
    }
    result = predict_state(payload)
    assert result["class_id"] in {0, 1}
    assert result["confidence"] >= 0.0
    assert result["confidence"] <= 1.0
    assert isinstance(result["label"], str)
    assert set(result["state_vector"]) == set(FEATURES)


def test_inference_rejects_non_finite_values():
    payload = {name: 0.0 for name in FEATURES}
    payload["posx"] = float("nan")
    result = predict_state(payload)
    assert result["class_id"] == -1
    assert result["label"] in {"PredictionError", "INVALID_INPUT"}


def test_scaler_transform_requires_exact_12_features():
    X = np.array([[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]], dtype=np.float32)
    assert X.shape[1] == 11
    assert np.isfinite(X).all()
