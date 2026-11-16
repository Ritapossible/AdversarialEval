#!/usr/bin/env python3
"""Count the payer's on-chain USDC payments for a block range (rule v2, amendment 1).

    python bench/onchain_payments.py <payer> <from_block> <to_block> <out.json>

Lists every test-USDC Transfer from the payer on Ethereum Sepolia, so the cost a buyer actually
paid can be reconciled with the calls made. Public data only; no key.
"""
import json
import subprocess
import sys

RPC = "https://ethereum-sepolia-rpc.publicnode.com"
TOKEN = "0xcc194e1a843B658526D0D5C431f670028582Ae17"
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"  # public-constant: keccak("Transfer(address,address,uint256)")


def main(payer: str, start: int, end: int, out: str) -> None:
    topic = "0x" + payer.lower().removeprefix("0x").rjust(64, "0")
    logs = []
    for f in range(start, end + 1, 2000):
        q = {"jsonrpc": "2.0", "id": 1, "method": "eth_getLogs", "params": [{"address": TOKEN, "fromBlock": hex(f),
             "toBlock": hex(min(f + 1999, end)), "topics": [TRANSFER, topic]}]}
        d = json.loads(subprocess.run(["curl", "-sS", "-m", "60", "--retry", "3", RPC, "-H", "content-type: application/json",
                                       "-d", json.dumps(q)], capture_output=True, text=True, check=True).stdout)
        if "error" in d:
            sys.exit(f"rpc error: {d['error']}")
        logs += d["result"]
    rows = [{"block": int(l["blockNumber"], 16), "tx": l["transactionHash"], "log_index": int(l["logIndex"], 16),
             "to": "0x" + l["topics"][2][-40:], "amount_uusdc": int(l["data"], 16)} for l in logs]
    summary = {"payer": payer, "token": TOKEN, "chain": "eip155:11155111", "from_block": start, "to_block": end,
               "transfers": len(rows), "total_usdc": sum(r["amount_uusdc"] for r in rows) / 1e6,
               "distinct_tx": len({r["tx"] for r in rows}), "payments": rows}
    json.dump(summary, open(out, "w"), indent=1)
    print({k: v for k, v in summary.items() if k != "payments"})


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
