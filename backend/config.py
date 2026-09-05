import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env.local")
load_dotenv(BASE_DIR / ".env")

MODELS_DIR = BASE_DIR / "models"
TRAINING_MODELS_DIR = BASE_DIR / "training_models" / "latest"
DEFAULT_MODEL_PATH = MODELS_DIR / "classifier.pt"
DEFAULT_SCALER_PATH = MODELS_DIR / "state_scaler.pkl"
LEGACY_MODEL_PATH = TRAINING_MODELS_DIR / "ddqn_trust_agent.pt"
LEGACY_SCALER_PATH = TRAINING_MODELS_DIR / "state_scaler.pkl"

FEATURES = [
    "posx",
    "posy",
    "posz",
    "spdx",
    "spdy",
    "spdz",
    "aclx",
    "acly",
    "aclz",
    "hedx",
    "hedy",
    "hedz",
]

APP_ENV = os.getenv("APP_ENV", "development")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/iov.db")
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "iov/+/telemetry")
MODEL_PATH = os.getenv("MODEL_PATH", str(DEFAULT_MODEL_PATH))
SCALER_PATH = os.getenv("SCALER_PATH", str(DEFAULT_SCALER_PATH))
MODEL_VERSION = os.getenv("MODEL_VERSION", "1.0.0")
SCALER_VERSION = os.getenv("SCALER_VERSION", "1.0.0")

JWT_SECRET = os.getenv("JWT_SECRET", "CHANGE_ME")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ISSUER = os.getenv("JWT_ISSUER", "iov-trust")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "iov-clients")

MAX_MESSAGE_AGE_SECONDS = int(os.getenv("MAX_MESSAGE_AGE_SECONDS", "30"))
MAX_FUTURE_SKEW_SECONDS = int(os.getenv("MAX_FUTURE_SKEW_SECONDS", "10"))
MAX_MESSAGES_PER_SECOND = int(os.getenv("MAX_MESSAGES_PER_SECOND", "20"))
SHARD_COUNT = int(os.getenv("SHARD_COUNT", "4"))

TRUST_CRITICAL = float(os.getenv("TRUST_CRITICAL", "0.20"))
TRUST_VERY_LOW = float(os.getenv("TRUST_VERY_LOW", "0.40"))
TRUST_LOW = float(os.getenv("TRUST_LOW", "0.60"))
TRUST_MEDIUM = float(os.getenv("TRUST_MEDIUM", "0.80"))
TRUST_REWARD_NORMAL = float(os.getenv("TRUST_REWARD_NORMAL", "0.02"))
TRUST_PENALTY_ATTACK = float(os.getenv("TRUST_PENALTY_ATTACK", "0.15"))
TRUST_PENALTY_REPLAY = float(os.getenv("TRUST_PENALTY_REPLAY", "0.25"))
TRUST_PENALTY_INVALID = float(os.getenv("TRUST_PENALTY_INVALID", "0.10"))
TRUST_MIN = float(os.getenv("TRUST_MIN", "0.0"))
TRUST_MAX = float(os.getenv("TRUST_MAX", "1.0"))
VALIDATOR_MIN_TRUST = float(os.getenv("VALIDATOR_MIN_TRUST", "0.80"))

MQTT_CANONICAL_TOPIC = "iov/{vehicle_id}/telemetry"


def get_model_paths():
    scaler_candidates = [
        SCALER_PATH,
        str(DEFAULT_SCALER_PATH),
        str(LEGACY_SCALER_PATH),
    ]
    model_candidates = [
        MODEL_PATH,
        str(DEFAULT_MODEL_PATH),
        str(LEGACY_MODEL_PATH),
    ]
    return model_candidates, scaler_candidates
