import argparse
import secrets
from pathlib import Path

from eth_account import Account


ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env.local"


def main():
    parser = argparse.ArgumentParser(description="Generate local Sepolia wallet and JWT configuration")
    parser.add_argument("--rpc-url", default="", help="Sepolia RPC URL from Alchemy or Infura")
    parser.add_argument("--contract-address", default="", help="Deployed TrustRegistry contract address")
    args = parser.parse_args()

    account = Account.create()
    contents = f"""APP_ENV=development
PORT=5000
DATABASE_URL=sqlite:///data/iov.db
MQTT_HOST=localhost
MQTT_PORT=1883
MQTT_TOPIC=iov/+/telemetry

ETH_RPC_URL={args.rpc_url}
ETH_CHAIN_ID=11155111
ETH_ACCOUNT={account.address}
ETH_PRIVATE_KEY={account.key.hex()}
ETH_CONTRACT_ADDRESS={args.contract_address}
JWT_SECRET={secrets.token_urlsafe(32)}
"""
    ENV_PATH.write_text(contents, encoding="utf-8")
    print(f"Created {ENV_PATH}")
    print(f"ETH_ACCOUNT={account.address}")
    print("ETH_PRIVATE_KEY was written only to .env.local")
    print("Add Sepolia test ETH to this address before sending transactions.")
    print("Add ETH_RPC_URL and ETH_CONTRACT_ADDRESS when available.")


if __name__ == "__main__":
    main()
