import os

import joblib
import numpy as np
import torch

from backend.config import FEATURES, LEGACY_MODEL_PATH, LEGACY_SCALER_PATH, MODEL_PATH, SCALER_PATH
from drl.agent import DDQNAgent
from drl.config import ACTION_SIZE, MODEL_FILE, SCALER_FILE, STATE_SIZE

_agent = None
_scaler = None


def _load_scaler():
    global _scaler
    candidate_paths = [SCALER_PATH, SCALER_FILE, str(LEGACY_SCALER_PATH), str(LEGACY_MODEL_PATH).replace("ddqn_trust_agent.pt", "state_scaler.pkl")]
    for path in candidate_paths:
        if path and os.path.exists(path):
            _scaler = joblib.load(path)
            return _scaler
    raise FileNotFoundError("Missing scaler: expected state_scaler.pkl in models/ or training_models/latest/")


def _load_classifier():
    global _agent
    candidate_paths = [MODEL_PATH, MODEL_FILE, str(LEGACY_MODEL_PATH)]
    for path in candidate_paths:
        if path and os.path.exists(path):
            if path.endswith(".pkl"):
                import pickle
                with open(path, "rb") as handle:
                    model = pickle.load(handle)
                return model
            _agent = DDQNAgent(STATE_SIZE, ACTION_SIZE)
            _agent.load(path)
            return _agent
    return None


def _ensure_loaded():
    global _agent, _scaler
    if _scaler is None:
        _load_scaler()
    if _agent is None:
        _agent = _load_classifier()


def _build_feature_vector(payload: dict):
    values = []
    for name in FEATURES:
        value = payload.get(name, 0.0)
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            numeric = 0.0
        if not np.isfinite(numeric):
            raise ValueError(f"Non-finite value for {name}: {value}")
        values.append(numeric)
    return np.asarray(values, dtype=np.float32).reshape(1, -1)


def predict_state(payload: dict):
    try:
        _ensure_loaded()
        row = _build_feature_vector(payload)
        scaler = _scaler
        X_scaled = scaler.transform(row).astype(np.float32)

        if _agent is None:
            raise FileNotFoundError("Missing classifier artifact. Models/classifier.pkl is required for production inference; this repo currently only contains the legacy model file and scaler.")

        if hasattr(_agent, "predict"):
            prediction = _agent.predict(X_scaled)
            label = "Normal" if str(prediction[0]).lower() == "0" or int(prediction[0]) == 0 else "Attack/Malicious"
            probabilities = None
            if hasattr(_agent, "predict_proba"):
                probabilities = _agent.predict_proba(X_scaled)[0]
                confidence = float(np.max(probabilities))
            else:
                confidence = 0.5
            return {
                "class_id": int(prediction[0]),
                "label": label,
                "confidence": round(confidence, 4),
                "state_vector": {name: float(payload.get(name, 0.0)) for name in FEATURES},
            }

        if hasattr(_agent, "act"):
            state = X_scaled[0]
            action = _agent.act(state, greedy=True)
            state_t = torch.FloatTensor(state).unsqueeze(0).to(_agent.device)
            with torch.no_grad():
                q = _agent.policy_net(state_t).cpu().numpy()[0]
            q_shift = q - np.max(q)
            probs = np.exp(q_shift) / np.sum(np.exp(q_shift))
            confidence = float(np.max(probs))
            label = "Normal" if action == 0 else "Attack/Malicious"
            return {
                "class_id": int(action),
                "label": label,
                "confidence": round(confidence, 4),
                "state_vector": {name: float(payload.get(name, 0.0)) for name in FEATURES},
            }

        raise TypeError("Classifier interface is not supported")
    except Exception as exc:
        return {
            "class_id": -1,
            "label": "PredictionError",
            "confidence": 0.0,
            "error": str(exc),
            "state_vector": {name: float(payload.get(name, 0.0)) for name in FEATURES},
        }
