import random
import time
from typing import Dict

from backend.config import FEATURES


class VehicleSimulator:
    def __init__(self, vehicle_id: str, attack_mode: bool = False):
        self.vehicle_id = vehicle_id
        self.attack_mode = attack_mode
        self.sequence = 0
        self.position = {
            "posx": random.uniform(0.0, 50.0),
            "posy": random.uniform(0.0, 50.0),
            "posz": random.uniform(0.0, 5.0),
        }
        self.velocity = {
            "spdx": random.uniform(-2.0, 2.0),
            "spdy": random.uniform(-2.0, 2.0),
            "spdz": random.uniform(-1.0, 1.0),
        }
        self.acceleration = {
            "aclx": random.uniform(-0.5, 0.5),
            "acly": random.uniform(-0.5, 0.5),
            "aclz": random.uniform(-0.5, 0.5),
        }
        self.heading = {
            "hedx": random.uniform(0.0, 1.0),
            "hedy": random.uniform(0.0, 1.0),
            "hedz": random.uniform(0.0, 1.0),
        }

    def next_features(self) -> Dict[str, float]:
        self.sequence += 1
        if self.attack_mode:
            base = self._attack_features()
        else:
            base = self._normal_features()
        return {name: float(base.get(name, 0.0)) for name in FEATURES}

    def _normal_features(self):
        self.position["posx"] += self.velocity["spdx"] * 0.2 + random.uniform(-0.5, 0.5)
        self.position["posy"] += self.velocity["spdy"] * 0.2 + random.uniform(-0.5, 0.5)
        self.position["posz"] = max(0.0, min(5.0, self.position["posz"] + self.velocity["spdz"] * 0.1))
        self.velocity["spdx"] = max(-10.0, min(10.0, self.velocity["spdx"] + random.uniform(-0.4, 0.4)))
        self.velocity["spdy"] = max(-10.0, min(10.0, self.velocity["spdy"] + random.uniform(-0.4, 0.4)))
        self.velocity["spdz"] = max(-2.0, min(2.0, self.velocity["spdz"] + random.uniform(-0.2, 0.2)))
        self.acceleration["aclx"] = random.uniform(-0.4, 0.4)
        self.acceleration["acly"] = random.uniform(-0.4, 0.4)
        self.acceleration["aclz"] = random.uniform(-0.2, 0.2)
        self.heading["hedx"] = random.uniform(-1.0, 1.0)
        self.heading["hedy"] = random.uniform(-1.0, 1.0)
        self.heading["hedz"] = random.uniform(-1.0, 1.0)
        return {
            **self.position,
            **self.velocity,
            **self.acceleration,
            **self.heading,
        }

    def _attack_features(self):
        self.position["posx"] += random.uniform(30.0, 120.0)
        self.position["posy"] += random.uniform(30.0, 120.0)
        self.velocity["spdx"] = random.uniform(20.0, 60.0)
        self.velocity["spdy"] = random.uniform(20.0, 60.0)
        self.velocity["spdz"] = random.uniform(5.0, 18.0)
        self.acceleration["aclx"] = random.uniform(8.0, 20.0)
        self.acceleration["acly"] = random.uniform(8.0, 20.0)
        self.acceleration["aclz"] = random.uniform(3.0, 10.0)
        self.heading["hedx"] = random.uniform(2.0, 10.0)
        self.heading["hedy"] = random.uniform(2.0, 10.0)
        self.heading["hedz"] = random.uniform(2.0, 10.0)
        return {
            **self.position,
            **self.velocity,
            **self.acceleration,
            **self.heading,
        }

    def packet(self, message_id: str):
        return {
            "vehicle_id": self.vehicle_id,
            "message_id": message_id,
            "sequence": self.sequence,
            "timestamp": time.time(),
            "features": self.next_features(),
        }
