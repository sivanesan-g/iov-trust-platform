import math
from datetime import datetime, timezone

from backend.config import FEATURES, MAX_FUTURE_SKEW_SECONDS, MAX_MESSAGE_AGE_SECONDS


def is_finite_number(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(number)


def validate_telemetry(payload: dict):
    if not isinstance(payload, dict):
        return False, {"code": "INVALID_PAYLOAD", "message": "Payload must be a JSON object"}

    required_top_level = ["vehicle_id", "message_id", "sequence", "features"]
    missing_top = [name for name in required_top_level if name not in payload]
    if missing_top:
        return False, {"code": "MISSING_REQUIRED_FIELDS", "message": f"Missing fields: {missing_top}"}

    vehicle_id = str(payload.get("vehicle_id", "")).strip()
    if not vehicle_id:
        return False, {"code": "INVALID_VEHICLE_ID", "message": "vehicle_id is required"}

    message_id = str(payload.get("message_id", "")).strip()
    if not message_id:
        return False, {"code": "INVALID_MESSAGE_ID", "message": "message_id is required"}

    sequence = payload.get("sequence")
    if not isinstance(sequence, int) or sequence < 1:
        return False, {"code": "INVALID_SEQUENCE", "message": "sequence must be a positive integer"}

    now = datetime.now(timezone.utc).timestamp()
    timestamp = payload.get("timestamp")
    if timestamp is None:
        ts = now
    else:
        if not is_finite_number(timestamp):
            return False, {"code": "INVALID_TIMESTAMP", "message": "timestamp must be a finite number"}
        ts = float(timestamp)
        if ts > now + MAX_FUTURE_SKEW_SECONDS:
            return False, {"code": "FUTURE_TIMESTAMP", "message": "timestamp exceeds allowed clock skew"}
        if now - ts > MAX_MESSAGE_AGE_SECONDS:
            return False, {"code": "STALE_MESSAGE", "message": "timestamp is too old"}

    features = payload.get("features")
    if not isinstance(features, dict):
        return False, {"code": "INVALID_FEATURES", "message": "features must be an object"}

    missing_features = [name for name in FEATURES if name not in features]
    if missing_features:
        return False, {"code": "INVALID_FEATURES", "message": f"Required feature missing: {missing_features}"}

    invalid_values = []
    for name in FEATURES:
        value = features.get(name)
        if not is_finite_number(value):
            invalid_values.append(name)
    if invalid_values:
        return False, {"code": "INVALID_FEATURE_VALUES", "message": f"Non-finite feature values: {invalid_values}"}

    return True, {"vehicle_id": vehicle_id, "message_id": message_id, "timestamp": ts, "sequence": sequence}
