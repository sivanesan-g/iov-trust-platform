import json
import math
import os
from pathlib import Path

from backend.config import (
    FEATURES,
    SHARD_COUNT,
    TRUST_CRITICAL,
    TRUST_LOW,
    TRUST_MEDIUM,
    TRUST_MIN,
    TRUST_MAX,
    TRUST_PENALTY_ATTACK,
    TRUST_PENALTY_INVALID,
    TRUST_PENALTY_REPLAY,
    TRUST_REWARD_NORMAL,
    TRUST_VERY_LOW,
)


class TrustService:
    """Stateful trust manager for IoV telemetry decisions."""

    def __init__(self, storage_path=None):
        base_dir = Path(__file__).resolve().parents[1]
        default_path = Path(os.getenv("TRUST_STORE_PATH", base_dir / "data" / "trust_state.json"))
        effective_path = str(storage_path) if storage_path is not None else str(default_path)
        self._in_memory = effective_path == ":memory:"
        self.storage_path = None if self._in_memory else Path(effective_path)
        if self.storage_path is not None:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.scores = {}
        self.history = {}
        self.load_state()

    @staticmethod
    def clamp(value: float, minimum=TRUST_MIN, maximum=TRUST_MAX):
        return max(minimum, min(maximum, float(value)))

    def get_level(self, score: float) -> str:
        score = float(score)
        if score <= TRUST_CRITICAL:
            return "CRITICAL"
        if score <= TRUST_VERY_LOW:
            return "VERY_LOW"
        if score <= TRUST_LOW:
            return "LOW"
        if score <= TRUST_MEDIUM:
            return "MEDIUM"
        return "HIGH"

    def get_percentage(self, score: float) -> float:
        return round(max(0.0, min(100.0, float(score) * 100.0)), 2)

    def get(self, vehicle_id: str) -> float:
        return self.scores.get(vehicle_id, 0.5)

    def load_state(self):
        if self._in_memory or self.storage_path is None:
            return
        if not self.storage_path.exists():
            return
        try:
            with self.storage_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            self.scores = {str(k): float(v) for k, v in data.get("scores", {}).items()}
            self.history = {str(k): dict(v) for k, v in data.get("history", {}).items()}
        except Exception:
            self.scores = {}
            self.history = {}

    def persist_state(self):
        if self._in_memory or self.storage_path is None:
            return
        with self.storage_path.open("w", encoding="utf-8") as handle:
            json.dump({"scores": self.scores, "history": self.history}, handle, indent=2, sort_keys=True)

    def _history_for(self, vehicle_id: str):
        if vehicle_id not in self.history:
            self.history[vehicle_id] = {"normal": 0, "attack": 0, "replay": 0, "invalid": 0}
        return self.history[vehicle_id]

    def update(self, vehicle_id: str, prediction_label: str, confidence: float = 0.5, *, invalid_packet: bool = False, replay: bool = False, authentication_valid: bool = True, reason: str = "score_update") -> float:
        current = self.get(vehicle_id)
        label = (prediction_label or "").strip().lower()
        confidence = max(0.0, min(1.0, float(confidence or 0.5)))
        history = self._history_for(vehicle_id)

        delta = 0.0
        if "normal" in label:
            history["normal"] += 1
            delta = TRUST_REWARD_NORMAL * (0.5 + confidence)
        elif "attack" in label or "malicious" in label:
            history["attack"] += 1
            repeat_penalty = min(0.08 * history["attack"], 0.25)
            delta = -(TRUST_PENALTY_ATTACK * confidence + repeat_penalty)
        elif replay:
            history["replay"] += 1
            delta = -TRUST_PENALTY_REPLAY
        elif invalid_packet:
            history["invalid"] += 1
            delta = -TRUST_PENALTY_INVALID
        else:
            delta = -0.01 if not authentication_valid else 0.0

        if not authentication_valid:
            delta -= 0.09

        new_score = self.clamp(current + delta)
        self.scores[vehicle_id] = new_score
        self.persist_state()
        return new_score

    def trust_status(self, trust_score):
        return self.get_level(trust_score)

    def get_history(self, vehicle_id: str):
        return self._history_for(vehicle_id)

    def process_telemetry(self, payload: dict):
        vehicle_id = str(payload.get("vehicle_id", "unknown"))
        features = payload.get("features", {})
        confidence = 0.5
        prediction = {"class_id": -1, "label": "PredictionError", "confidence": 0.0, "state_vector": {name: float(features.get(name, 0.0)) for name in FEATURES}}
        status = "ERROR"
        authenticated = True
        packet_valid = True
        replay_detected = False

        if not isinstance(features, dict):
            packet_valid = False
        else:
            for name in FEATURES:
                if name not in features:
                    packet_valid = False
                    break
                value = features[name]
                if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                    packet_valid = False
                    break

        if not packet_valid:
            self.update(vehicle_id, "Invalid", 0.0, invalid_packet=True, authentication_valid=authenticated, reason="invalid_packet")
            return {
                "status": "rejected",
                "security": {"authenticated": authenticated, "packet_valid": False, "replay": False, "action": "REJECT"},
                "trust": {"score": self.get(vehicle_id), "percentage": self.get_percentage(self.get(vehicle_id)), "level": self.trust_status(self.get(vehicle_id))},
                "prediction": prediction,
            }

        ml_prediction = payload.get("prediction")
        if isinstance(ml_prediction, dict):
            prediction = ml_prediction
            confidence = float(ml_prediction.get("confidence", 0.5))
            status = "PREDICTED"

        score = self.update(vehicle_id, prediction.get("label", "Normal"), confidence, invalid_packet=False, replay=False, authentication_valid=authenticated, reason="ml_update")
        level = self.trust_status(score)
        action = "ALLOW" if level in {"HIGH", "MEDIUM"} else "MONITOR" if level == "LOW" else "QUARANTINE"
        if prediction.get("label", "").lower().startswith("attack") or prediction.get("label", "").lower().startswith("malicious"):
            action = "QUARANTINE" if score < 0.4 else "SUSPICIOUS"

        return {
            "status": status,
            "prediction": prediction,
            "trust": {"score": round(score, 4), "percentage": self.get_percentage(score), "level": level},
            "security": {"authenticated": authenticated, "packet_valid": packet_valid, "replay": replay_detected, "action": action},
            "network": {"shard": f"shard_{(abs(hash(vehicle_id)) % SHARD_COUNT) + 1}", "validator": vehicle_id},
        }


def analyze_vehicle_status(ml_label: str, confidence: float, trust_score: float, authenticated: bool, packet_valid: bool, replay: bool, historical_trust: float) -> dict:
    score = float(trust_score)
    if ml_label.lower().startswith("attack") or ml_label.lower().startswith("malicious"):
        if confidence >= 0.9 and score < 0.4:
            action = "QUARANTINE"
        elif score < 0.6:
            action = "SUSPICIOUS"
        else:
            action = "MONITOR"
    elif score >= 0.8 and authenticated and packet_valid and not replay:
        action = "ALLOW"
    elif score >= 0.6:
        action = "MONITOR"
    else:
        action = "SUSPICIOUS"

    final_status = "ATTACK/MALICIOUS" if ml_label.lower().startswith("attack") or ml_label.lower().startswith("malicious") else "TRUSTED" if score >= 0.8 else "NORMAL"
    return {"final_status": final_status, "action": action, "score": round(score, 4), "historical_trust": round(historical_trust, 4)}
