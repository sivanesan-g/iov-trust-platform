import argparse
import json
import random
import time

import requests

from simulator.attacks import generate_attack_schedule
from simulator.vehicle import VehicleSimulator


def parse_args():
    parser = argparse.ArgumentParser(description="Run the IoV simulator")
    parser.add_argument("--vehicles", type=int, default=10)
    parser.add_argument("--interval", type=float, default=0.1)
    parser.add_argument("--attack-rate", type=float, default=0.10)
    parser.add_argument("--api-url", default="http://127.0.0.1:5000/api/predict")
    return parser.parse_args()


def send_packet(api_url: str, packet: dict):
    try:
        response = requests.post(api_url, json=packet, timeout=5)
        if response.status_code >= 400:
            print(f"Rejected: {packet['vehicle_id']} -> {response.status_code} {response.text[:180]}")
        else:
            body = response.json()
            print(f"Vehicle {packet['vehicle_id']} -> {body.get('prediction', {}).get('label')} | Trust {body.get('trust', {}).get('score')} | Action {body.get('security', {}).get('action')}")
    except Exception as exc:
        print(f"Transport error for {packet['vehicle_id']}: {exc}")


def main():
    args = parse_args()
    attack_vehicles = set(generate_attack_schedule(args.vehicles, args.attack_rate))
    vehicles = []
    for index in range(1, args.vehicles + 1):
        vehicle_id = f"veh_sim_{index}"
        vehicles.append(VehicleSimulator(vehicle_id=vehicle_id, attack_mode=vehicle_id in attack_vehicles))

    for _ in range(10):
        for vehicle in vehicles:
            packet = vehicle.packet(f"msg-{vehicle.vehicle_id}-{random.randint(1000, 9999)}")
            send_packet(args.api_url, packet)
            time.sleep(args.interval)


if __name__ == "__main__":
    main()
