// Burner wallet helper for the paid benchmark (Ethereum Sepolia, testnet only).
//
//   node bench/wallet.mjs balance
//   node bench/wallet.mjs mint-usdc <amount>            # Telegraph's Sepolia test USDC is open-mint
//   node bench/wallet.mjs send-erc20 <token> <to> <amount> <decimals>
//   node bench/wallet.mjs escrow-deposit <amount>       # approve + LedgerFacet.depositUSDC on the Diamond
//   node bench/wallet.mjs escrow-balance                # the node's ledger view of this payer
//
// Key: $BENCH_KEY_FILE (default ~/.adversarialeval/burner.key). Never stored in the repo.
import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { createPublicClient, createWalletClient, http, parseAbi, parseUnits, formatUnits } from "viem";
import { sepolia, baseSepolia } from "viem/chains";
import { privateKeyToAccount } from "viem/accounts";

const RPC = "https://ethereum-sepolia-rpc.publicnode.com";
const TEST_USDC = "0xcc194e1a843B658526D0D5C431f670028582Ae17";
const CIRCLE_USDC = "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238"; // what the node asked for on 2026-11-17
const BASE_SEPOLIA_USDC = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"; // the node's exact-payment asset from 2026-11-20
const DIAMOND = "0x72a70e949362670Bf8bceAd24eFC5b8f950aa08b"; // Telegraph Diamond on Sepolia from 2026-11-17
const NODE = "https://devnode.telegraphprotocol.com";
const abi = parseAbi([
  "function approve(address,uint256) returns (bool)",
  "function depositUSDC(uint256)",
  "function balanceOf(address) view returns (uint256)",
  "function mint(address,uint256)",
  "function transfer(address,uint256) returns (bool)",
]);
const account = privateKeyToAccount(readFileSync(process.env.BENCH_KEY_FILE || join(homedir(), ".adversarialeval", "burner.key"), "utf8").trim());
const pub = createPublicClient({ chain: sepolia, transport: http(RPC) });
const wallet = createWalletClient({ account, chain: sepolia, transport: http(RPC) });

async function send(to, functionName, args) {
  const hash = await wallet.writeContract({ address: to, abi, functionName, args });
  const r = await pub.waitForTransactionReceipt({ hash });
  console.log(`${functionName} tx ${hash} status ${r.status}`);
}

const [cmd, ...a] = process.argv.slice(2);
if (cmd === "balance") {
  const eth = await pub.getBalance({ address: account.address });
  const usdc = await pub.readContract({ address: TEST_USDC, abi, functionName: "balanceOf", args: [account.address] });
  const circle = await pub.readContract({ address: CIRCLE_USDC, abi, functionName: "balanceOf", args: [account.address] });
  const base = createPublicClient({ chain: baseSepolia, transport: http("https://base-sepolia-rpc.publicnode.com") });
  const baseUsdc = await base.readContract({ address: BASE_SEPOLIA_USDC, abi, functionName: "balanceOf", args: [account.address] });
  console.log(`${account.address} Sepolia: ETH ${formatUnits(eth, 18)} testUSDC(old) ${formatUnits(usdc, 6)} CircleUSDC ${formatUnits(circle, 6)} | Base Sepolia: USDC ${formatUnits(baseUsdc, 6)}`);
} else if (cmd === "mint-usdc") {
  await send(TEST_USDC, "mint", [account.address, parseUnits(a[0], 6)]);
} else if (cmd === "send-erc20") {
  await send(a[0], "transfer", [a[1], parseUnits(a[2], Number(a[3]))]);
} else if (cmd === "escrow-deposit") {
  // escrow is funded in the open-mint test USDC (docs: anjoman.ai/docs/using/escrow-inference)
  const amount = parseUnits(a[0], 6);
  await send(TEST_USDC, "approve", [DIAMOND, amount]);
  await send(DIAMOND, "depositUSDC", [amount]);
} else if (cmd === "escrow-balance") {
  const r = await fetch(`${NODE}/v1/ledger/account/${account.address.toLowerCase()}`);
  const d = await r.json();
  console.log(JSON.stringify({ deposited: d.deposited, charged: d.charged, unbilled: d.unbilled, balance: d.balance, available: d.available }));
} else {
  console.log("usage: balance | mint-usdc <amount> | send-erc20 <token> <to> <amount> <decimals>");
}
