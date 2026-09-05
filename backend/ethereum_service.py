import json
import os
from pathlib import Path

try:
    from web3 import Web3
except Exception:
    Web3 = None


class EthereumTrustService:
    """
    Logs trust updates to a deployed TrustRegistry smart contract.
    If Ethereum is not configured, the API still runs and returns disabled status.
    """

    def __init__(self):
        self.enabled = False
        self.contract = None
        self.w3 = None
        self.disabled_reason = "not initialized"

        if Web3 is None:
            self.disabled_reason = "web3 package not installed"
            return

        rpc_url = os.getenv("ETH_RPC_URL", "http://127.0.0.1:7545")
        self.account = os.getenv("ETH_ACCOUNT")
        self.private_key = os.getenv("ETH_PRIVATE_KEY")
        self.contract_address = os.getenv("TRUST_CONTRACT_ADDRESS") or os.getenv("ETH_CONTRACT_ADDRESS")
        self.chain_id = int(os.getenv("ETH_CHAIN_ID", "1337"))

        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.w3.is_connected():
            self.disabled_reason = "Ethereum node not connected"
            return

        if not self.account:
            try:
                self.account = self.w3.eth.accounts[0]
            except Exception:
                self.disabled_reason = "no Ganache account available"
                return

        if not self.private_key:
            self.private_key = None

        abi, bytecode = self._load_contract_artifact()
        if not abi or not bytecode:
            self.disabled_reason = "contract artifact not available"
            return

        try:
            if self.contract_address:
                self.contract = self.w3.eth.contract(
                    address=Web3.to_checksum_address(self.contract_address),
                    abi=abi
                )
            else:
                self.contract_address = self._deploy_contract(abi, bytecode)
                self.contract = self.w3.eth.contract(
                    address=Web3.to_checksum_address(self.contract_address),
                    abi=abi
                )

            self.enabled = True
            self.disabled_reason = ""
        except Exception as exc:
            self.disabled_reason = f"contract_init_error: {exc}"

    def _load_contract_artifact(self):
        artifact_path = Path(__file__).resolve().parents[1] / "contracts" / "artifacts" / "TrustRegistry.json"
        try:
            with artifact_path.open("r", encoding="utf-8") as handle:
                artifact = json.load(handle)
            abi = artifact.get("abi")
            bytecode = artifact.get("data", {}).get("bytecode", {}).get("object")
            return abi, bytecode
        except Exception:
            return None, None

    def _deploy_contract(self, abi, bytecode):
        contract_factory = self.w3.eth.contract(abi=abi, bytecode=bytecode)
        nonce = self.w3.eth.get_transaction_count(self.account)

        tx = contract_factory.constructor().build_transaction({
            "from": self.account,
            "nonce": nonce,
            "chainId": self.chain_id,
            "gas": 3000000,
            "gasPrice": self.w3.to_wei("2", "gwei")
        })

        if self.private_key:
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        else:
            tx_hash = self.w3.eth.send_transaction(tx)

        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return receipt.contractAddress

    def update_trust_on_chain(
        self,
        vehicle_id: str,
        trust_score: float,
        prediction_label: str,
        confidence: float,
        shard: str,
        status: str
    ):
        if not self.enabled:
            return {
                "status": "ethereum_disabled",
                "reason": self.disabled_reason
            }

        trust_scaled = int(float(trust_score) * 1000)
        conf_scaled = int(float(confidence or 0.5) * 1000)

        try:
            nonce = self.w3.eth.get_transaction_count(self.account)

            tx = self.contract.functions.updateTrust(
                vehicle_id,
                trust_scaled,
                prediction_label,
                conf_scaled,
                shard,
                status
            ).build_transaction({
                "from": self.account,
                "nonce": nonce,
                "chainId": self.chain_id,
                "gas": 300000,
                "gasPrice": self.w3.to_wei("2", "gwei")
            })

            if self.private_key:
                signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            else:
                tx_hash = self.w3.eth.send_transaction(tx)

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            return {
                "status": "saved_ethereum",
                "tx_hash": tx_hash.hex(),
                "block_number": receipt.blockNumber
            }
        except Exception as exc:
            return {
                "status": "ethereum_error",
                "reason": str(exc)
            }
