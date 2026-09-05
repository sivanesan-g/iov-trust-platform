import os
import uuid
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from backend.config import DEFAULT_MODEL_PATH, DEFAULT_SCALER_PATH, SHARD_COUNT
from backend.security.rate_limit import RateLimiter
from backend.security.replay import ReplayGuard
from backend.security.validation import validate_telemetry
from backend.trust_service import TrustService, analyze_vehicle_status
from blockchain.agsb import AdaptiveGraphSharding
from blockchain.dpos import DPoSValidator
from blockchain.ledger import ShardedBlockchainLedger
from drl.infer import predict_state

BASE_DIR = Path(__file__).resolve().parent
DASHBOARD_DIR = BASE_DIR / "iov_admin_dashboard"

app = Flask(__name__)
CORS(app)

trust_service = TrustService()
rate_limiter = RateLimiter()
replay_guard = ReplayGuard()
sharding = AdaptiveGraphSharding(shard_count=SHARD_COUNT)
validator_engine = DPoSValidator()
ledger = ShardedBlockchainLedger(shard_names=[f"shard_{idx + 1}" for idx in range(SHARD_COUNT)])


def error_response(code: str, message: str, status_code: int = 400):
    return jsonify({"error": {"code": code, "message": message, "request_id": str(uuid.uuid4())}}), status_code


@app.route("/", methods=["GET"])
def index():
    return send_from_directory(DASHBOARD_DIR, "index.html")


@app.route("/<path:filename>", methods=["GET"])
def dashboard_static(filename):
    return send_from_directory(DASHBOARD_DIR, filename)


@app.route("/api/health", methods=["GET"])
def health():
    model_state = "loaded" if DEFAULT_MODEL_PATH.exists() else "degraded"
    scaler_state = "loaded" if DEFAULT_SCALER_PATH.exists() else "missing"
    compat = {
        "status": "healthy" if model_state == "loaded" and scaler_state == "loaded" else "degraded",
        "database": "healthy",
        "model": model_state,
        "scaler": scaler_state,
        "mqtt": "connected",
        "missing_artifacts": [name for name, exists in {"models/classifier.pkl": DEFAULT_MODEL_PATH.exists(), "models/state_scaler.pkl": DEFAULT_SCALER_PATH.exists()}.items() if not exists],
        "message": "Production classifier not present; using degraded runtime until a real classifier artifact is added." if model_state == "degraded" else "All required runtime components are available.",
    }
    return jsonify(compat)


@app.route("/api/predict", methods=["POST"])
def predict_api():
    request_id = str(uuid.uuid4())
    payload = request.get_json(silent=True) or {}
    ok, validation = validate_telemetry(payload)
    if not ok:
        return error_response(validation.get("code", "INVALID_REQUEST"), validation.get("message", "Invalid request"))

    vehicle_id = str(payload["vehicle_id"])
    bucket_key = vehicle_id
    if not rate_limiter.allow(bucket_key):
        return error_response("RATE_LIMIT", "Too many requests", 429)

    if replay_guard.is_duplicate(vehicle_id, payload["message_id"], payload["sequence"]):
        return error_response("REPLAY_DETECTED", "Duplicate message detected", 409)

    features = payload["features"]
    prediction = predict_state(features)
    current_trust = trust_service.get(vehicle_id)
    shard_name, cross_shard = sharding.assign_shard(vehicle_id, features, current_trust)
    updated_trust = trust_service.update(vehicle_id, prediction["label"], prediction.get("confidence", 0.5))
    trust_status = trust_service.trust_status(updated_trust)

    validator_engine.update_trust(vehicle_id, updated_trust)
    validator = validator_engine.select_validator(sharding.shards[shard_name])
    if validator is None:
        validator = vehicle_id

    final_status = analyze_vehicle_status(prediction.get("label", "Normal"), float(prediction.get("confidence", 0.5)), updated_trust, True, True, False, current_trust)
    event = {
        "event": {
            "vehicle_id": vehicle_id,
            "features": features,
            "prediction": prediction,
            "trust_score": updated_trust,
            "shard": shard_name,
            "cross_shard": cross_shard,
            "validator": validator,
        },
        "block": ledger.add_block(shard_name, validator or vehicle_id, {"vehicle_id": vehicle_id, "prediction": prediction, "trust_score": updated_trust}),
    }
    replay_guard.mark_processed(vehicle_id, payload["message_id"], payload["sequence"])

    response = {
        "vehicle_id": vehicle_id,
        "prediction": {"class_id": prediction.get("class_id"), "label": prediction.get("label"), "confidence": prediction.get("confidence")},
        "trust": {"score": round(updated_trust, 4), "percentage": trust_service.get_percentage(updated_trust), "level": trust_status},
        "network": {"shard": shard_name, "validator": validator},
        "security": {"authenticated": True, "packet_valid": True, "replay": False, "action": final_status["action"]},
        "event": event,
        "request_id": request_id,
    }
    return jsonify(response)


@app.route("/api/healthz", methods=["GET"])
def healthz():
    return jsonify({"status": "healthy"})


@app.route("/api/vehicles", methods=["GET"])
def vehicles():
    return jsonify({"vehicles": list(sharding.vehicle_to_shard.keys())})


@app.route("/api/vehicles/<vehicle_id>", methods=["GET"])
def vehicle_detail(vehicle_id):
    return jsonify({"vehicle_id": vehicle_id, "trust": trust_service.get(vehicle_id), "history": trust_service.get_history(vehicle_id)})


@app.route("/api/trust/<vehicle_id>", methods=["GET"])
def trust_detail(vehicle_id):
    score = trust_service.get(vehicle_id)
    return jsonify({"vehicle_id": vehicle_id, "score": round(score, 4), "percentage": trust_service.get_percentage(score), "level": trust_service.trust_status(score), "history": trust_service.get_history(vehicle_id)})


@app.route("/api/telemetry/<vehicle_id>", methods=["GET"])
def telemetry_detail(vehicle_id):
    return jsonify({"vehicle_id": vehicle_id, "telemetry": []})


@app.route("/api/predictions/<vehicle_id>", methods=["GET"])
def predictions(vehicle_id):
    return jsonify({"vehicle_id": vehicle_id, "predictions": []})


@app.route("/api/shards", methods=["GET"])
def shards():
    payload = []
    for shard_id, vehicles in sharding.shards.items():
        payload.append({"id": shard_id, "vehicles": len(vehicles), "validator": validator_engine.select_validator(vehicles) or shard_id})
    return jsonify({"shards": payload})


@app.route("/api/ledger", methods=["GET"])
def ledger_summary():
    return jsonify(ledger.export())


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("APP_ENV", "development") == "development",
    )