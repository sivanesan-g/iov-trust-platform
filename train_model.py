import argparse
import json
import os
import shutil
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from drl.agent import DDQNAgent
from drl.config import ACTION_SIZE, FEATURES, MODEL_DIR, MODEL_FILE, SCALER_FILE, STATE_SIZE
from drl.env import IoVTrustEnv

DEFAULT_DATA_FILE = os.path.join("data", "processed", "cleaned_data_full.csv")
REPORT_FILE = os.path.join(MODEL_DIR, "ddqn_training_report.txt")


def parse_args():
    parser = argparse.ArgumentParser(description="Train DDQN trust model")
    parser.add_argument("--data-file", default=DEFAULT_DATA_FILE, help="Processed dataset CSV/JSON file")
    parser.add_argument("--episodes", type=int, default=5, help="Number of training episodes")
    parser.add_argument("--test-size", type=float, default=0.2, help="Fraction of data reserved for testing")
    return parser.parse_args()


def load_dataset(path: str):
    dataset_path = Path(path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    suffix = dataset_path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(dataset_path)
    elif suffix in {".json", ".jsonl"}:
        if suffix == ".jsonl":
            records = [json.loads(line) for line in dataset_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        else:
            records = json.loads(dataset_path.read_text(encoding="utf-8"))
        df = pd.DataFrame(records)
    else:
        raise ValueError("Unsupported dataset format. Use .csv or .json/.jsonl")

    label_column = "target" if "target" in df.columns else "label" if "label" in df.columns else None
    if label_column is None:
        raise ValueError("Dataset must contain a 'target' or 'label' column")

    missing_features = [feature for feature in FEATURES if feature not in df.columns]
    if missing_features:
        raise ValueError(f"Dataset is missing required features: {missing_features}")

    X = df[FEATURES].to_numpy(dtype=np.float32)
    y = df[label_column].to_numpy(dtype=np.int64)
    return X, y


def evaluate(agent, X, y):
    preds = [agent.act(row, greedy=True) for row in X]
    acc = accuracy_score(y, preds)
    rep = classification_report(y, preds)
    cm = confusion_matrix(y, preds)
    return acc, rep, cm


def main(data_file, episodes, test_size):
    if not os.path.exists(data_file):
        raise FileNotFoundError(f"Processed dataset not found: {data_file}")

    os.makedirs(MODEL_DIR, exist_ok=True)

    X, y = load_dataset(data_file)

    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
    except ValueError:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train).astype("float32")
    X_test = scaler.transform(X_test).astype("float32")
    joblib.dump(scaler, SCALER_FILE)

    env = IoVTrustEnv(X_train, y_train)
    agent = DDQNAgent(STATE_SIZE, ACTION_SIZE)

    losses = []
    rewards = []

    for ep in range(episodes):
        state = env.reset()
        done = False
        total_reward = 0.0
        while not done:
            action = agent.act(state, greedy=False)
            next_state, reward, done, _ = env.step(action)
            agent.remember(state, action, reward, next_state, done)
            loss = agent.replay()
            if loss is not None:
                losses.append(loss)
            total_reward += reward
            state = next_state
        rewards.append(total_reward)
        print(f"Episode {ep + 1}/{episodes} reward={total_reward:.2f} epsilon={agent.epsilon:.4f}")

    run_name = f"trained_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    run_dir = Path(MODEL_DIR) / run_name
    run_dir.mkdir(parents=True, exist_ok=True)

    model_path = run_dir / "ddqn_trust_agent.pt"
    scaler_path = run_dir / "state_scaler.pkl"
    shutil.copy2(MODEL_FILE, model_path)
    shutil.copy2(SCALER_FILE, scaler_path)

    latest_dir = Path(MODEL_DIR) / "latest"
    if latest_dir.exists():
        shutil.rmtree(latest_dir)
    latest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(model_path, latest_dir / "ddqn_trust_agent.pt")
    shutil.copy2(scaler_path, latest_dir / "state_scaler.pkl")

    agent.save(MODEL_FILE)

    acc, rep, cm = evaluate(agent, X_test, y_test)

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(f"Data file: {data_file}\n")
        f.write(f"Accuracy: {acc}\n")
        f.write(f"Rewards by episode: {rewards}\n")
        if losses:
            f.write(f"Average loss: {sum(losses)/len(losses):.6f}\n\n")
        f.write("Classification report:\n")
        f.write(rep)
        f.write("\nConfusion Matrix:\n")
        f.write(str(cm))

    print("Model saved:", MODEL_FILE)
    print("Scaler saved:", SCALER_FILE)
    print("Accuracy:", acc)
    print(rep)
    print("Confusion Matrix:\n", cm)


if __name__ == "__main__":
    args = parse_args()
    main(args.data_file, args.episodes, args.test_size)
