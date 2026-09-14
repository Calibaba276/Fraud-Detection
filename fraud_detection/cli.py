from __future__ import annotations

import argparse
import json
from pathlib import Path

from .generator import write_dataset
from .ingestion import load_transactions
from .model import train_model


def generate() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/transactions.csv")
    parser.add_argument("--rows", type=int, default=20_000)
    args = parser.parse_args()
    print(write_dataset(args.output, args.rows))


def train() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--output", default="artifacts/model.joblib")
    args = parser.parse_args()
    result = train_model(load_transactions(args.input), args.output)
    print(json.dumps(result, indent=2))


def evaluate() -> None:
    train()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["generate", "train", "evaluate"])
    args, remaining = parser.parse_known_args()
    import sys
    sys.argv = [sys.argv[0], *remaining]
    {"generate": generate, "train": train, "evaluate": evaluate}[args.command]()
