from collections import defaultdict
import math
from time import time


class AdaptiveGraphSharding:
    """
    Adaptive Graph Sharding manager.
    Assignment uses position, speed bucket, trust score, and shard load.
    """

    def __init__(self, shard_count=3):
        self.shard_count = shard_count
        self.shards = {f"shard_{i+1}": [] for i in range(shard_count)}
        self.vehicle_to_shard = {}
        self.shard_load = defaultdict(int)
        self.cross_shard_transfers = []

    def _zone_hash(self, posx, posy):
        zx = int(abs(posx) // 250)
        zy = int(abs(posy) // 250)
        return zx + zy

    def _speed_bucket(self, spdx, spdy, spdz):
        mag = math.sqrt(spdx**2 + spdy**2 + spdz**2)
        if mag < 5:
            return 0
        if mag < 15:
            return 1
        return 2

    def _trust_bias(self, trust_score):
        if trust_score > 0.8:
            return -0.2
        if trust_score < 0.3:
            return 0.4
        return 0.1

    def assign_shard(self, vehicle_id, features, trust_score=0.5):
        posx = float(features.get("posx", 0))
        posy = float(features.get("posy", 0))
        spdx = float(features.get("spdx", 0))
        spdy = float(features.get("spdy", 0))
        spdz = float(features.get("spdz", 0))

        zone = self._zone_hash(posx, posy)
        speed_bucket = self._speed_bucket(spdx, spdy, spdz)
        trust_bucket = int(trust_score * 10)

        preferred = (hash(vehicle_id) + zone + speed_bucket + trust_bucket) % self.shard_count
        shard_names = list(self.shards.keys())

        candidates = [
            shard_names[preferred],
            shard_names[(preferred + 1) % self.shard_count],
            shard_names[(preferred + 2) % self.shard_count]
        ]

        chosen = min(
            candidates,
            key=lambda s: self.shard_load[s] + self._trust_bias(trust_score)
        )

        old = self.vehicle_to_shard.get(vehicle_id)
        transfer = None

        if old and old != chosen:
            transfer = {
                "vehicle_id": vehicle_id,
                "from_shard": old,
                "to_shard": chosen,
                "zone": zone,
                "speed_bucket": speed_bucket,
                "trust_bucket": trust_bucket,
                "reason": "adaptive_rebalance",
                "timestamp": time()
            }
            self.cross_shard_transfers.append(transfer)

        if old and vehicle_id in self.shards[old]:
            self.shards[old].remove(vehicle_id)
            self.shard_load[old] = max(0, self.shard_load[old] - 1)

        if vehicle_id not in self.shards[chosen]:
            self.shards[chosen].append(vehicle_id)
            self.shard_load[chosen] += 1

        self.vehicle_to_shard[vehicle_id] = chosen
        return chosen, transfer

    def metrics(self):
        return {
            "shard_load": dict(self.shard_load),
            "vehicle_to_shard": dict(self.vehicle_to_shard),
            "cross_shard_transfers": self.cross_shard_transfers[-20:]
        }
