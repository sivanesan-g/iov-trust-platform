from pathlib import Path

FEATURES = [
    "posx", "posy", "posz",
    "spdx", "spdy", "spdz",
    "aclx", "acly", "aclz",
    "hedx", "hedy", "hedz"
]

STATE_SIZE = len(FEATURES)
ACTION_SIZE = 2

BASE_DIR = Path(__file__).resolve().parents[1]
MODEL_DIR = str(BASE_DIR / "training_models")
TRAINING_MODELS_DIR = BASE_DIR / "training_models" / "latest"
MODEL_FILE = str(TRAINING_MODELS_DIR / "ddqn_trust_agent.pt")
SCALER_FILE = str(TRAINING_MODELS_DIR / "state_scaler.pkl")
