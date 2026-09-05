class DPoSValidator:
    """
    Trust-weighted Delegated Proof-of-Stake validator selection.
    """

    def __init__(self):
        self.trust_registry = {}

    def update_trust(self, vehicle_id, trust_score):
        self.trust_registry[vehicle_id] = float(trust_score)

    def select_validator(self, shard_vehicle_ids):
        if not shard_vehicle_ids:
            return None
        ranked = sorted(
            shard_vehicle_ids,
            key=lambda vid: self.trust_registry.get(vid, 0.5),
            reverse=True
        )
        return ranked[0]
