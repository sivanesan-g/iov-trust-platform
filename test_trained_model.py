import joblib
import numpy as np
import torch

from drl.agent import DDQNAgent
from drl.config import FEATURES, STATE_SIZE, ACTION_SIZE, MODEL_FILE, SCALER_FILE


def test_model():
    agent = DDQNAgent(STATE_SIZE, ACTION_SIZE)
    agent.load(MODEL_FILE)
    scaler = joblib.load(SCALER_FILE)

    sample = np.array([[300.0, 120.0, 0.0, 4.5, 9.8, 2.2, 4.2, 8.5, 0.5, 2.4, -2.1, 1.3]], dtype=np.float32)
    scaled = scaler.transform(sample).astype(np.float32)

    action = agent.act(scaled[0], greedy=True)
    state_t = torch.FloatTensor(scaled[0]).unsqueeze(0).to(agent.device)
    with torch.no_grad():
        q_values = agent.policy_net(state_t).cpu().numpy()[0]

    print("Model file:", MODEL_FILE)
    print("Scaler file:", SCALER_FILE)
    print("Features used:", FEATURES)
    print("Predicted action:", action)
    print("Q-values:", q_values)


if __name__ == "__main__":
    test_model()
