"""Small simulator: run one prediction -> trust update -> shard assign -> validator select -> ledger block

This script uses the project's services but does not interact with Ethereum.
Run: python scripts/simulate_request.py
"""
import json
from pathlib import Path

from backend.trust_service import TrustService
from blockchain.agsb import AdaptiveGraphSharding
from blockchain.dpos import DPoSValidator
from blockchain.ledger import ShardedBlockchainLedger
from drl.infer import predict_state


def simulate(vehicle_id: str, features: dict):
    trust_service = TrustService()
    agsb = AdaptiveGraphSharding(shard_count=3)
    validator_engine = DPoSValidator()
    ledger = ShardedBlockchainLedger(shard_names=list(agsb.shards.keys()))

    # Current trust
    current_trust = trust_service.get(vehicle_id)

    # Shard assignment
    shard, cross_shard = agsb.assign_shard(vehicle_id, features, trust_score=current_trust)

    # Predict
    prediction = predict_state(features)

    # Update trust
    updated_trust = trust_service.update(vehicle_id, prediction.get("label", "PredictionError"), confidence=prediction.get("confidence", 0.5))

    # Validator selection
    validator_engine.update_trust(vehicle_id, updated_trust)
    validator = validator_engine.select_validator(agsb.shards[shard])

    # Ledger
    event = {
        "vehicle_id": vehicle_id,
        "features": features,
        "prediction": prediction,
        "trust_score": updated_trust,
        "shard": shard,
        "cross_shard": cross_shard,
        "validator": validator,
    }

    block = ledger.add_block(shard_name=shard, validator=validator or "fallback", data=event)

    out = {
        "event": event,
        "block": block,
    }

    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    # example features (stationary vehicle)
    features = {
        "posx": 12.3, "posy": -4.2, "posz": 0.0,
        "spdx": 0.5, "spdy": 0.2, "spdz": 0.0,
        "aclx": 0.0, "acly": 0.0, "aclz": 0.0,
        "hedx": 0.0, "hedy": 0.0, "hedz": 0.0,
    }

    simulate("veh_sim_1", features)
