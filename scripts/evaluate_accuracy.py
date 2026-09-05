import argparse
import csv
import json
import sys
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from drl.agent import DDQNAgent
from drl.config import ACTION_SIZE, FEATURES, MODEL_FILE, SCALER_FILE, STATE_SIZE


def load_dataset(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            records = list(csv.DictReader(handle))
    elif path.suffix.lower() in {".json", ".jsonl"}:
        if path.suffix.lower() == ".jsonl":
            records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        else:
            records = json.loads(path.read_text(encoding="utf-8"))
    else:
        raise ValueError("Dataset must be .csv, .json, or .jsonl")

    if not records:
        raise ValueError("Dataset is empty")

    columns = set(records[0])
    label_column = "target" if "target" in columns else "label" if "label" in columns else None
    if label_column is None:
        raise ValueError("Dataset must contain a 'label' or 'target' column")

    missing = [feature for feature in FEATURES if feature not in columns]
    if missing:
        raise ValueError(f"Dataset is missing required features: {missing}")

    features = np.asarray([[float(record[name]) for name in FEATURES] for record in records], dtype=np.float32)
    labels = np.asarray([int(record[label_column]) for record in records], dtype=np.int64)
    return features, labels


def main():
    parser = argparse.ArgumentParser(description="Report DDQN model accuracy as a percentage")
    parser.add_argument("--data-file", default="sample_data.csv")
    parser.add_argument("--model-file", default=MODEL_FILE)
    parser.add_argument("--scaler-file", default=SCALER_FILE)
    args = parser.parse_args()

    features, labels = load_dataset(Path(args.data_file))
    scaler = joblib.load(args.scaler_file)
    scaled_features = scaler.transform(features).astype(np.float32)

    agent = DDQNAgent(STATE_SIZE, ACTION_SIZE)
    agent.load(args.model_file)
    predictions = np.asarray([agent.act(row, greedy=True) for row in scaled_features], dtype=np.int64)

    accuracy = accuracy_score(labels, predictions)
    print(f"Samples: {len(labels)}")
    print(f"Correct: {int(np.sum(labels == predictions))}")
    print(f"Accuracy: {accuracy * 100:.2f}%")
    print("\nClassification report:")
    print(classification_report(labels, predictions, zero_division=0))
    print("Confusion matrix:")
    print(confusion_matrix(labels, predictions))


if __name__ == "__main__":
    main()
