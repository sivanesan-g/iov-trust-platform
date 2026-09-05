# IoV Trust Management Platform

This project validates telemetry, runs ML inference using the supplied scaler contract, updates trust, assigns shards, and exposes a Flask API. The repo already contains a real `state_scaler.pkl`, and the platform is intentionally aligned to that exact 12-feature order.

## Current project status

The saved scaler is a scikit-learn `StandardScaler` with 12 required features. The repository does not currently include a production classifier pickle, so the code loads the best available model artifact and fails clearly if no classifier is available instead of silently inventing a model.

## Architecture overview

- HTTP telemetry ingestion and MQTT consumer support
- Feature validation and replay protection
- Trust scoring state
- Shard and validator logic
- Local ledger block creation
- Docker-ready deployment
- Simulator for normal and attack traffic
- Render deployment template with Sepolia testnet variables

## Requirements

- Python 3.11+
- `pip install -r requirements.txt`
- Optional: Docker
- Optional: PostgreSQL

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Environment variables

```bash
copy .env.example .env
```

Relevant environment values include the database URL, MQTT host, model paths, secret key, and trust thresholds.

## Model setup

The exact feature order is:

```python
FEATURES = [
    "posx", "posy", "posz",
    "spdx", "spdy", "spdz",
    "aclx", "acly", "aclz",
    "hedx", "hedy", "hedz",
]
```

Inference uses:

```python
X = np.array([[features[name] for name in FEATURES]], dtype=np.float32)
X_scaled = scaler.transform(X)
```

## Running backend

```bash
python app.py
```

## Health check

```bash
curl http://127.0.0.1:5000/api/health
```

## Prediction API

Example request:

```bash
curl -X POST http://127.0.0.1:5000/api/predict -H "Content-Type: application/json" -d "{\"vehicle_id\":\"veh_sim_1\",\"message_id\":\"msg-001\",\"sequence\":1,\"timestamp\":1788534955.68,\"features\":{\"posx\":12.3,\"posy\":-4.2,\"posz\":0,\"spdx\":0.5,\"spdy\":0.2,\"spdz\":0,\"aclx\":0,\"acly\":0,\"aclz\":0,\"hedx\":0,\"hedy\":0,\"hedz\":0}}"
```

## Running simulator

```bash
python simulator/run.py --vehicles 10 --interval 0.1 --attack-rate 0.10
```

## Docker setup

```bash
docker compose up --build
```

## Free cloud and blockchain setup

The repository includes `render.yaml` for a free Render web service. In Render,
create the service from the repository and provide the secret environment values
marked with `sync: false`. Render supplies the public `PORT` value at runtime.

For a free blockchain test environment, use Ethereum Sepolia. Deploy
`contracts/TrustRegistry.sol` to Sepolia, then configure:

```text
ETH_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/<provider-key>
ETH_CHAIN_ID=11155111
ETH_ACCOUNT=0x<testnet-account>
ETH_PRIVATE_KEY=<testnet-private-key>
ETH_CONTRACT_ADDRESS=0x<deployed-contract>
```

Use test ETH only. Never place a mainnet private key in Render, `.env`, or the
repository. The service accepts `ETH_CONTRACT_ADDRESS` and the legacy
`TRUST_CONTRACT_ADDRESS` name.

Neon or another hosted PostgreSQL provider can supply `DATABASE_URL`. The local
Docker stack continues to use Postgres and Mosquitto; a hosted MQTT broker is
needed if the cloud deployment must receive MQTT traffic, because `localhost`
and the Docker `mqtt` hostname are not reachable from Render.

## Testing

```bash
pytest -q tests/test_inference.py tests/test_trust.py
```

## MQTT topic

Canonical topic:

```text
iov/{vehicle_id}/telemetry
```

## AWS notes

The target cloud architecture is:

```text
Vehicle -> AWS IoT Core -> ECS Fargate -> Flask API -> RDS PostgreSQL
```

## Troubleshooting

- Missing scaler: ensure `models/state_scaler.pkl` exists.
- Model missing: add the classifier artifact to `models/classifier.pkl` or update `MODEL_PATH`.
- MQTT problems: confirm the broker is running and `MQTT_HOST` is correct.
- `predict_state` failing: inspect the model artifact type and ensure it exposes a supported inference interface.

## Security notes

- Keep secrets outside source code.
- Validate message timestamps and replay IDs.
- Treat `Normal` and `Trusted` as separate concepts.
- Keep blockchain logging outside the synchronous telemetry critical path.

## Minimal missing artifact

The repository contains the scaler but not a real classifier pickle. The platform is explicitly built to detect this and report it rather than fabricating a model interface.

