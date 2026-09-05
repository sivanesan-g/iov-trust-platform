import hashlib
import json
import os
from pathlib import Path
from time import time


class ShardedBlockchainLedger:
    def __init__(self, shard_names, state_path=None):
        base_dir = Path(__file__).resolve().parents[1]
        self.state_path = Path(state_path or os.getenv("LEDGER_STATE_PATH", base_dir / "data" / "ledger_state.json"))
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.ledgers = {name: [] for name in shard_names}
        self._load_or_initialize()

    def _hash(self, block):
        return hashlib.sha256(json.dumps(block, sort_keys=True).encode()).hexdigest()

    def _create_genesis(self, shard_name):
        genesis = {
            "index": 1,
            "timestamp": time(),
            "previous_hash": "0",
            "validator": "genesis",
            "data": {"message": f"Genesis block for {shard_name}"}
        }
        genesis["hash"] = self._hash(genesis)
        self.ledgers[shard_name].append(genesis)

    def _load_or_initialize(self):
        if self.state_path.exists():
            try:
                with self.state_path.open("r", encoding="utf-8") as handle:
                    saved = json.load(handle)

                if isinstance(saved, dict):
                    for shard_name in self.ledgers:
                        self.ledgers[shard_name] = saved.get(shard_name, [])

                    for shard_name in self.ledgers:
                        if not self.ledgers[shard_name]:
                            self._create_genesis(shard_name)

                    self._persist_state()
                    return
            except Exception:
                pass

        for shard_name in self.ledgers:
            if not self.ledgers[shard_name]:
                self._create_genesis(shard_name)

        self._persist_state()

    def _persist_state(self):
        with self.state_path.open("w", encoding="utf-8") as handle:
            json.dump(self.ledgers, handle, indent=2)

    def add_block(self, shard_name, validator, data):
        chain = self.ledgers[shard_name]
        prev = chain[-1]
        block = {
            "index": len(chain) + 1,
            "timestamp": time(),
            "previous_hash": prev["hash"],
            "validator": validator,
            "data": data
        }
        block["hash"] = self._hash(block)
        chain.append(block)
        self._persist_state()
        return block

    def export(self):
        return self.ledgers
