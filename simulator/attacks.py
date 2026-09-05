import random

from simulator.vehicle import VehicleSimulator


class AttackVehicle(VehicleSimulator):
    def __init__(self, vehicle_id: str):
        super().__init__(vehicle_id=vehicle_id, attack_mode=True)

    def replay_packet(self, message_id: str):
        packet = self.packet(message_id)
        packet["message_id"] = message_id
        packet["sequence"] = max(1, packet["sequence"] - 1)
        return packet


def generate_attack_schedule(total_vehicles: int, attack_rate: float = 0.10):
    attack_count = max(1, int(total_vehicles * attack_rate))
    attack_ids = set()
    while len(attack_ids) < attack_count:
        attack_ids.add(f"veh_sim_{random.randint(1, total_vehicles)}")
    return sorted(attack_ids)
